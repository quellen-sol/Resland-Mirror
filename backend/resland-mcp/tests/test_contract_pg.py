"""The MCP tools against the API's real routes and a live Postgres
(TEST_PG_URL): the JSON the tools send must be what the API's request models
accept, and what the API returns must be what the tools expect. Auth is
overridden to one user; exports (S3) aren't covered here.

Run: TEST_PG_URL=... uv run pytest tests/test_contract_pg.py -v
"""

import os
import tempfile
import unittest
from pathlib import Path

import httpx2
import psycopg
from api.auth import require_auth0_id
from api.deps import get_pg_conn
from api.memory.router import router as memory_router
from api.profile.router import router as profile_router
from api.tailored.router import router as tailored_router
from fastapi import FastAPI
from mcp import Client
from resland_mcp.api import ReslandApi
from resland_mcp.server import create_server
from shared.testing import destructive_db_ok

from .helpers import settings

TEST_PG_URL = os.getenv(
    "TEST_PG_URL", "postgres://resland:resland@localhost:5432/resland_test"
)
USER = "auth0|contract"


def _pg_ready() -> str | None:
    ok, reason = destructive_db_ok(TEST_PG_URL)
    if not ok:
        return reason
    try:
        psycopg.connect(TEST_PG_URL, connect_timeout=3).close()
    except Exception:
        return f"needs Postgres at TEST_PG_URL ({TEST_PG_URL})"
    return None


SKIP_REASON = _pg_ready()


class StaticTokens:
    async def token(self):
        return "tok"


def _app() -> FastAPI:
    app = FastAPI()
    for router in (profile_router, memory_router, tailored_router):
        app.include_router(router)

    async def pg_conn():
        conn = await psycopg.AsyncConnection.connect(TEST_PG_URL, autocommit=True)
        try:
            yield conn
        finally:
            await conn.close()

    app.dependency_overrides[require_auth0_id] = lambda: USER
    app.dependency_overrides[get_pg_conn] = pg_conn
    return app


def _seed(conn) -> dict:
    conn.execute('TRUNCATE "user" CASCADE')
    conn.execute(
        """INSERT INTO "user" (auth0_id, full_name, email) VALUES (%s, 'Jane Doe', 'jane@example.com')""",
        (USER,),
    )
    ids = {}
    for name, title, start, created, bullets in (
        ("Initech", "Engineer", "2019", "2024-01-01", ["Ran the payments ledger"]),
        (
            "Acme",
            "Senior Engineer",
            "2022",
            "2025-01-01",
            ["Led the data team", "Built ingestion"],
        ),
    ):
        exp_id = conn.execute(
            """
            INSERT INTO user_base_experience (user_id, company_name, title, start_date, created_at)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
            """,
            (USER, name, title, start, created),
        ).fetchone()[0]
        ids[name] = exp_id
        if name == "Acme":
            conn.execute(
                "UPDATE user_base_experience SET location = 'Remote' WHERE id = %s",
                (exp_id,),
            )
        for order, text in enumerate(bullets):
            conn.execute(
                """
                INSERT INTO user_base_experience_bullet (user_experience_id, bullet, bullet_order)
                VALUES (%s, %s, %s)
                """,
                (exp_id, text, order),
            )
    for order, (skill, category) in enumerate(
        [("Python", "Languages"), ("Kafka", "Data")]
    ):
        conn.execute(
            "INSERT INTO user_base_skill (user_id, name, category, sort_order) VALUES (%s, %s, %s, %s)",
            (USER, skill, category, order),
        )
    return ids


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class Contract(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        with psycopg.connect(TEST_PG_URL, autocommit=True) as conn:
            self.ids = _seed(conn)
        http = httpx2.AsyncClient(transport=httpx2.ASGITransport(app=_app()))
        api = ReslandApi("http://api.test", StaticTokens(), http)
        self.server = create_server(api, settings(Path(tempfile.mkdtemp())))

    async def call(self, client, name, args=None):
        result = await client.call_tool(name, args or {})
        self.assertFalse(result.is_error, result.content)
        return result.structured_content

    async def test_tailor_flow_round_trips(self):
        async with Client(self.server) as client:
            profile = await self.call(client, "get_profile")
            self.assertEqual(
                [e["company_name"] for e in profile["experiences"]], ["Acme", "Initech"]
            )

            saved = await self.call(
                client,
                "remember_facts",
                {
                    "facts": [
                        {"topic": "Senior Engineer at Acme", "content": "Team of 6"}
                    ]
                },
            )
            fact_id = saved["saved"][0]["id"]
            memory = await self.call(client, "list_memory")
            self.assertEqual(
                [(f["id"], f["source"]) for f in memory["facts"]], [(fact_id, "TAILOR")]
            )

            created = await self.call(
                client,
                "save_tailored_resume",
                {
                    "job_description": "Data platform lead",
                    "company_name": "Globex",
                    "role": "Staff Engineer",
                    "experiences": [
                        {
                            "experience_id": e["id"],
                            "bullets": [b["text"] for b in e["bullets"]][::-1],
                        }
                        for e in profile["experiences"]
                    ],
                    "skills": ["Kafka", "Python"],
                },
            )
            self.assertTrue(created["url"].endswith(f"/tailored/{created['id']}"))

            got = await self.call(
                client, "get_tailored_resume", {"tailored_id": created["id"]}
            )
            content = got["content"]
            self.assertEqual(
                content["experiences"][0]["bullets"],
                ["Built ingestion", "Led the data team"],
            )
            self.assertEqual(
                [g["category"] for g in content["skill_groups"]], ["Data", "Languages"]
            )

            # The content get returns is the shape update accepts.
            content["summary"] = "Data platform engineer."
            updated = await self.call(
                client,
                "update_tailored_resume",
                {"tailored_id": created["id"], "content": content, "role": "Principal"},
            )
            self.assertEqual(updated["role"], "Principal")
            self.assertEqual(updated["content"]["summary"], "Data platform engineer.")
            # A full-content update keeps each experience's location.
            self.assertEqual(
                [e["location"] for e in updated["content"]["experiences"]],
                ["Remote", None],
            )

            listed = await self.call(client, "list_tailored_resumes")
            self.assertEqual([i["id"] for i in listed["items"]], [created["id"]])

    async def test_bad_experience_id_comes_back_as_a_tool_error(self):
        async with Client(self.server) as client:
            result = await client.call_tool(
                "save_tailored_resume",
                {
                    "job_description": "JD",
                    "experiences": [{"experience_id": 999999, "bullets": ["x"]}],
                    "skills": [],
                },
            )
        self.assertTrue(result.is_error)
        self.assertIn("Unknown experience ids [999999]", result.content[0].text)

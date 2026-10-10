"""Wire shapes for the routes the personal MCP server calls: GET /profile,
GET/POST /memory, and POST /tailored.

Run: .venv/bin/python -m pytest backend/api/tests/test_profile_memory_routes.py -v
"""

import unittest
from unittest.mock import AsyncMock, patch

from api import api as api_app
from api.auth import require_auth0_id
from api.deps import get_pg_conn
from api.memory import model as memory_model
from api.memory import router as memory_router
from api.memory import service as memory_service
from api.profile import model as profile_model
from api.profile import router as profile_router
from api.profile import service as profile_service
from api.tailored import model as tailored_model
from api.tailored import router as tailored_router
from api.tailored import service as tailored_service
from fastapi import FastAPI
from fastapi.testclient import TestClient

EMPTY_PROFILE = profile_model.ProfileResponse(
    social_links=[], experiences=[], skills=[], education=[], projects=[]
)


class Routes(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(profile_router.router)
        app.include_router(memory_router.router)
        app.include_router(tailored_router.router)
        app.dependency_overrides[require_auth0_id] = lambda: "auth0|u1"
        app.dependency_overrides[get_pg_conn] = lambda: None
        self.client = TestClient(app)

    def test_get_profile(self):
        with patch.object(
            profile_service, "get_profile", new=AsyncMock(return_value=EMPTY_PROFILE)
        ) as get:
            resp = self.client.get("/profile")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["experiences"], [])
        self.assertEqual(get.call_args.kwargs["user_id"], "auth0|u1")

    def test_list_memory(self):
        with patch.object(
            memory_service,
            "list_memory",
            new=AsyncMock(return_value=memory_model.MemoryListResponse(facts=[])),
        ):
            resp = self.client.get("/memory")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"facts": []})

    def test_remember_passes_the_parsed_request(self):
        saved = memory_model.RememberResponse(
            saved=[memory_model.MemoryFact(id=1, topic="General", content="Likes Go")]
        )
        with patch.object(
            memory_service, "remember", new=AsyncMock(return_value=saved)
        ) as remember:
            resp = self.client.post(
                "/memory",
                json={"facts": [{"topic": " General", "content": "Likes Go"}]},
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["saved"][0]["id"], 1)
        self.assertEqual(remember.call_args.kwargs["req"].facts[0].topic, "General")

    def test_remember_rejects_an_empty_batch(self):
        resp = self.client.post("/memory", json={"facts": []})
        self.assertEqual(resp.status_code, 422)

    def test_create_tailored(self):
        with patch.object(
            tailored_service,
            "create_tailored",
            new=AsyncMock(return_value=tailored_model.CreateTailoredResponse(id="t9")),
        ) as create:
            resp = self.client.post(
                "/tailored",
                json={
                    "job_description": "JD",
                    "experiences": [{"experience_id": 1, "bullets": ["Built x"]}],
                },
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"id": "t9"})
        self.assertEqual(create.call_args.kwargs["req"].experiences[0].experience_id, 1)

    def test_create_tailored_needs_a_job_description(self):
        resp = self.client.post(
            "/tailored", json={"experiences": [{"experience_id": 1, "bullets": []}]}
        )
        self.assertEqual(resp.status_code, 422)


class AppWiring(unittest.TestCase):
    def test_routes_are_mounted(self):
        # Included routers are wrapped, so read the mounted paths off the
        # OpenAPI schema rather than app.routes.
        paths = api_app.app.openapi()["paths"]
        self.assertIn("get", paths["/profile"])
        self.assertEqual({"get", "post"}, set(paths["/memory"]))
        self.assertIn("post", paths["/tailored"])

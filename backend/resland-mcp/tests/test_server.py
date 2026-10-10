"""The MCP tools and prompt, driven through an in-process MCP client against a
fake Resland API.

Run: uv run pytest tests/test_server.py -v   (from backend/resland-mcp)
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

import httpx2
from mcp import Client
from mcp.server.mcpserver.exceptions import ToolError
from resland_mcp.api import ReslandApi
from resland_mcp.prompts import INSTRUCTIONS, TAILORING_GUIDE
from resland_mcp.server import create_server, libreoffice_to_pdf
from shared.memory import MEMORY_RULES
from shared.writing import BULLET_WRITING_RULES

from .helpers import FakeHttp, body, settings

API = "https://api.test"
PRESIGNED = "https://bucket.s3.test/resumes/u1/tailored/t1.docx"

TAILORED = {
    "id": "t1",
    "company_name": "Acme Corp",
    "role": "Senior Engineer",
    "job_description": "JD",
    "content": {"summary": None, "experiences": [], "skill_groups": []},
    "created_at": "2026-10-01T00:00:00+00:00",
    "updated_at": "2026-10-01T00:00:00+00:00",
    "generated_at": None,
}


class StaticTokens:
    async def token(self):
        return "tok"


def ok(payload):
    return lambda request: httpx2.Response(200, json=payload)


class ServerTest(unittest.IsolatedAsyncioTestCase):
    # Routes every test in the class starts with (copied per test).
    routes: ClassVar[dict] = {}

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.settings = settings(self.tmp)
        self.fake = FakeHttp(dict(self.routes))
        self.pdf_calls: list[Path] = []
        api = ReslandApi(API, StaticTokens(), self.fake.client())
        self.server = create_server(api, self.settings, to_pdf=self._to_pdf)

    async def _to_pdf(self, docx: Path) -> Path:
        self.pdf_calls.append(docx)
        pdf = docx.with_suffix(".pdf")
        pdf.write_bytes(b"%PDF")
        return pdf

    async def call(self, name, args=None):
        async with Client(self.server) as client:
            return await client.call_tool(name, args or {})


class Tools(ServerTest):
    async def test_lists_the_tools_and_the_prompt(self):
        async with Client(self.server) as client:
            tools = {t.name for t in (await client.list_tools()).tools}
            prompts = {p.name for p in (await client.list_prompts()).prompts}
        self.assertEqual(
            tools,
            {
                "get_tailoring_guide",
                "get_profile",
                "list_memory",
                "remember_facts",
                "list_tailored_resumes",
                "get_tailored_resume",
                "save_tailored_resume",
                "update_tailored_resume",
                "export_tailored_resume",
            },
        )
        self.assertEqual(prompts, {"tailor"})

    async def test_get_profile_passes_the_api_json_through(self):
        self.fake.routes[("GET", f"{API}/profile")] = ok({"full_name": "Jane"})
        result = await self.call("get_profile")
        self.assertFalse(result.is_error)
        self.assertEqual(result.structured_content, {"full_name": "Jane"})

    async def test_remember_facts(self):
        self.fake.routes[("POST", f"{API}/memory")] = ok({"saved": [], "full": 0})
        await self.call(
            "remember_facts",
            {"facts": [{"topic": "General", "content": "Likes Go", "replaces_id": 3}]},
        )
        self.assertEqual(
            body(self.fake.requests[0]),
            {"facts": [{"topic": "General", "content": "Likes Go", "replaces_id": 3}]},
        )

    async def test_save_tailored_resume_returns_a_board_link(self):
        self.fake.routes[("POST", f"{API}/tailored")] = ok({"id": "t9"})
        result = await self.call(
            "save_tailored_resume",
            {
                "job_description": "JD",
                "company_name": "Acme",
                "experiences": [{"experience_id": 2, "bullets": ["Led x"]}],
                "skills": ["Go"],
            },
        )
        self.assertEqual(
            result.structured_content,
            {"id": "t9", "url": "https://app.test/tailored/t9"},
        )
        self.assertEqual(
            body(self.fake.requests[0]),
            {
                "job_description": "JD",
                "company_name": "Acme",
                "role": None,
                "summary": None,
                "experiences": [{"experience_id": 2, "bullets": ["Led x"]}],
                "skills": ["Go"],
            },
        )

    async def test_list_and_get_add_links(self):
        self.fake.routes[("GET", f"{API}/tailored")] = ok({"items": [{"id": "t1"}]})
        self.fake.routes[("GET", f"{API}/tailored/t1")] = ok(TAILORED)
        listed = await self.call("list_tailored_resumes")
        self.assertEqual(
            listed.structured_content["items"][0]["url"], "https://app.test/tailored/t1"
        )
        got = await self.call("get_tailored_resume", {"tailored_id": "t1"})
        self.assertEqual(got.structured_content["url"], "https://app.test/tailored/t1")
        self.assertEqual(got.structured_content["company_name"], "Acme Corp")

    async def test_update_sends_only_the_fields_given(self):
        self.fake.routes[("PATCH", f"{API}/tailored/t1")] = ok(TAILORED)
        await self.call(
            "update_tailored_resume", {"tailored_id": "t1", "role": "Staff Engineer"}
        )
        self.assertEqual(body(self.fake.requests[0]), {"role": "Staff Engineer"})

        content = {
            "summary": None,
            "experiences": [
                {
                    "company_name": "Acme",
                    "title": "Engineer",
                    "start_date": "2020",
                    "end_date": None,
                    "bullets": ["Built x"],
                }
            ],
            "skill_groups": [{"category": None, "skills": ["Go"]}],
        }
        await self.call(
            "update_tailored_resume", {"tailored_id": "t1", "content": content}
        )
        self.assertEqual(body(self.fake.requests[1]), {"content": content})

    async def test_update_with_nothing_to_change_is_refused(self):
        result = await self.call("update_tailored_resume", {"tailored_id": "t1"})
        self.assertTrue(result.is_error)
        self.assertEqual(self.fake.requests, [])

    async def test_api_errors_come_back_as_tool_errors(self):
        self.fake.routes[("GET", f"{API}/tailored/nope")] = lambda r: httpx2.Response(
            404, json={"detail": "Tailored resume not found"}
        )
        result = await self.call("get_tailored_resume", {"tailored_id": "nope"})
        self.assertTrue(result.is_error)
        self.assertIn("Tailored resume not found", result.content[0].text)


class Export(ServerTest):
    routes: ClassVar[dict] = {
        ("POST", f"{API}/tailored/t1/export"): ok(
            {"url": PRESIGNED + "?sig=1", "generated_at": "x", "regenerated": True}
        ),
        ("GET", f"{API}/tailored/t1"): ok(TAILORED),
        ("GET", PRESIGNED): lambda r: httpx2.Response(200, content=b"PK docx"),
    }

    async def test_docx_lands_in_the_export_dir(self):
        result = await self.call("export_tailored_resume", {"tailored_id": "t1"})
        self.assertFalse(result.is_error, result.content)
        path = Path(result.structured_content["path"])
        self.assertEqual(path.parent, self.settings.export_dir)
        self.assertEqual(path.name, "acme-corp-senior-engineer-t1.docx")
        self.assertEqual(path.read_bytes(), b"PK docx")
        self.assertEqual(self.pdf_calls, [])

    async def test_pdf_is_converted_from_the_docx(self):
        out = self.tmp / "elsewhere"
        result = await self.call(
            "export_tailored_resume",
            {"tailored_id": "t1", "format": "pdf", "directory": str(out)},
        )
        path = Path(result.structured_content["path"])
        self.assertEqual(path, out / "acme-corp-senior-engineer-t1.pdf")
        self.assertEqual(path.read_bytes(), b"%PDF")
        self.assertEqual(self.pdf_calls, [out / "acme-corp-senior-engineer-t1.docx"])


class LibreOffice(unittest.IsolatedAsyncioTestCase):
    async def test_missing_soffice_says_what_to_install(self):
        with (
            patch("resland_mcp.server.shutil.which", return_value=None),
            self.assertRaises(ToolError) as ctx,
        ):
            await libreoffice_to_pdf(Path("/tmp/resume.docx"))
        self.assertIn("LibreOffice", str(ctx.exception))
        self.assertIn("/tmp/resume.docx", str(ctx.exception))

    @unittest.skipUnless(
        shutil.which("soffice") or shutil.which("libreoffice"), "needs LibreOffice"
    )
    async def test_converts_a_real_docx(self):
        from docx import Document

        tmp = Path(tempfile.mkdtemp())
        doc = Document()
        doc.add_paragraph("Jane Doe")
        doc.save(tmp / "resume.docx")
        pdf = await libreoffice_to_pdf(tmp / "resume.docx")
        self.assertEqual(pdf, tmp / "resume.pdf")
        self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))


class Guide(ServerTest):
    async def test_guide_tool_returns_the_site_rules(self):
        # Clients that don't surface MCP prompts (Claude Desktop) still get
        # the rules: every client supports tools.
        result = await self.call("get_tailoring_guide")
        self.assertFalse(result.is_error)
        text = result.content[0].text
        self.assertEqual(text, TAILORING_GUIDE)
        self.assertIn(BULLET_WRITING_RULES, text)
        self.assertIn(MEMORY_RULES, text)
        self.assertIn("save_tailored_resume", text)
        self.assertEqual(self.fake.requests, [])
        # Models mirror the punctuation they're shown (see shared.writing).
        self.assertNotIn("\u2014", text)

    def test_server_instructions_point_at_the_guide(self):
        self.assertIn("get_tailoring_guide", INSTRUCTIONS)
        # Claude Code truncates server instructions at 2,048 characters.
        self.assertLess(len(INSTRUCTIONS), 2048)


class Prompt(ServerTest):
    async def test_tailor_prompt_carries_the_posting_and_the_site_rules(self):
        async with Client(self.server) as client:
            result = await client.get_prompt(
                "tailor",
                {"job_description": "Build payment rails", "company_name": "Globex"},
            )
        text = result.messages[0].content.text
        self.assertIn("<job_posting>\nBuild payment rails\n</job_posting>", text)
        self.assertIn("Target company: Globex", text)
        self.assertIn("Target role: (not given)", text)
        # The prompt wraps the same guide the tool returns.
        self.assertIn(TAILORING_GUIDE, text)
        # Models mirror the punctuation they're shown (see shared.writing).
        self.assertNotIn("—", text)

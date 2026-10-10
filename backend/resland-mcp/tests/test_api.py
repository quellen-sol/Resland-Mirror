"""The Resland API client: bearer auth, error wording, and presigned downloads.

Run: uv run pytest tests/test_api.py -v   (from backend/resland-mcp)
"""

import unittest

import httpx2
from resland_mcp.api import ApiError, ReslandApi, ReslandUnreachable
from resland_mcp.auth import NotLoggedIn

from .helpers import FakeHttp, body


class StaticTokens:
    def __init__(self, token="tok"):
        self._token = token

    async def token(self):
        return self._token


def api(fake: FakeHttp) -> ReslandApi:
    return ReslandApi("https://api.test", StaticTokens(), fake.client())


class Requests(unittest.IsolatedAsyncioTestCase):
    async def test_sends_the_bearer_token(self):
        fake = FakeHttp(
            {
                ("GET", "https://api.test/profile"): lambda r: httpx2.Response(
                    200, json={"ok": 1}
                )
            }
        )
        self.assertEqual(await api(fake).get_profile(), {"ok": 1})
        self.assertEqual(fake.requests[0].headers["authorization"], "Bearer tok")

    async def test_routes_and_bodies(self):
        def echo(request):
            return httpx2.Response(200, json={"path": request.url.path})

        fake = FakeHttp(
            {
                ("GET", "https://api.test/memory"): echo,
                ("POST", "https://api.test/memory"): echo,
                ("GET", "https://api.test/tailored"): echo,
                ("POST", "https://api.test/tailored"): echo,
                ("GET", "https://api.test/tailored/t1"): echo,
                ("PATCH", "https://api.test/tailored/t1"): echo,
                ("POST", "https://api.test/tailored/t1/export"): echo,
            }
        )
        client = api(fake)
        await client.list_memory()
        await client.remember([{"topic": "General", "content": "x"}])
        await client.list_tailored()
        await client.create_tailored({"job_description": "JD"})
        await client.get_tailored("t1")
        await client.update_tailored("t1", {"role": "Staff"})
        await client.export_tailored("t1")
        self.assertEqual(
            body(fake.sent("POST", "https://api.test/memory")[0]),
            {"facts": [{"topic": "General", "content": "x"}]},
        )
        self.assertEqual(
            body(fake.sent("PATCH", "https://api.test/tailored/t1")[0]),
            {"role": "Staff"},
        )

    async def test_ids_are_path_escaped(self):
        fake = FakeHttp({})
        with self.assertRaises(ApiError):
            await api(fake).get_tailored("../account")
        self.assertEqual(fake.requests[0].url.raw_path, b"/tailored/..%2Faccount")


class Errors(unittest.IsolatedAsyncioTestCase):
    async def test_401_means_log_in_again(self):
        fake = FakeHttp(
            {
                ("GET", "https://api.test/profile"): lambda r: httpx2.Response(
                    401, json={"detail": "Invalid access token"}
                )
            }
        )
        with self.assertRaises(NotLoggedIn) as ctx:
            await api(fake).get_profile()
        self.assertIn("resland-mcp login", str(ctx.exception))

    async def test_detail_string_is_passed_through(self):
        fake = FakeHttp(
            {
                ("GET", "https://api.test/tailored/t1"): lambda r: httpx2.Response(
                    404, json={"detail": "Tailored resume not found"}
                )
            }
        )
        with self.assertRaises(ApiError) as ctx:
            await api(fake).get_tailored("t1")
        self.assertEqual(ctx.exception.status, 404)
        self.assertIn("Tailored resume not found", str(ctx.exception))

    async def test_validation_errors_name_the_field(self):
        detail = [
            {
                "loc": ["body", "experiences", 0, "bullets", 1],
                "msg": "String should have at most 2000 characters",
                "type": "string_too_long",
            }
        ]
        fake = FakeHttp(
            {
                ("POST", "https://api.test/tailored"): lambda r: httpx2.Response(
                    422, json={"detail": detail}
                )
            }
        )
        with self.assertRaises(ApiError) as ctx:
            await api(fake).create_tailored({})
        self.assertIn(
            "experiences.0.bullets.1: String should have at most 2000",
            str(ctx.exception),
        )

    async def test_non_json_error(self):
        fake = FakeHttp(
            {
                ("GET", "https://api.test/profile"): lambda r: httpx2.Response(
                    502, text="Bad gateway"
                )
            }
        )
        with self.assertRaises(ApiError) as ctx:
            await api(fake).get_profile()
        self.assertIn("Bad gateway", str(ctx.exception))

    async def test_unreachable_api(self):
        def refuse(request):
            raise httpx2.ConnectError("refused", request=request)

        fake = FakeHttp({("GET", "https://api.test/profile"): refuse})
        with self.assertRaises(ReslandUnreachable) as ctx:
            await api(fake).get_profile()
        self.assertIn("https://api.test", str(ctx.exception))


class Download(unittest.IsolatedAsyncioTestCase):
    async def test_presigned_download_carries_no_bearer_token(self):
        url = "https://bucket.s3.test/resumes/u1/tailored/t1.docx"
        fake = FakeHttp(
            {("GET", url): lambda r: httpx2.Response(200, content=b"PK docx")}
        )
        self.assertEqual(
            await api(fake).download(url + "?X-Amz-Signature=abc"), b"PK docx"
        )
        self.assertNotIn("authorization", fake.requests[0].headers)

    async def test_failed_download(self):
        url = "https://bucket.s3.test/x.docx"
        fake = FakeHttp({("GET", url): lambda r: httpx2.Response(403, text="expired")})
        with self.assertRaises(ApiError):
            await api(fake).download(url)

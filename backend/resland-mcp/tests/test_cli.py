"""The resland-mcp command: config errors, login, status, logout.

Run: uv run pytest tests/test_cli.py -v   (from backend/resland-mcp)
"""

import contextlib
import io
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx2
import resland_mcp
from resland_mcp.auth import Credentials, TokenStore

from .helpers import FakeHttp, settings

TOKEN_URL = "https://tenant.auth0.test/oauth/token"
DEVICE_URL = "https://tenant.auth0.test/oauth/device/code"


async def no_sleep(_seconds):
    pass


class Main(unittest.TestCase):
    def test_missing_auth0_settings_exit_2(self):
        err = io.StringIO()
        with patch.dict("os.environ", {}, clear=True), contextlib.redirect_stderr(err):
            self.assertEqual(resland_mcp.main(["status"]), 2)
        self.assertIn("RESLAND_AUTH0_DOMAIN", err.getvalue())

    def test_logout(self):
        tmp = Path(tempfile.mkdtemp())
        env = {
            "RESLAND_AUTH0_DOMAIN": "tenant.auth0.test",
            "RESLAND_AUTH0_CLIENT_ID": "cli-123",
            "RESLAND_AUTH0_AUDIENCE": "aud",
            "RESLAND_CREDENTIALS_PATH": str(tmp / "credentials.json"),
        }
        TokenStore(tmp / "credentials.json").save(Credentials("at", 1.0))
        out = io.StringIO()
        with patch.dict("os.environ", env, clear=True), contextlib.redirect_stdout(out):
            self.assertEqual(resland_mcp.main(["logout"]), 0)
            self.assertEqual(resland_mcp.main(["logout"]), 0)
        self.assertEqual(
            out.getvalue().splitlines(), ["Signed out.", "You weren't signed in."]
        )
        self.assertFalse((tmp / "credentials.json").exists())


class Commands(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.settings = settings(self.tmp)
        self.store = TokenStore(self.settings.credentials_path)

    async def test_login_prints_the_code_and_saves_the_tokens(self):
        fake = FakeHttp(
            {
                ("POST", DEVICE_URL): lambda r: httpx2.Response(
                    200,
                    json={
                        "device_code": "dev-1",
                        "user_code": "ABCD-EFGH",
                        "verification_uri": "https://tenant.auth0.test/activate",
                        "interval": 1,
                        "expires_in": 600,
                    },
                ),
                ("POST", TOKEN_URL): [
                    httpx2.Response(
                        200,
                        json={
                            "access_token": "at",
                            "refresh_token": "rt",
                            "expires_in": 600,
                        },
                    )
                ],
            }
        )
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = await resland_mcp.login(
                self.settings, self.store, fake.client(), sleep=no_sleep
            )
        self.assertEqual(code, 0)
        self.assertIn("ABCD-EFGH", out.getvalue())
        self.assertIn("https://tenant.auth0.test/activate", out.getvalue())
        self.assertEqual(self.store.load().refresh_token, "rt")

    async def test_failed_login_saves_nothing(self):
        fake = FakeHttp(
            {
                ("POST", DEVICE_URL): lambda r: httpx2.Response(
                    401, json={"error": "unauthorized_client"}
                )
            }
        )
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = await resland_mcp.login(self.settings, self.store, fake.client())
        self.assertEqual(code, 1)
        self.assertIn("unauthorized_client", err.getvalue())
        self.assertIsNone(self.store.load())

    async def test_status_names_the_account(self):
        self.store.save(Credentials("at", time.time() + 3600))
        fake = FakeHttp(
            {
                ("GET", "https://api.test/profile"): lambda r: httpx2.Response(
                    200, json={"full_name": "Jane Doe"}
                )
            }
        )
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(
                await resland_mcp.status(self.settings, self.store, fake.client()), 0
            )
        self.assertIn("Signed in as Jane Doe", out.getvalue())

    async def test_status_without_login(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(
                await resland_mcp.status(
                    self.settings, self.store, FakeHttp({}).client()
                ),
                1,
            )
        self.assertIn("resland-mcp login", err.getvalue())

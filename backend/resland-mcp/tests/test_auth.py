"""Device-flow login, the credentials file, and token refresh.

Run: uv run pytest tests/test_auth.py -v   (from backend/resland-mcp)
"""

import stat
import tempfile
import unittest
from pathlib import Path

import httpx2
from resland_mcp.auth import (
    DEVICE_GRANT,
    Auth0,
    AuthError,
    Credentials,
    NotLoggedIn,
    TokenProvider,
    TokenStore,
)

from .helpers import FakeHttp, form, settings

DEVICE_URL = "https://tenant.auth0.test/oauth/device/code"
TOKEN_URL = "https://tenant.auth0.test/oauth/token"

DEVICE_CODE = {
    "device_code": "dev-1",
    "user_code": "ABCD-EFGH",
    "verification_uri": "https://tenant.auth0.test/activate",
    "verification_uri_complete": "https://tenant.auth0.test/activate?user_code=ABCD-EFGH",
    "interval": 5,
    "expires_in": 900,
}


def pending(error="authorization_pending"):
    return httpx2.Response(403, json={"error": error, "error_description": error})


def tokens(access="at-1", refresh="rt-1", expires_in=86400):
    payload = {"access_token": access, "expires_in": expires_in, "token_type": "Bearer"}
    if refresh:
        payload["refresh_token"] = refresh
    return httpx2.Response(200, json=payload)


class Clock:
    def __init__(self, now=1_000.0):
        self.now = now

    def __call__(self):
        return self.now


class Sleeps:
    def __init__(self, clock: Clock):
        self.clock = clock
        self.calls: list[float] = []

    async def __call__(self, seconds):
        self.calls.append(seconds)
        self.clock.now += seconds


class Store(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.store = TokenStore(self.tmp / "nested" / "credentials.json")

    def test_round_trip_owner_only(self):
        self.assertIsNone(self.store.load())
        creds = Credentials(access_token="at", expires_at=123.0, refresh_token="rt")
        self.store.save(creds)
        self.assertEqual(self.store.load(), creds)
        mode = stat.S_IMODE(self.store.path.stat().st_mode)
        self.assertEqual(mode, 0o600)

    def test_clear(self):
        self.assertFalse(self.store.clear())
        self.store.save(Credentials(access_token="at", expires_at=1.0))
        self.assertTrue(self.store.clear())
        self.assertIsNone(self.store.load())

    def test_unreadable_file_is_no_login(self):
        self.store.path.parent.mkdir(parents=True)
        self.store.path.write_text("{not json")
        self.assertIsNone(self.store.load())


class DeviceLogin(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.clock = Clock()
        self.sleeps = Sleeps(self.clock)

    def _auth0(self, fake: FakeHttp) -> Auth0:
        return Auth0(
            settings(self.tmp), fake.client(), clock=self.clock, sleep=self.sleeps
        )

    async def test_start_asks_for_a_refresh_token_for_the_api(self):
        fake = FakeHttp(
            {("POST", DEVICE_URL): lambda r: httpx2.Response(200, json=DEVICE_CODE)}
        )
        code = await self._auth0(fake).start_device_login()
        self.assertEqual(code.user_code, "ABCD-EFGH")
        self.assertEqual(code.interval, 5)
        sent = form(fake.requests[0])
        self.assertEqual(sent["client_id"], "cli-123")
        self.assertEqual(sent["audience"], "https://api.test/")
        self.assertIn("offline_access", sent["scope"].split())

    async def test_polls_until_approved_backing_off_on_slow_down(self):
        fake = FakeHttp(
            {
                ("POST", TOKEN_URL): [
                    pending(),
                    pending("slow_down"),
                    tokens(expires_in=3600),
                ]
            }
        )
        code = await self._start(fake)
        creds = await self._auth0(fake).finish_device_login(code)
        self.assertEqual(creds.access_token, "at-1")
        self.assertEqual(creds.refresh_token, "rt-1")
        # Default interval, then +5s after slow_down (RFC 8628).
        self.assertEqual(self.sleeps.calls, [5, 5, 10])
        self.assertEqual(creds.expires_at, self.clock.now + 3600)
        sent = form(fake.sent("POST", TOKEN_URL)[0])
        self.assertEqual(sent["grant_type"], DEVICE_GRANT)
        self.assertEqual(sent["device_code"], "dev-1")

    async def test_denied_or_expired_code_fails_with_a_reason(self):
        for error in ("access_denied", "expired_token"):
            fake = FakeHttp({("POST", TOKEN_URL): [pending(error)]})
            with self.assertRaises(AuthError) as ctx:
                await self._auth0(fake).finish_device_login(await self._start(fake))
            self.assertIn(error, str(ctx.exception))

    async def test_gives_up_when_the_code_expires(self):
        code = await self._start(FakeHttp({}))
        code.expires_in = 12
        fake = FakeHttp({("POST", TOKEN_URL): lambda r: pending()})
        with self.assertRaises(AuthError):
            await self._auth0(fake).finish_device_login(code)

    async def _start(self, fake: FakeHttp):
        fake.routes[("POST", DEVICE_URL)] = lambda r: httpx2.Response(
            200, json=DEVICE_CODE
        )
        return await self._auth0(fake).start_device_login()


class Provider(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.clock = Clock()
        self.store = TokenStore(self.tmp / "credentials.json")

    def _provider(self, fake: FakeHttp) -> TokenProvider:
        auth0 = Auth0(settings(self.tmp), fake.client(), clock=self.clock)
        return TokenProvider(auth0, self.store, clock=self.clock)

    async def test_no_login(self):
        with self.assertRaises(NotLoggedIn) as ctx:
            await self._provider(FakeHttp({})).token()
        self.assertIn("resland-mcp login", str(ctx.exception))

    async def test_live_token_is_used_as_is(self):
        self.store.save(Credentials(access_token="at", expires_at=self.clock.now + 600))
        fake = FakeHttp({})
        self.assertEqual(await self._provider(fake).token(), "at")
        self.assertEqual(fake.requests, [])

    async def test_expiring_token_is_refreshed_and_saved(self):
        self.store.save(
            Credentials(
                access_token="old", expires_at=self.clock.now + 30, refresh_token="rt-1"
            )
        )
        # Auth0 didn't rotate the refresh token this time: keep the old one.
        fake = FakeHttp({("POST", TOKEN_URL): [tokens(access="new", refresh=None)]})
        self.assertEqual(await self._provider(fake).token(), "new")
        sent = form(fake.requests[0])
        self.assertEqual(sent["grant_type"], "refresh_token")
        self.assertEqual(sent["refresh_token"], "rt-1")
        saved = self.store.load()
        self.assertEqual((saved.access_token, saved.refresh_token), ("new", "rt-1"))

    async def test_rotated_refresh_token_is_kept(self):
        self.store.save(
            Credentials(
                access_token="old", expires_at=self.clock.now - 1, refresh_token="rt-1"
            )
        )
        fake = FakeHttp({("POST", TOKEN_URL): [tokens(access="new", refresh="rt-2")]})
        await self._provider(fake).token()
        self.assertEqual(self.store.load().refresh_token, "rt-2")

    async def test_expired_without_refresh_token_needs_login(self):
        self.store.save(Credentials(access_token="old", expires_at=self.clock.now - 1))
        with self.assertRaises(NotLoggedIn):
            await self._provider(FakeHttp({})).token()

    async def test_rejected_refresh_needs_login(self):
        self.store.save(
            Credentials(
                access_token="old", expires_at=self.clock.now - 1, refresh_token="rt-1"
            )
        )
        fake = FakeHttp(
            {
                ("POST", TOKEN_URL): [
                    httpx2.Response(403, json={"error": "invalid_grant"})
                ]
            }
        )
        with self.assertRaises(NotLoggedIn):
            await self._provider(fake).token()

"""api.py — lifespan AMQP wiring and the maintenance-mode middleware
(503 for everyone but site admins and /docs). The flag itself lives in the
site_settings table — these tests stub the cached read.

Run: .venv/bin/python -m unittest backend.api.tests.test_api_app -v
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from api import api, auth, deps, site_settings

from .test_auth import _admin_conn, _token, _verify_patched


class Lifespan(unittest.IsolatedAsyncioTestCase):
    async def test_amqp_client_set_up_and_closed(self):
        client = MagicMock()
        client.setup = AsyncMock()
        client.close = AsyncMock()
        with (
            patch.object(api, "AmqpClient", return_value=client),
            patch.object(api.account_sweeper, "run_forever", new=AsyncMock()),
        ):
            async with api.lifespan(api.app):
                client.setup.assert_awaited_once()
                self.assertIs(deps.amqp_client, client)
        client.close.assert_awaited_once()
        self.assertIsNone(deps.amqp_client)

    async def test_deletion_sweeper_runs_for_the_apps_lifetime(self):
        client = MagicMock()
        client.setup = AsyncMock()
        client.close = AsyncMock()
        started = asyncio.Event()
        cancelled = asyncio.Event()

        async def sweeper():
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise

        with (
            patch.object(api, "AmqpClient", return_value=client),
            patch.object(api.account_sweeper, "run_forever", new=sweeper),
        ):
            async with api.lifespan(api.app):
                await asyncio.wait_for(started.wait(), 1)
        self.assertTrue(cancelled.is_set())


class MaintenanceMode(unittest.IsolatedAsyncioTestCase):
    async def _call(self, maint, admin, docs, stripe_webhook=False):
        req = MagicMock()
        nxt = AsyncMock(return_value="response")
        with (
            patch.object(
                site_settings,
                "is_maintenance_mode",
                new=AsyncMock(return_value=maint),
            ),
            patch.object(
                api, "is_site_admin_request", new=AsyncMock(return_value=admin)
            ),
            patch.object(api, "is_docs_request", return_value=docs),
            patch.object(
                api,
                "is_stripe_webhook_request",
                return_value=stripe_webhook,
            ),
        ):
            return await api.maintenance_mode(req, nxt), nxt

    async def test_off_passes_through(self):
        resp, nxt = await self._call(False, False, False)
        self.assertEqual(resp, "response")
        nxt.assert_awaited_once()

    async def test_on_blocks_normal_user_with_503(self):
        resp, nxt = await self._call(True, False, False)
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.headers["retry-after"], "600")
        nxt.assert_not_awaited()

    async def test_on_lets_admin_through(self):
        resp, nxt = await self._call(True, True, False)
        self.assertEqual(resp, "response")
        nxt.assert_awaited_once()

    async def test_on_lets_docs_through(self):
        resp, nxt = await self._call(True, False, True)
        self.assertEqual(resp, "response")
        nxt.assert_awaited_once()

    async def test_on_lets_stripe_webhook_through(self):
        # Stripe calls unauthenticated — a 503 would strand paid checkouts.
        resp, nxt = await self._call(True, False, False, stripe_webhook=True)
        self.assertEqual(resp, "response")
        nxt.assert_awaited_once()

    def test_stripe_webhook_path_matches(self):
        req = MagicMock()
        req.url.path = "/stripe/webhook"
        self.assertTrue(api.is_stripe_webhook_request(req))
        req.url.path = "/billing/checkout"
        self.assertFalse(api.is_stripe_webhook_request(req))


class MaintenanceModeE2E(unittest.TestCase):
    """The whole middleware stack via TestClient: real RS256 JWTs, only the
    JWKS fetch and the Postgres connection are stubbed."""

    def _client(self, admin_row):
        conn = _admin_conn(admin_row)
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=False)
        patches = [
            patch.object(
                site_settings,
                "is_maintenance_mode",
                new=AsyncMock(return_value=True),
            ),
            *_verify_patched(),
            patch.object(
                auth.AsyncConnection, "connect", new=AsyncMock(return_value=cm)
            ),
        ]
        for p in patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in patches])
        return TestClient(api.app)

    def test_admin_reaches_router(self):
        # /nope has no route — a 404 proves the request passed the middleware.
        r = self._client((True,)).get(
            "/nope", headers={"Authorization": f"Bearer {_token()}"}
        )
        self.assertEqual(r.status_code, 404)

    def test_non_admin_jwt_503(self):
        r = self._client((False,)).get(
            "/nope", headers={"Authorization": f"Bearer {_token()}"}
        )
        self.assertEqual(r.status_code, 503)

    def test_no_token_503(self):
        self.assertEqual(self._client((True,)).get("/nope").status_code, 503)

    def test_bad_token_503(self):
        r = self._client((True,)).get(
            "/nope", headers={"Authorization": "Bearer not.a.jwt"}
        )
        self.assertEqual(r.status_code, 503)

    def test_docs_infra_exempt(self):
        # openapi.json backs /docs and /redoc — exempting only /docs leaves
        # the Swagger UI unable to fetch its spec during maintenance.
        client = self._client((False,))
        self.assertEqual(client.get("/docs").status_code, 200)
        self.assertEqual(client.get("/openapi.json").status_code, 200)
        self.assertEqual(client.get("/redoc").status_code, 200)

    def test_stripe_webhook_exempt(self):
        # GET on the POST-only route 405s — proves it cleared the middleware.
        r = self._client((False,)).get("/stripe/webhook")
        self.assertEqual(r.status_code, 405)


if __name__ == "__main__":
    unittest.main()

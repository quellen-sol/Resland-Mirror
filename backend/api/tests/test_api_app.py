"""api.py — lifespan AMQP wiring and the maintenance-mode middleware
(503 for everyone but site admins and /docs).

Run: .venv/bin/python -m unittest backend.api.tests.test_api_app -v
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from api import api, deps


class Lifespan(unittest.IsolatedAsyncioTestCase):
    async def test_amqp_client_set_up_and_closed(self):
        client = MagicMock()
        client.setup = AsyncMock()
        client.close = AsyncMock()
        with patch.object(api, "AmqpClient", return_value=client):
            async with api.lifespan(api.app):
                client.setup.assert_awaited_once()
                self.assertIs(deps.amqp_client, client)
        client.close.assert_awaited_once()
        self.assertIsNone(deps.amqp_client)


class MaintenanceMode(unittest.IsolatedAsyncioTestCase):
    async def _call(self, maint, admin, docs):
        req = MagicMock()
        nxt = AsyncMock(return_value="response")
        with (
            patch.object(api, "MAINTENANCE_MODE", maint),
            patch.object(
                api, "is_site_admin_request", new=AsyncMock(return_value=admin)
            ),
            patch.object(api, "is_docs_request", return_value=docs),
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


if __name__ == "__main__":
    unittest.main()

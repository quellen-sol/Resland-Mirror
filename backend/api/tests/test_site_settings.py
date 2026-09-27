"""site_settings — the DB-backed kill switches behind the TTL cache, and the
/admin/settings endpoints + payments-paused checkout guard that consume it.

Run: .venv/bin/python -m unittest backend.api.tests.test_site_settings -v
"""

import datetime
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from api import site_settings
from api.admin import model as admin_model, service as admin_service
from api.billing import model as billing_model, service as billing_service

from .helpers import _Pg, one


def _row(maint=False, paused=False, updated=None):
    return one(
        (maint, paused, updated or datetime.datetime(2025, 1, 1, 12, 0, 0))
    )


class _Reset(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        site_settings._reset_cache()

    def tearDown(self):
        site_settings._reset_cache()


class Get(_Reset):
    async def test_reads_row(self):
        pg = _Pg([_row(maint=True, paused=True)])
        s = await site_settings.get(pg)
        self.assertTrue(s.maintenance_mode)
        self.assertTrue(s.payments_paused)
        self.assertEqual(s.updated_at.isoformat(), "2025-01-01T12:00:00")

    async def test_caches_within_ttl(self):
        pg = _Pg([_row(maint=True)])
        await site_settings.get(pg)
        again = await site_settings.get(pg)
        self.assertTrue(again.maintenance_mode)
        self.assertEqual(len(pg.queries), 1)

    async def test_refreshes_after_ttl(self):
        pg = _Pg([_row(maint=True), _row(maint=False)])
        first = await site_settings.get(pg)
        self.assertTrue(first.maintenance_mode)
        site_settings._cache_expires_at = 0.0  # force expiry
        second = await site_settings.get(pg)
        self.assertFalse(second.maintenance_mode)
        self.assertEqual(len(pg.queries), 2)

    async def test_missing_row_seeds_from_env(self):
        pg = _Pg(
            [
                one(None),  # SELECT -> no row
                one(None),  # INSERT ON CONFLICT DO NOTHING
                _row(maint=True),  # re-SELECT -> seeded row
            ]
        )
        with patch.object(site_settings, "MAINTENANCE_MODE", True):
            s = await site_settings.get(pg)
        self.assertTrue(s.maintenance_mode)
        self.assertEqual(len(pg.queries), 3)
        self.assertIn("INSERT INTO site_settings", pg.queries[1][0])
        self.assertEqual(pg.queries[1][1], (1, True))

    async def test_no_conn_opens_its_own(self):
        conn = _Pg([_row(paused=True)])
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=False)
        with patch.object(
            site_settings.AsyncConnection,
            "connect",
            new=AsyncMock(return_value=cm),
        ):
            s = await site_settings.get()
        self.assertTrue(s.payments_paused)

    async def test_db_error_fails_open(self):
        pg = _Pg()
        pg.cursor = MagicMock(side_effect=RuntimeError("down"))
        s = await site_settings.get(pg)
        self.assertFalse(s.maintenance_mode)
        self.assertFalse(s.payments_paused)

    async def test_db_error_serves_stale_cache(self):
        site_settings._cache = site_settings.SiteSettings(
            maintenance_mode=True, payments_paused=True
        )
        site_settings._cache_expires_at = 0.0
        pg = _Pg()
        pg.cursor = MagicMock(side_effect=RuntimeError("down"))
        s = await site_settings.get(pg)
        self.assertTrue(s.maintenance_mode)
        self.assertTrue(s.payments_paused)


class Update(_Reset):
    async def test_updates_and_writes_through(self):
        site_settings._cache = site_settings.SiteSettings(
            maintenance_mode=False, payments_paused=False
        )
        site_settings._cache_expires_at = float("inf")
        pg = _Pg([_row(maint=True, paused=False)])
        s = await site_settings.update(pg, maintenance_mode=True)
        self.assertTrue(s.maintenance_mode)
        self.assertFalse(s.payments_paused)
        self.assertIn("UPDATE site_settings", pg.queries[0][0])
        self.assertEqual(pg.queries[0][1], (True, False, 1))
        # Write-through: a fresh read doesn't touch the DB again.
        again = await site_settings.get(pg)
        self.assertTrue(again.maintenance_mode)
        self.assertEqual(len(pg.queries), 1)

    async def test_partial_update_keeps_other_flag(self):
        pg = _Pg([_row(maint=True, paused=False), _row(maint=True, paused=True)])
        await site_settings.update(pg, payments_paused=True)
        self.assertEqual(pg.queries[1][1], (True, True, 1))


class AdminEndpoints(_Reset):
    async def test_get_settings(self):
        pg = _Pg([_row(maint=True)])
        resp = await admin_service.get_settings(pg)
        self.assertTrue(resp.maintenance_mode)
        self.assertEqual(resp.updated_at, "2025-01-01T12:00:00")

    async def test_update_settings(self):
        pg = _Pg([_row(), _row(paused=True)])
        resp = await admin_service.update_settings(
            pg, admin_model.SiteSettingsUpdate(payments_paused=True)
        )
        self.assertTrue(resp.payments_paused)
        self.assertFalse(resp.maintenance_mode)


class PaymentsPausedGuard(_Reset):
    async def test_checkout_blocked_when_paused(self):
        pg = _Pg([_row(paused=True)])
        with (
            patch.object(billing_service, "STRIPE_SECRET_KEY", "sk_test_x"),
            self.assertRaises(HTTPException) as ctx,
        ):
            await billing_service.create_checkout(
                pg_conn=pg,
                user_id="u1",
                req=billing_model.CheckoutRequest(pack_id="starter"),
            )
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("paused", ctx.exception.detail)
        # No customer lookup, no Stripe session — the guard fires first.
        self.assertEqual(len(pg.queries), 1)

    async def test_checkout_proceeds_when_unpaused(self):
        pg = _Pg([_row(), one(("cus_1",))])
        session_create = MagicMock(
            return_value=type(
                "S", (), {"id": "cs_1", "url": "https://checkout.test/pay"}
            )()
        )
        with (
            patch.object(billing_service, "STRIPE_SECRET_KEY", "sk_test_x"),
            patch.object(
                billing_service.stripe.checkout.Session,
                "create",
                session_create,
            ),
        ):
            res = await billing_service.create_checkout(
                pg_conn=pg,
                user_id="u1",
                req=billing_model.CheckoutRequest(pack_id="starter"),
            )
        self.assertEqual(res.url, "https://checkout.test/pay")
        session_create.assert_called_once()


if __name__ == "__main__":
    unittest.main()

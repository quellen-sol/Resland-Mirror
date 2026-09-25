"""admin service — response assembly for users/usage/purchases/models and
the upsert_model validation guards.

Run: .venv/bin/python -m unittest backend.api.tests.test_admin_service -v
"""

import datetime
import unittest

from fastapi import HTTPException

from api.admin import model, service

from .helpers import _Pg, _Result


class ListUsers(unittest.IsolatedAsyncioTestCase):
    async def test_rows_mapped(self):
        pg = _Pg(
            [
                [
                    ("u1", "a@x.com", "Ann", 500, 120.5, 1000, 2000, 300),
                ]
            ]
        )
        resp = await service.list_users(pg)
        u = resp.users[0]
        self.assertEqual(u.auth0_id, "u1")
        self.assertEqual(u.balance_cents, 500.0)
        self.assertEqual(u.cents_used, 120.5)
        self.assertEqual(u.input_tokens, 1000)
        self.assertEqual(u.cents_purchased, 300)

    async def test_empty(self):
        resp = await service.list_users(_Pg([[]]))
        self.assertEqual(resp.users, [])


class GetUsage(unittest.IsolatedAsyncioTestCase):
    async def test_all_sections_mapped(self):
        pg = _Pg(
            [
                [("openrouter:m", 3, 100, 50, 2.5)],
                [("SUGGESTION", 3, 2.5)],
                [(datetime.date(2025, 1, 1), 1.5)],
                [
                    (
                        1,
                        "u1",
                        "TAILOR",
                        "j1",
                        "openrouter:m",
                        10,
                        5,
                        0.5,
                        0.4,
                        datetime.datetime(2025, 1, 2),
                    )
                ],
            ]
        )
        resp = await service.get_usage(pg)
        self.assertEqual(resp.by_model[0].model, "openrouter:m")
        self.assertEqual(resp.by_kind[0].job_kind, "SUGGESTION")
        self.assertEqual(resp.by_day[0].day, "2025-01-01")
        r = resp.recent[0]
        self.assertEqual(r.job_id, "j1")
        self.assertEqual(r.actual_cost_cents, 0.4)
        self.assertEqual(r.created_at, "2025-01-02T00:00:00")

    async def test_null_actual_cost(self):
        pg = _Pg(
            [
                [],
                [],
                [],
                [(1, "u1", "T", "j", "m", 1, 1, 0.1, None, datetime.datetime.now())],
            ]
        )
        resp = await service.get_usage(pg)
        self.assertIsNone(resp.recent[0].actual_cost_cents)


class ListPurchases(unittest.IsolatedAsyncioTestCase):
    async def test_revenue_and_rows(self):
        pg = _Pg(
            [
                [("cs_1", "u1", 500, 500, "usd", "COMPLETED", datetime.datetime(2025, 1, 1))],
                [(1500,)],
            ]
        )
        resp = await service.list_purchases(pg)
        self.assertEqual(resp.revenue_cents, 1500)
        self.assertEqual(resp.purchases[0].id, "cs_1")
        self.assertEqual(resp.purchases[0].created_at, "2025-01-01T00:00:00")


class ListModels(unittest.IsolatedAsyncioTestCase):
    async def test_rows_mapped(self):
        pg = _Pg([[("openrouter:m", "Name", 0.1, 0.5, True, False, 1)]])
        resp = await service.list_models(pg)
        m = resp.models[0]
        self.assertEqual(m.id, "openrouter:m")
        self.assertEqual(m.cents_per_1k_input, 0.1)
        self.assertFalse(m.is_default)


def _upsert(**over):
    base = dict(
        display_name="M",
        cents_per_1k_input=0.1,
        cents_per_1k_output=0.5,
        enabled=True,
        is_default=False,
        sort_order=0,
    )
    base.update(over)
    return model.ModelPricingUpsert(**base)


class UpsertModel(unittest.IsolatedAsyncioTestCase):
    async def test_non_openrouter_id_400(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.upsert_model(_Pg(), "openai:gpt", _upsert())
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_negative_rate_400(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.upsert_model(
                _Pg(), "openrouter:m", _upsert(cents_per_1k_input=-1)
            )
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_disabled_default_400(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.upsert_model(
                _Pg(), "openrouter:m", _upsert(is_default=True, enabled=False)
            )
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_default_clears_other_defaults_first(self):
        pg = _Pg()
        row = await service.upsert_model(
            pg, "openrouter:m", _upsert(is_default=True)
        )
        self.assertTrue(row.is_default)
        self.assertIn(
            "UPDATE model_pricing SET is_default = false", pg.queries[0][0]
        )
        self.assertIn("INSERT INTO model_pricing", pg.queries[1][0])

    async def test_non_default_skips_clear(self):
        pg = _Pg()
        await service.upsert_model(pg, "openrouter:m", _upsert())
        self.assertEqual(len(pg.queries), 1)
        self.assertIn("INSERT", pg.queries[0][0])


class DeleteModel(unittest.IsolatedAsyncioTestCase):
    async def test_not_found_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.delete_model(_Pg([_Result(rowcount=0)]), "m")
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_deleted(self):
        await service.delete_model(_Pg([_Result(rowcount=1)]), "m")


if __name__ == "__main__":
    unittest.main()

"""balance.py — require_balance gating and validate_model_choice whitelist.

Run: .venv/bin/python -m unittest backend.api.tests.test_balance -v
"""

import unittest

from fastapi import HTTPException

from api.balance import require_balance, validate_model_choice

from .helpers import _Pg


class RequireBalance(unittest.IsolatedAsyncioTestCase):
    async def test_positive_balance_returned(self):
        pg = _Pg([[(500,)]])
        bal = await require_balance(pg, "u1")
        self.assertEqual(bal, 500.0)

    async def test_zero_balance_402(self):
        pg = _Pg([[(0,)]])
        with self.assertRaises(HTTPException) as ctx:
            await require_balance(pg, "u1")
        self.assertEqual(ctx.exception.status_code, 402)
        self.assertEqual(ctx.exception.detail, "insufficient_balance")

    async def test_missing_user_402(self):
        pg = _Pg([[]])
        with self.assertRaises(HTTPException) as ctx:
            await require_balance(pg, "ghost")
        self.assertEqual(ctx.exception.status_code, 402)


class ValidateModelChoice(unittest.IsolatedAsyncioTestCase):
    async def test_none_passes_without_query(self):
        pg = _Pg()
        self.assertIsNone(await validate_model_choice(pg, None))
        self.assertEqual(pg.queries, [])

    async def test_enabled_model_returned(self):
        pg = _Pg([[(1,)]])
        self.assertEqual(
            await validate_model_choice(pg, "openrouter:x"), "openrouter:x"
        )
        self.assertIn("model_pricing", pg.queries[0][0])

    async def test_unknown_model_400(self):
        pg = _Pg([[]])
        with self.assertRaises(HTTPException) as ctx:
            await validate_model_choice(pg, "bogus")
        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()

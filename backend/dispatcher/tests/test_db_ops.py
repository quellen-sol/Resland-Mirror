"""record_token_usage tests — need a live Postgres (TEST_PG_URL).

generation_ids=[] always takes the rate-card path (fetch_generation_cost_cents
returns None before touching OpenRouter); the actual-cost path is stubbed.
"""

try:
    import pytest
except ImportError:
    # unittest discovery has no pytest — the pytest-function tests are
    # ignored by unittest anyway, so a decorator stub is all the module
    # needs to stay importable for its TestCase classes.
    class _PytestStub:
        @staticmethod
        def fixture(f=None, **_kw):
            return f if f is not None else (lambda g: g)

        def __getattr__(self, name):
            raise ImportError("pytest is required to run this test")

    pytest = _PytestStub()

from dispatcher.runners import db_ops

MODEL = "openrouter:test/model"


@pytest.fixture
def user(pg):
    pg.execute(
        'INSERT INTO "user" (auth0_id, balance_cents) VALUES (%s, %s)',
        ("u1", 1000),
    )
    pg.execute(
        """
        INSERT INTO model_pricing
          (id, display_name, cents_per_1k_input, cents_per_1k_output, enabled)
        VALUES (%s, 'Test', 0.16, 1.25, true)
        """,
        (MODEL,),
    )
    return "u1"


def balance(pg, user_id="u1"):
    row = pg.execute(
        'SELECT balance_cents FROM "user" WHERE auth0_id = %s', (user_id,)
    ).fetchone()
    return float(row[0]) if row else None


def charge(pg, user_id="u1", job_id="job1", model=MODEL, in_tok=1000, out_tok=1000):
    return db_ops.record_token_usage(
        pg,
        user_id=user_id,
        job_kind="SUGGESTION",
        job_id=job_id,
        model=model,
        input_tokens=in_tok,
        output_tokens=out_tok,
        generation_ids=[],
    )


def test_rate_card_charge(pg, user):
    # (1000*0.16 + 1000*1.25)/1000 = 1.41¢
    charged = charge(pg)
    assert charged == pytest.approx(1.41)
    assert balance(pg) == pytest.approx(998.59)


def test_redelivered_job_never_double_charges(pg, user):
    """AMQP only acks on completion, so a mid-job crash re-runs the job —
    the second run must see the existing ledger row and not debit again."""
    first = charge(pg)
    second = charge(pg)
    assert second == pytest.approx(first)
    assert balance(pg) == pytest.approx(1000 - first)
    count = pg.execute(
        "SELECT COUNT(*) FROM token_usage WHERE job_kind = 'SUGGESTION'"
    ).fetchone()[0]
    assert count == 1


def test_each_turn_of_a_session_is_charged(pg, user):
    """Answers and retries reuse the session id; their per-turn ledger keys
    must each debit, while a redelivery of one turn still doesn't."""
    first = charge(pg, job_id=db_ops.usage_job_id("s1", {"turn_id": "t1"}))
    second = charge(pg, job_id=db_ops.usage_job_id("s1", {"turn_id": "t2"}))
    redelivered = charge(pg, job_id=db_ops.usage_job_id("s1", {"turn_id": "t2"}))
    assert redelivered == pytest.approx(second)
    assert balance(pg) == pytest.approx(1000 - first - second)
    count = pg.execute("SELECT COUNT(*) FROM token_usage").fetchone()[0]
    assert count == 2


def test_actual_cost_with_markup(pg, user, monkeypatch):
    monkeypatch.setattr(
        db_ops, "fetch_generation_cost_cents", lambda ids: 1.0
    )
    charged = db_ops.record_token_usage(
        pg,
        user_id=user,
        job_kind="SUGGESTION",
        job_id="job1",
        model=MODEL,
        input_tokens=10,
        output_tokens=10,
        generation_ids=["gen_1"],
    )
    # 1.0¢ actual * 1.25 markup = 1.25¢
    assert charged == pytest.approx(1.25)
    row = pg.execute(
        "SELECT actual_cost_cents FROM token_usage WHERE job_id = 'job1'"
    ).fetchone()
    assert float(row[0]) == pytest.approx(1.0)


def test_fallback_rate_when_model_unpriced(pg, user):
    # 2000 input * 0.16¢/1k = 0.32¢ (fallback consts, model not in card)
    charged = charge(pg, model="openrouter:unpriced", in_tok=2000, out_tok=0)
    assert charged == pytest.approx(0.32)


def test_overrun_floors_at_zero(pg, user):
    pg.execute(
        'UPDATE "user" SET balance_cents = 0.5 WHERE auth0_id = %s', ("u1",)
    )
    charged = charge(pg)
    assert charged == pytest.approx(1.41)
    assert balance(pg) == 0


def test_zero_tokens_no_row(pg, user):
    charged = charge(pg, in_tok=0, out_tok=0)
    assert charged == 0
    count = pg.execute("SELECT COUNT(*) FROM token_usage").fetchone()[0]
    assert count == 0
    assert balance(pg) == 1000
"""Unit tests for token-usage cost resolution in dispatcher.runners.db_ops.

Run from the repo root with the workspace venv:
    .venv/bin/python -m unittest backend/dispatcher/tests/test_db_ops.py -v
"""

import math
import unittest
from unittest.mock import MagicMock, patch

import httpx
from openrouter import components, errors

from dispatcher.runners import db_ops


def make_not_found_error() -> errors.NotFoundResponseError:
    data = errors.NotFoundResponseErrorData(
        error=components.NotFoundResponseErrorData(
            code=404, message="Generation gen-x not found"
        )
    )
    return errors.NotFoundResponseError(
        data, httpx.Response(404, text="Generation gen-x not found")
    )


def make_openrouter_client(behaviors: list) -> MagicMock:
    """behaviors: per-id list of either a cost (float, USD) or an Exception."""
    client = MagicMock()
    responses = MagicMock()
    responses.data = MagicMock()
    calls = iter(behaviors)

    def get_generation(id: str):
        behavior = next(calls)
        if isinstance(behavior, Exception):
            raise behavior
        responses.data.total_cost = behavior
        return responses

    client.generations.get_generation.side_effect = get_generation
    return client


def make_pg(pricing_row=None) -> MagicMock:
    """psycopg.Connection stand-in: execute() -> result with fetchone()."""
    pg = MagicMock()
    result = MagicMock()
    result.fetchone.return_value = pricing_row
    pg.execute.return_value = result
    return pg


def inserted_amount(pg: MagicMock) -> float:
    """The amount_cents arg from the INSERT INTO token_usage call."""
    for call in pg.execute.call_args_list:
        sql, params = call.args
        if "INSERT INTO token_usage" in sql:
            return params[6]
    raise AssertionError("token_usage insert was never executed")


class FetchGenerationCostCentsTest(unittest.TestCase):
    def test_sums_costs_across_generations(self):
        client = make_openrouter_client([0.001, 0.0025])
        with (
            patch.object(db_ops, "OPENROUTER_API_KEY", "k"),
            patch.object(db_ops, "OpenRouter", return_value=client),
        ):
            self.assertAlmostEqual(
                db_ops.fetch_generation_cost_cents(["gen-1", "gen-2"]), 0.35
            )

    def test_retries_on_not_found_then_succeeds(self):
        client = make_openrouter_client(
            [make_not_found_error(), make_not_found_error(), 0.004]
        )
        with (
            patch.object(db_ops, "OPENROUTER_API_KEY", "k"),
            patch.object(db_ops, "OpenRouter", return_value=client),
            patch.object(db_ops.time, "sleep"),
        ):
            self.assertAlmostEqual(
                db_ops.fetch_generation_cost_cents(["gen-1"]), 0.4
            )
            self.assertEqual(client.generations.get_generation.call_count, 3)

    def test_not_found_past_deadline_returns_none(self):
        client = make_openrouter_client([make_not_found_error()] * 10)
        with (
            patch.object(db_ops, "OPENROUTER_API_KEY", "k"),
            patch.object(db_ops, "OpenRouter", return_value=client),
            patch.object(db_ops, "STATS_LOOKUP_TIMEOUT_S", 0),
            patch.object(db_ops.time, "sleep"),
        ):
            self.assertIsNone(db_ops.fetch_generation_cost_cents(["gen-1"]))

    def test_non_404_error_is_not_retried(self):
        client = make_openrouter_client([ValueError("boom"), 0.001])
        with (
            patch.object(db_ops, "OPENROUTER_API_KEY", "k"),
            patch.object(db_ops, "OpenRouter", return_value=client),
        ):
            self.assertIsNone(db_ops.fetch_generation_cost_cents(["gen-1"]))
            self.assertEqual(client.generations.get_generation.call_count, 1)

    def test_any_unresolved_id_returns_none(self):
        client = make_openrouter_client([0.001, ValueError("boom")])
        with (
            patch.object(db_ops, "OPENROUTER_API_KEY", "k"),
            patch.object(db_ops, "OpenRouter", return_value=client),
        ):
            self.assertIsNone(
                db_ops.fetch_generation_cost_cents(["gen-1", "gen-2"])
            )

    def test_no_ids_or_key_returns_none(self):
        self.assertIsNone(db_ops.fetch_generation_cost_cents([]))
        with patch.object(db_ops, "OPENROUTER_API_KEY", ""):
            self.assertIsNone(db_ops.fetch_generation_cost_cents(["gen-1"]))


class UsageJobIdTest(unittest.TestCase):
    def test_turn_id_scopes_the_key(self):
        self.assertEqual(db_ops.usage_job_id("s1", {"turn_id": "t1"}), "s1:t1")

    def test_turns_of_one_session_get_distinct_keys(self):
        self.assertNotEqual(
            db_ops.usage_job_id("s1", {"turn_id": "t1"}),
            db_ops.usage_job_id("s1", {"turn_id": "t2"}),
        )

    def test_legacy_job_without_turn_id_keeps_bare_id(self):
        self.assertEqual(db_ops.usage_job_id("s1", {}), "s1")
        self.assertEqual(db_ops.usage_job_id("s1", {"turn_id": ""}), "s1")
        self.assertEqual(db_ops.usage_job_id("s1", {"turn_id": 7}), "s1")


class RecordTokenUsageTest(unittest.TestCase):
    def test_inline_cost_skips_stats_lookup(self):
        pg = make_pg()
        with patch.object(db_ops, "OpenRouter") as client_cls:
            charged = db_ops.record_token_usage(
                pg,
                user_id="u1",
                job_kind="SUGGESTION",
                job_id="s1",
                model="openrouter:m",
                input_tokens=100,
                output_tokens=50,
                generation_ids=["gen-1"],
                cost_usd=0.001,
            )
        client_cls.assert_not_called()
        # $0.001 -> 0.1c, markup 1.25 -> 0.125c
        self.assertAlmostEqual(charged, 0.125)
        self.assertAlmostEqual(inserted_amount(pg), 0.125)

    def test_stats_lookup_used_when_inline_cost_missing(self):
        pg = make_pg()
        client = make_openrouter_client([0.002])
        with (
            patch.object(db_ops, "OPENROUTER_API_KEY", "k"),
            patch.object(db_ops, "OpenRouter", return_value=client),
        ):
            charged = db_ops.record_token_usage(
                pg,
                user_id="u1",
                job_kind="TAILOR",
                job_id="r1",
                model="openrouter:m",
                input_tokens=100,
                output_tokens=50,
                generation_ids=["gen-1"],
                cost_usd=None,
            )
        # $0.002 -> 0.2c, markup 1.25 -> 0.25c
        self.assertAlmostEqual(charged, 0.25)

    def test_rate_card_used_when_all_cost_sources_fail(self):
        pg = make_pg(pricing_row=(0.5, 2.0))
        client = make_openrouter_client([ValueError("boom")])
        with (
            patch.object(db_ops, "OPENROUTER_API_KEY", "k"),
            patch.object(db_ops, "OpenRouter", return_value=client),
        ):
            charged = db_ops.record_token_usage(
                pg,
                user_id="u1",
                job_kind="TAILOR",
                job_id="r1",
                model="openrouter:m",
                input_tokens=1000,
                output_tokens=100,
                generation_ids=["gen-1"],
                cost_usd=None,
            )
        # (1000*0.5 + 100*2.0)/1000 = 0.7c — no markup on the rate card
        self.assertAlmostEqual(charged, 0.7)

    def test_fallback_rates_when_model_unpriced(self):
        pg = make_pg(pricing_row=None)
        client = make_openrouter_client([ValueError("boom")])
        with (
            patch.object(db_ops, "OPENROUTER_API_KEY", "k"),
            patch.object(db_ops, "OpenRouter", return_value=client),
        ):
            charged = db_ops.record_token_usage(
                pg,
                user_id="u1",
                job_kind="TAILOR",
                job_id="r1",
                model="openrouter:unknown",
                input_tokens=1000,
                output_tokens=1000,
                generation_ids=["gen-1"],
                cost_usd=None,
            )
        expected = math.ceil(
            (1000 * db_ops.FALLBACK_CENTS_PER_1K_INPUT
             + 1000 * db_ops.FALLBACK_CENTS_PER_1K_OUTPUT) / 1000 * 10_000
        ) / 10_000
        self.assertAlmostEqual(charged, expected)

    def test_no_tokens_is_noop(self):
        pg = make_pg()
        charged = db_ops.record_token_usage(
            pg,
            user_id="u1",
            job_kind="SUGGESTION",
            job_id="s1",
            model="openrouter:m",
            input_tokens=0,
            output_tokens=0,
            generation_ids=[],
            cost_usd=0.5,
        )
        self.assertEqual(charged, 0.0)
        pg.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()

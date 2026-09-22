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

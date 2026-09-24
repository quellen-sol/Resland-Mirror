"""record_token_usage tests — need a live Postgres (TEST_PG_URL).

generation_ids=[] always takes the rate-card path (fetch_generation_cost_cents
returns None before touching OpenRouter); the actual-cost path is stubbed.
"""

import pytest

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

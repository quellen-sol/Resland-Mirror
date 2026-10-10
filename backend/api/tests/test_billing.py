"""Billing service tests — need a live Postgres (TEST_PG_URL).

Stripe is never hit: `stripe.Webhook.construct_event` is patched to return
crafted events, and `Customer.create`/`Session.create` are stubbed.
"""

from types import SimpleNamespace

try:
    import pytest
except ImportError:
    # unittest discovery has no pytest — this module is all pytest-function
    # tests, so it collects zero tests under unittest; the stub just keeps
    # the module importable.
    class _PytestStub:
        @staticmethod
        def fixture(*_a, **_kw):
            return lambda g: g

        def __getattr__(self, name):
            raise ImportError("pytest is required to run this test")

    pytest = _PytestStub()
import stripe
from fastapi import HTTPException

from api.balance import require_balance, validate_model_choice
from api.billing import model, service

from .helpers import _Pg


@pytest.fixture(autouse=True)
def stripe_env(monkeypatch):
    monkeypatch.setattr(service, "STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setattr(service, "STRIPE_WEBHOOK_SECRET", "whsec_x")


@pytest.fixture
def stripe_events(monkeypatch):
    """Makes handle_webhook see whatever event is stored under 'event'.

    The stub builds real Stripe objects, not plain dicts — stripe-python v15
    objects have no .get(), which is exactly what production events deliver.
    """
    holder = {}
    monkeypatch.setattr(
        stripe.Webhook,
        "construct_event",
        staticmethod(
            lambda *args, **kwargs: stripe.Event.construct_from(
                holder["event"], key=None
            )
        ),
    )
    return holder


def checkout_event(
    event_type="checkout.session.completed",
    session_id="cs_1",
    user_id="u1",
    cents="500",
    payment_intent="pi_1",
    amount_total=500,
    payment_status="paid",
):
    return {
        "type": event_type,
        "data": {
            "object": {
                "id": session_id,
                "client_reference_id": user_id,
                "metadata": {"pack_id": "starter", "cents": cents},
                "amount_total": amount_total,
                "currency": "usd",
                "payment_intent": payment_intent,
                "payment_status": payment_status,
            }
        },
    }


def completed_event(**kwargs):
    return checkout_event("checkout.session.completed", **kwargs)


def async_succeeded_event(**kwargs):
    return checkout_event("checkout.session.async_payment_succeeded", **kwargs)


def charge_refunded_event(payment_intent="pi_1", amount=500, amount_refunded=500):
    return {
        "type": "charge.refunded",
        "data": {
            "object": {
                "id": "ch_1",
                "payment_intent": payment_intent,
                "amount": amount,
                "amount_refunded": amount_refunded,
            }
        },
    }


async def send(pg, event):
    return await service.handle_webhook(
        pg_conn=pg, payload=b"{}", sig_header="sig"
    )


async def get_balance(pg, user_id="u1"):
    cur = await pg.execute(
        'SELECT balance_cents FROM "user" WHERE auth0_id = %s', (user_id,)
    )
    row = await cur.fetchone()
    return float(row[0]) if row else None


async def purchase_row(pg, purchase_id):
    cur = await pg.execute(
        "SELECT status, payment_intent_id FROM balance_purchase WHERE id = %s",
        (purchase_id,),
    )
    return await cur.fetchone()


async def test_completed_credits_once(pg, user, stripe_events):
    stripe_events["event"] = completed_event()
    assert await send(pg, stripe_events["event"]) == {"ok": True}
    assert await get_balance(pg) == 500
    row = await purchase_row(pg, "cs_1")
    assert row[0] == "COMPLETED"
    assert row[1] == "pi_1"

    # Stripe redelivery must not double-credit.
    await send(pg, stripe_events["event"])
    assert await get_balance(pg) == 500


async def test_late_pending_insert_does_not_reset_completed(
    pg, user, stripe_events
):
    """The checkout endpoint's PENDING INSERT can commit *after* the webhook
    already completed the row — DO NOTHING must not regress the status."""
    stripe_events["event"] = completed_event()
    await send(pg, stripe_events["event"])
    await pg.execute(
        """
        INSERT INTO balance_purchase
          (id, user_id, cents, amount_cents, currency, status)
        VALUES ('cs_1', 'u1', 500, 500, 'usd', 'PENDING')
        ON CONFLICT (id) DO NOTHING
        """
    )
    row = await purchase_row(pg, "cs_1")
    assert row[0] == "COMPLETED"
    assert await get_balance(pg) == 500


async def test_expired_marks_row_no_credit(pg, user, stripe_events):
    await pg.execute(
        """
        INSERT INTO balance_purchase
          (id, user_id, cents, amount_cents, currency, status)
        VALUES ('cs_1', 'u1', 500, 500, 'usd', 'PENDING')
        """
    )
    stripe_events["event"] = {
        "type": "checkout.session.expired",
        "data": {"object": {"id": "cs_1"}},
    }
    await send(pg, stripe_events["event"])
    row = await purchase_row(pg, "cs_1")
    assert row[0] == "EXPIRED"
    assert await get_balance(pg) == 0


async def test_bad_signature_rejected(pg, user, monkeypatch):
    monkeypatch.setattr(
        stripe.Webhook,
        "construct_event",
        staticmethod(
            lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("bad sig"))
        ),
    )
    with pytest.raises(HTTPException) as exc:
        await service.handle_webhook(pg_conn=pg, payload=b"{}", sig_header="s")
    assert exc.value.status_code == 400
    assert await get_balance(pg) == 0


async def test_event_without_metadata_is_noop(pg, user, stripe_events):
    stripe_events["event"] = {
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_other", "amount_total": 1}},
    }
    assert await send(pg, stripe_events["event"]) == {"ok": True}
    assert await purchase_row(pg, "cs_other") is None
    assert await get_balance(pg) == 0


async def test_apply_paid_checkout_credits_once(pg, user):
    """The webhook's credit path, shared with account deletion (which uses it
    for a paid checkout whose webhook never arrived)."""
    session = completed_event()["data"]["object"]
    assert await service.apply_paid_checkout(pg, session) == 500
    assert await service.apply_paid_checkout(pg, session) is None
    assert await get_balance(pg) == 500
    assert (await purchase_row(pg, "cs_1"))[0] == "COMPLETED"
    unpaid = completed_event(session_id="cs_2", payment_status="unpaid")
    assert await service.apply_paid_checkout(pg, unpaid["data"]["object"]) is None
    assert await purchase_row(pg, "cs_2") is None


async def test_unpaid_completed_stays_pending(pg, user, stripe_events):
    """Async payment methods complete checkout with payment_status='unpaid' —
    crediting there would pay out on a payment that can still fail."""
    stripe_events["event"] = completed_event(payment_status="unpaid")
    assert await send(pg, stripe_events["event"]) == {"ok": True}
    assert await purchase_row(pg, "cs_1") is None
    assert await get_balance(pg) == 0


async def test_async_payment_succeeded_credits(pg, user, stripe_events):
    stripe_events["event"] = completed_event(payment_status="unpaid")
    await send(pg, stripe_events["event"])
    stripe_events["event"] = async_succeeded_event()
    await send(pg, stripe_events["event"])
    row = await purchase_row(pg, "cs_1")
    assert row[0] == "COMPLETED"
    assert row[1] == "pi_1"
    assert await get_balance(pg) == 500


async def test_full_refund_claws_back_credit(pg, user, stripe_events):
    stripe_events["event"] = completed_event()
    await send(pg, stripe_events["event"])
    assert await get_balance(pg) == 500

    stripe_events["event"] = charge_refunded_event()
    await send(pg, stripe_events["event"])
    row = await purchase_row(pg, "cs_1")
    assert row[0] == "REFUNDED"
    assert await get_balance(pg) == 0

    # Redelivery must not claw back twice (floor at 0 anyway).
    await send(pg, stripe_events["event"])
    assert await get_balance(pg) == 0


async def test_partial_refund_keeps_credit(pg, user, stripe_events):
    stripe_events["event"] = completed_event()
    await send(pg, stripe_events["event"])
    stripe_events["event"] = charge_refunded_event(amount_refunded=100)
    await send(pg, stripe_events["event"])
    row = await purchase_row(pg, "cs_1")
    assert row[0] == "COMPLETED"
    assert await get_balance(pg) == 500


async def test_refund_floors_at_zero(pg, user, stripe_events):
    """Credit already spent can't be clawed back below zero."""
    stripe_events["event"] = completed_event()
    await send(pg, stripe_events["event"])
    await pg.execute(
        'UPDATE "user" SET balance_cents = 200 WHERE auth0_id = %s', ("u1",)
    )
    stripe_events["event"] = charge_refunded_event()
    await send(pg, stripe_events["event"])
    assert await get_balance(pg) == 0


async def test_require_balance(pg, user):
    with pytest.raises(HTTPException) as exc:
        await require_balance(pg, "u1")
    assert exc.value.status_code == 402

    with pytest.raises(HTTPException):
        await require_balance(pg, "nobody")

    await pg.execute(
        'UPDATE "user" SET balance_cents = 0.5 WHERE auth0_id = %s', ("u1",)
    )
    assert await require_balance(pg, "u1") == 0.5


async def test_list_models_action_costs_assembly():
    """Mapping check that runs without Postgres — the SQL itself is covered
    by test_list_models_includes_action_costs when TEST_PG_URL is set."""
    pg = _Pg(
        [
            [
                ("openrouter:a", "A", 0.1, 0.5, True),
                ("openrouter:b", "B", 0.2, 0.6, False),
            ],
            [
                ("openrouter:a", "TAILOR", 3.5),
                ("openrouter:a", "SUGGESTION", 1.0),
            ],
        ]
    )
    resp = await service.list_models(pg)
    a, b = resp.models
    assert a.action_costs == [
        model.ActionCostEstimate(job_kind="TAILOR", avg_cents=3.5),
        model.ActionCostEstimate(job_kind="SUGGESTION", avg_cents=1.0),
    ]
    assert b.action_costs == []


async def test_list_models_includes_action_costs(pg, user):
    await pg.execute(
        """
        INSERT INTO model_pricing
          (id, display_name, cents_per_1k_input, cents_per_1k_output,
           enabled, is_default, sort_order)
        VALUES ('openrouter:a', 'A', 0.10, 0.50, true, true, 0),
               ('openrouter:b', 'B', 0.20, 0.60, true, false, 1),
               ('openrouter:off', 'Off', 0.10, 0.10, false, false, 2)
        """
    )
    await pg.execute(
        """
        INSERT INTO token_usage
          (user_id, job_kind, job_id, model, input_tokens, output_tokens,
           amount_cents, created_at)
        VALUES
          ('u1', 'TAILOR', 't1', 'openrouter:a', 100, 50, 2.0, now()),
          -- one run billed over two turns: counts as a single 4.0¢ action
          ('u1', 'TAILOR', 't2:turn1', 'openrouter:a', 100, 50, 1.5, now()),
          ('u1', 'TAILOR', 't2:turn2', 'openrouter:a', 100, 50, 2.5, now()),
          ('u1', 'SUGGESTION', 's1', 'openrouter:a', 100, 50, 1.0, now()),
          -- outside the 90-day window: stale prices don't skew the estimate
          ('u1', 'SUGGESTION', 's0', 'openrouter:a', 100, 50, 50.0,
           now() - interval '120 days'),
          ('u1', 'TAILOR', 't3', 'openrouter:off', 100, 50, 9.0, now())
        """
    )
    resp = await service.list_models(pg)
    by_id = {m.id: m for m in resp.models}
    # Disabled models stay hidden even though they have usage history.
    assert "openrouter:off" not in by_id
    costs = {c.job_kind: c for c in by_id["openrouter:a"].action_costs}
    assert costs["TAILOR"].avg_cents == 3.0
    assert costs["SUGGESTION"].avg_cents == 1.0
    # No usage history → no estimates.
    assert by_id["openrouter:b"].action_costs == []


async def test_validate_model_choice(pg):
    await pg.execute(
        """
        INSERT INTO model_pricing
          (id, display_name, cents_per_1k_input, cents_per_1k_output, enabled)
        VALUES ('openrouter:m', 'M', 0.16, 1.25, true),
               ('openrouter:off', 'Off', 0.16, 1.25, false)
        """
    )
    assert await validate_model_choice(pg, "openrouter:m") == "openrouter:m"
    assert await validate_model_choice(pg, None) is None
    for bad in ("openrouter:off", "openrouter:nope"):
        with pytest.raises(HTTPException) as exc:
            await validate_model_choice(pg, bad)
        assert exc.value.status_code == 400


async def test_create_checkout(pg, user, monkeypatch):
    customer_calls = []
    session_calls = []
    monkeypatch.setattr(
        stripe.Customer,
        "create",
        lambda **kwargs: (
            customer_calls.append(kwargs) or SimpleNamespace(id="cus_1")
        ),
    )
    monkeypatch.setattr(
        stripe.checkout.Session,
        "create",
        lambda **kwargs: (
            session_calls.append(kwargs)
            or SimpleNamespace(
                id=f"cs_{len(session_calls)}", url="https://checkout.test/pay"
            )
        ),
    )

    res = await service.create_checkout(
        pg_conn=pg, user_id="u1", req=model.CheckoutRequest(pack_id="starter")
    )
    assert res.url == "https://checkout.test/pay"
    assert customer_calls == [{"metadata": {"auth0_id": "u1"}}]

    row = await purchase_row(pg, "cs_1")
    assert row is not None and row[0] == "PENDING"

    # Second checkout reuses the stored customer — no second Customer.create.
    await service.create_checkout(
        pg_conn=pg, user_id="u1", req=model.CheckoutRequest(pack_id="pro")
    )
    assert len(customer_calls) == 1


async def test_checkout_unknown_pack(pg, user):
    with pytest.raises(HTTPException) as exc:
        await service.create_checkout(
            pg_conn=pg,
            user_id="u1",
            req=model.CheckoutRequest(pack_id="nope"),
        )
    assert exc.value.status_code == 400


async def test_checkout_missing_user(pg):
    with pytest.raises(HTTPException) as exc:
        await service.create_checkout(
            pg_conn=pg,
            user_id="ghost",
            req=model.CheckoutRequest(pack_id="starter"),
        )
    assert exc.value.status_code == 404


async def test_stripe_unconfigured(pg, user, monkeypatch):
    monkeypatch.setattr(service, "STRIPE_SECRET_KEY", "")
    with pytest.raises(HTTPException) as exc:
        await service.create_checkout(
            pg_conn=pg,
            user_id="u1",
            req=model.CheckoutRequest(pack_id="starter"),
        )
    assert exc.value.status_code == 503

import asyncio

import stripe
from fastapi import HTTPException

from .. import site_settings
from ..deps import PgConnection
from ..env_vars import FRONTEND_BASE_URL, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from . import model
from .model import TOKEN_PACKS


def _require_stripe() -> None:
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe is not configured")
    stripe.api_key = STRIPE_SECRET_KEY


async def get_balance(pg_conn: PgConnection, user_id: str) -> model.BalanceResponse:
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            'SELECT balance_cents FROM "user" WHERE auth0_id = %s', (user_id,)
        )
        row = await res.fetchone()
    return model.BalanceResponse(balance_cents=float(row[0]) if row else 0.0)


async def list_models(pg_conn: PgConnection) -> model.ModelsResponse:
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            SELECT id, display_name, cents_per_1k_input, cents_per_1k_output,
                   is_default
            FROM model_pricing WHERE enabled ORDER BY sort_order
            """
        )
        rows = await res.fetchall()
    return model.ModelsResponse(
        models=[
            model.ModelInfo(
                id=r[0],
                display_name=r[1],
                cents_per_1k_input=float(r[2]),
                cents_per_1k_output=float(r[3]),
                is_default=r[4],
            )
            for r in rows
        ]
    )


async def list_purchases(
    pg_conn: PgConnection, user_id: str
) -> model.PurchasesResponse:
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            SELECT id, cents, amount_cents, currency, status, created_at
            FROM balance_purchase WHERE user_id = %s ORDER BY created_at DESC
            """,
            (user_id,),
        )
        rows = await res.fetchall()
    return model.PurchasesResponse(
        purchases=[
            model.PurchaseItem(
                id=r[0],
                cents=r[1],
                amount_cents=r[2],
                currency=r[3],
                status=r[4],
                created_at=r[5].isoformat(),
            )
            for r in rows
        ]
    )


async def create_checkout(
    pg_conn: PgConnection, user_id: str, req: model.CheckoutRequest
) -> model.CheckoutResponse:
    _require_stripe()
    if await site_settings.payments_paused(pg_conn):
        # 403 (not 503) so the web client's error mapping surfaces this detail.
        raise HTTPException(
            status_code=403,
            detail="Purchases are temporarily paused — please try again later.",
        )
    pack = TOKEN_PACKS.get(req.pack_id)
    if not pack:
        raise HTTPException(status_code=400, detail="Unknown pack")

    # FOR UPDATE serializes concurrent checkouts for this user: the second
    # waits on the row lock, then sees the customer the first just created.
    async with pg_conn.transaction(), pg_conn.cursor() as cursor:
        res = await cursor.execute(
            'SELECT stripe_customer_id FROM "user" WHERE auth0_id = %s FOR UPDATE',
            (user_id,),
        )
        row = await res.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        customer_id = row[0]

        if not customer_id:
            customer = await asyncio.to_thread(
                stripe.Customer.create,
                metadata={"auth0_id": user_id},
            )
            customer_id = customer.id
            await cursor.execute(
                'UPDATE "user" SET stripe_customer_id = %s WHERE auth0_id = %s',
                (customer_id, user_id),
            )

    session = await asyncio.to_thread(
        stripe.checkout.Session.create,
        mode="payment",
        customer=customer_id,
        client_reference_id=user_id,
        line_items=[
            {
                "price_data": {
                    "currency": pack.currency,
                    "unit_amount": pack.amount_cents,
                    "product_data": {"name": pack.name},
                },
                "quantity": 1,
            }
        ],
        metadata={"pack_id": pack.id, "cents": str(pack.cents)},
        success_url=f"{FRONTEND_BASE_URL}/billing?checkout=success",
        cancel_url=f"{FRONTEND_BASE_URL}/billing?checkout=cancelled",
    )

    # The webhook flips this to COMPLETED and tops up the balance; the
    # session id is the purchase's PK so a redelivered webhook can't
    # double-credit.
    async with pg_conn.transaction(), pg_conn.cursor() as cursor:
        await cursor.execute(
            """
            INSERT INTO balance_purchase
              (id, user_id, cents, amount_cents, currency, status)
            VALUES (%s, %s, %s, %s, %s, 'PENDING')
            ON CONFLICT (id) DO NOTHING
            """,
            (
                session.id,
                user_id,
                pack.cents,
                pack.amount_cents,
                pack.currency,
            ),
        )

    assert session.url
    return model.CheckoutResponse(url=session.url)


async def handle_webhook(
    pg_conn: PgConnection, payload: bytes, sig_header: str | None
) -> dict:
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe is not configured")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header or "", STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signature") from None

    event_type = event["type"]
    obj = event["data"]["object"]
    # stripe-python v15 objects aren't dicts — .get() doesn't exist on them.
    # to_dict() so field access works for real events and the plain-dict
    # events tests stub in alike.
    if not isinstance(obj, dict):
        obj = obj.to_dict()

    if event_type in (
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    ):
        session = obj
        if session.get("payment_status") == "unpaid":
            # Async payment still in flight — the purchase stays PENDING until
            # checkout.session.async_payment_succeeded lands.
            return {"ok": True}
        purchaser_id = session.get("client_reference_id")
        cents = (session.get("metadata") or {}).get("cents")
        if not purchaser_id or not cents:
            # Not one of our token-pack sessions — acknowledge and move on.
            return {"ok": True}
        payment_intent = session.get("payment_intent")
        async with pg_conn.transaction(), pg_conn.cursor() as cursor:
            # Stripe may deliver the event before the checkout endpoint's
            # INSERT commits — upsert from the session payload first.
            await cursor.execute(
                """
                INSERT INTO balance_purchase
                  (id, user_id, cents, amount_cents, currency, status,
                   payment_intent_id)
                VALUES (%s, %s, %s, %s, %s, 'PENDING', %s)
                ON CONFLICT (id) DO UPDATE SET
                  payment_intent_id = COALESCE(
                    balance_purchase.payment_intent_id,
                    EXCLUDED.payment_intent_id
                  )
                """,
                (
                    session["id"],
                    purchaser_id,
                    int(cents),
                    session["amount_total"],
                    session["currency"],
                    payment_intent,
                ),
            )
            # Only a PENDING row transitions — a redelivered event is a no-op.
            res = await cursor.execute(
                """
                UPDATE balance_purchase SET status = 'COMPLETED'
                WHERE id = %s AND status = 'PENDING'
                RETURNING user_id, cents
                """,
                (session["id"],),
            )
            purchase = await res.fetchone()
            if purchase:
                await cursor.execute(
                    """
                    UPDATE "user"
                    SET balance_cents = balance_cents + %s
                    WHERE auth0_id = %s
                    """,
                    (purchase[1], purchase[0]),
                )
    elif event_type == "checkout.session.expired":
        async with pg_conn.transaction(), pg_conn.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE balance_purchase SET status = 'EXPIRED'
                WHERE id = %s AND status = 'PENDING'
                """,
                (obj["id"],),
            )
    elif event_type == "charge.refunded":
        charge = obj
        payment_intent = charge.get("payment_intent")
        # Only a full refund claws the credit back — a partial refund leaves
        # the purchase COMPLETED.
        if (
            payment_intent
            and charge.get("amount_refunded") == charge.get("amount")
        ):
            async with pg_conn.transaction(), pg_conn.cursor() as cursor:
                # COMPLETED → REFUNDED transition is the idempotency guard:
                # a redelivered event is a no-op.
                res = await cursor.execute(
                    """
                    UPDATE balance_purchase SET status = 'REFUNDED'
                    WHERE payment_intent_id = %s AND status = 'COMPLETED'
                    RETURNING user_id, cents
                    """,
                    (payment_intent,),
                )
                purchase = await res.fetchone()
                if purchase:
                    await cursor.execute(
                        """
                        UPDATE "user"
                        SET balance_cents = GREATEST(0, balance_cents - %s)
                        WHERE auth0_id = %s
                        """,
                        (purchase[1], purchase[0]),
                    )

    return {"ok": True}

from fastapi import HTTPException

from ..deps import PgConnection
from . import model


async def list_users(pg_conn: PgConnection) -> model.AdminUsersResponse:
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            SELECT
                u.auth0_id, u.email, u.full_name, u.balance_cents,
                COALESCE(uu.cents_used, 0) AS cents_used,
                COALESCE(uu.input_tokens, 0) AS input_tokens,
                COALESCE(uu.output_tokens, 0) AS output_tokens,
                COALESCE(p.cents_purchased, 0) AS cents_purchased
            FROM "user" u
            LEFT JOIN (
                SELECT user_id, SUM(amount_cents) AS cents_used,
                       SUM(input_tokens) AS input_tokens,
                       SUM(output_tokens) AS output_tokens
                FROM token_usage GROUP BY user_id
            ) uu ON uu.user_id = u.auth0_id
            LEFT JOIN (
                SELECT user_id, SUM(cents) AS cents_purchased
                FROM balance_purchase WHERE status = 'COMPLETED'
                GROUP BY user_id
            ) p ON p.user_id = u.auth0_id
            ORDER BY cents_used DESC
            """
        )
        rows = await res.fetchall()
    return model.AdminUsersResponse(
        users=[
            model.AdminUserRow(
                auth0_id=r[0],
                email=r[1],
                full_name=r[2],
                balance_cents=float(r[3]),
                cents_used=float(r[4]),
                input_tokens=r[5],
                output_tokens=r[6],
                cents_purchased=r[7],
            )
            for r in rows
        ]
    )


async def get_usage(pg_conn: PgConnection) -> model.AdminUsageResponse:
    async with pg_conn.cursor() as cursor:
        by_model = await (
            await cursor.execute(
                """
                SELECT model, COUNT(*), SUM(input_tokens), SUM(output_tokens),
                       SUM(amount_cents)
                FROM token_usage GROUP BY model ORDER BY SUM(amount_cents) DESC
                """
            )
        ).fetchall()

        by_kind = await (
            await cursor.execute(
                """
                SELECT job_kind, COUNT(*), SUM(amount_cents)
                FROM token_usage GROUP BY job_kind ORDER BY SUM(amount_cents) DESC
                """
            )
        ).fetchall()

        by_day = await (
            await cursor.execute(
                """
                SELECT created_at::date AS day, SUM(amount_cents)
                FROM token_usage
                WHERE created_at > now() - interval '30 days'
                GROUP BY day ORDER BY day
                """
            )
        ).fetchall()

        recent = await (
            await cursor.execute(
                """
                SELECT id, user_id, job_kind, job_id, model, input_tokens,
                       output_tokens, amount_cents, actual_cost_cents, created_at
                FROM token_usage ORDER BY created_at DESC LIMIT 50
                """
            )
        ).fetchall()

    return model.AdminUsageResponse(
        by_model=[
            model.UsageByModelRow(
                model=r[0],
                job_count=r[1],
                input_tokens=r[2],
                output_tokens=r[3],
                cents=float(r[4]),
            )
            for r in by_model
        ],
        by_kind=[
            model.UsageByKindRow(job_kind=r[0], job_count=r[1], cents=float(r[2]))
            for r in by_kind
        ],
        by_day=[
            model.UsageByDayRow(day=r[0].isoformat(), cents=float(r[1])) for r in by_day
        ],
        recent=[
            model.RecentUsageRow(
                id=r[0],
                user_id=r[1],
                job_kind=r[2],
                job_id=r[3],
                model=r[4],
                input_tokens=r[5],
                output_tokens=r[6],
                amount_cents=float(r[7]),
                actual_cost_cents=(float(r[8]) if r[8] is not None else None),
                created_at=r[9].isoformat(),
            )
            for r in recent
        ],
    )


async def list_purchases(pg_conn: PgConnection) -> model.AdminPurchasesResponse:
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            SELECT id, user_id, cents, amount_cents, currency, status, created_at
            FROM balance_purchase ORDER BY created_at DESC LIMIT 200
            """
        )
        rows = await res.fetchall()

        rev = await cursor.execute(
            """
            SELECT COALESCE(SUM(amount_cents), 0) FROM balance_purchase
            WHERE status = 'COMPLETED'
            """
        )
        revenue = (await rev.fetchone())[0]

    return model.AdminPurchasesResponse(
        revenue_cents=revenue,
        purchases=[
            model.AdminPurchaseRow(
                id=r[0],
                user_id=r[1],
                cents=r[2],
                amount_cents=r[3],
                currency=r[4],
                status=r[5],
                created_at=r[6].isoformat(),
            )
            for r in rows
        ],
    )


async def list_models(pg_conn: PgConnection) -> model.AdminModelsResponse:
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            SELECT id, display_name, cents_per_1k_input, cents_per_1k_output,
                   enabled, is_default, sort_order
            FROM model_pricing ORDER BY sort_order, id
            """
        )
        rows = await res.fetchall()
    return model.AdminModelsResponse(
        models=[
            model.ModelPricingRow(
                id=r[0],
                display_name=r[1],
                cents_per_1k_input=float(r[2]),
                cents_per_1k_output=float(r[3]),
                enabled=r[4],
                is_default=r[5],
                sort_order=r[6],
            )
            for r in rows
        ]
    )


async def upsert_model(
    pg_conn: PgConnection, model_id: str, body: model.ModelPricingUpsert
) -> model.ModelPricingRow:
    if not model_id.startswith("openrouter:"):
        raise HTTPException(
            status_code=400,
            detail="Model id must be an openrouter: spec — only OpenRouter "
            "models are reachable with the current provider setup.",
        )
    if body.cents_per_1k_input < 0 or body.cents_per_1k_output < 0:
        raise HTTPException(status_code=400, detail="Rates can't be negative")
    if body.is_default and not body.enabled:
        raise HTTPException(status_code=400, detail="The default model must be enabled")
    async with pg_conn.cursor() as cursor:
        # Single-winner flag — clear the rest in the same txn.
        if body.is_default:
            await cursor.execute("UPDATE model_pricing SET is_default = false")
        await cursor.execute(
            """
            INSERT INTO model_pricing
              (id, display_name, cents_per_1k_input, cents_per_1k_output,
               enabled, is_default, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
              display_name = EXCLUDED.display_name,
              cents_per_1k_input = EXCLUDED.cents_per_1k_input,
              cents_per_1k_output = EXCLUDED.cents_per_1k_output,
              enabled = EXCLUDED.enabled,
              is_default = EXCLUDED.is_default,
              sort_order = EXCLUDED.sort_order
            """,
            (
                model_id,
                body.display_name,
                body.cents_per_1k_input,
                body.cents_per_1k_output,
                body.enabled,
                body.is_default,
                body.sort_order,
            ),
        )
    return model.ModelPricingRow(id=model_id, **body.model_dump())


async def delete_model(pg_conn: PgConnection, model_id: str):
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            "DELETE FROM model_pricing WHERE id = %s", (model_id,)
        )
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Model not found")

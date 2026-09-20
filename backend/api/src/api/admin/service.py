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
                       output_tokens, amount_cents, created_at
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
            model.UsageByKindRow(
                job_kind=r[0], job_count=r[1], cents=float(r[2])
            )
            for r in by_kind
        ],
        by_day=[
            model.UsageByDayRow(day=r[0].isoformat(), cents=float(r[1]))
            for r in by_day
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
                created_at=r[8].isoformat(),
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

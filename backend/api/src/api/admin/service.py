from ..deps import PgConnection
from . import model


async def list_users(pg_conn: PgConnection) -> model.AdminUsersResponse:
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            SELECT
                u.auth0_id, u.email, u.full_name, u.token_balance,
                COALESCE(uu.credits_used, 0) AS credits_used,
                COALESCE(uu.input_tokens, 0) AS input_tokens,
                COALESCE(uu.output_tokens, 0) AS output_tokens,
                COALESCE(p.credits_purchased, 0) AS credits_purchased
            FROM "user" u
            LEFT JOIN (
                SELECT user_id, SUM(credits_charged) AS credits_used,
                       SUM(input_tokens) AS input_tokens,
                       SUM(output_tokens) AS output_tokens
                FROM token_usage GROUP BY user_id
            ) uu ON uu.user_id = u.auth0_id
            LEFT JOIN (
                SELECT user_id, SUM(credits) AS credits_purchased
                FROM token_purchase WHERE status = 'COMPLETED'
                GROUP BY user_id
            ) p ON p.user_id = u.auth0_id
            ORDER BY credits_used DESC
            """
        )
        rows = await res.fetchall()
    return model.AdminUsersResponse(
        users=[
            model.AdminUserRow(
                auth0_id=r[0],
                email=r[1],
                full_name=r[2],
                token_balance=r[3],
                credits_used=r[4],
                input_tokens=r[5],
                output_tokens=r[6],
                credits_purchased=r[7],
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
                       SUM(credits_charged)
                FROM token_usage GROUP BY model ORDER BY SUM(credits_charged) DESC
                """
            )
        ).fetchall()

        by_kind = await (
            await cursor.execute(
                """
                SELECT job_kind, COUNT(*), SUM(credits_charged)
                FROM token_usage GROUP BY job_kind ORDER BY SUM(credits_charged) DESC
                """
            )
        ).fetchall()

        by_day = await (
            await cursor.execute(
                """
                SELECT created_at::date AS day, SUM(credits_charged)
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
                       output_tokens, credits_charged, created_at
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
                credits=r[4],
            )
            for r in by_model
        ],
        by_kind=[
            model.UsageByKindRow(job_kind=r[0], job_count=r[1], credits=r[2])
            for r in by_kind
        ],
        by_day=[
            model.UsageByDayRow(day=r[0].isoformat(), credits=r[1])
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
                credits_charged=r[7],
                created_at=r[8].isoformat(),
            )
            for r in recent
        ],
    )


async def list_purchases(pg_conn: PgConnection) -> model.AdminPurchasesResponse:
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            SELECT id, user_id, credits, amount_cents, currency, status, created_at
            FROM token_purchase ORDER BY created_at DESC LIMIT 200
            """
        )
        rows = await res.fetchall()

        rev = await cursor.execute(
            """
            SELECT COALESCE(SUM(amount_cents), 0) FROM token_purchase
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
                credits=r[2],
                amount_cents=r[3],
                currency=r[4],
                status=r[5],
                created_at=r[6].isoformat(),
            )
            for r in rows
        ],
    )

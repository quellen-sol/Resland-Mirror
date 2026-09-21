from fastapi import HTTPException

from .deps import PgConnection


async def require_balance(pg_conn: PgConnection, user_id: str) -> float:
    """Gate for starting a paid job. Running jobs are never interrupted —
    the dispatcher deducts what they burn, flooring the balance at 0."""
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            'SELECT balance_cents FROM "user" WHERE auth0_id = %s',
            (user_id,),
        )
        row = await res.fetchone()
    balance = float(row[0]) if row else 0.0
    if balance <= 0:
        raise HTTPException(
            status_code=402,
            detail="insufficient_balance",
        )
    return balance


async def validate_model_choice(pg_conn: PgConnection, model: str | None) -> str | None:
    """A user-selected model must be an enabled row in model_pricing —
    never let a free-form model spec reach init_chat_model."""
    if model is None:
        return None
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            "SELECT 1 FROM model_pricing WHERE id = %s AND enabled",
            (model,),
        )
        ok = await res.fetchone()
    if not ok:
        raise HTTPException(status_code=400, detail="Unknown model")
    return model

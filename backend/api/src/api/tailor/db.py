from dataclasses import dataclass
from datetime import datetime

from psycopg.rows import class_row
from shared.checkpoints import CHECKPOINT_TABLES

from ..deps import PgConnection


@dataclass
class UserTailorRunRow:
    id: str
    user_id: str
    job_description: str
    company_name: str | None
    role: str | None
    model: str | None
    pending_question: str | None
    result: str | None
    status: str
    created_at: datetime


async def create_tailor_run(
    conn: PgConnection,
    run_id: str,
    user_id: str,
    job_description: str,
    company_name: str | None,
    role: str | None,
    model: str | None,
) -> str:
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            INSERT INTO user_tailor_run
                (id, user_id, job_description, company_name, role, model)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (run_id, user_id, job_description, company_name, role, model),
        )
    return run_id


async def get_tailor_run(
    pg_conn: PgConnection, user_id: str, run_id: str
) -> UserTailorRunRow | None:
    async with pg_conn.cursor(row_factory=class_row(UserTailorRunRow)) as cursor:
        res = await cursor.execute(
            """
            SELECT * FROM user_tailor_run WHERE id = %s AND user_id = %s
            """,
            (run_id, user_id),
        )

        row = await res.fetchone()

    return row


async def get_outstanding_tailor_run(
    pg_conn: PgConnection, user_id: str
) -> UserTailorRunRow | None:
    """The user's latest unresolved run — anything short of COMPLETED still
    counts as outstanding, including FAILED (the user decides its fate)."""
    async with pg_conn.cursor(row_factory=class_row(UserTailorRunRow)) as cursor:
        res = await cursor.execute(
            """
            SELECT * FROM user_tailor_run
            WHERE user_id = %s AND status <> 'COMPLETED'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        )
        return await res.fetchone()


async def update_tailor_run(
    conn: PgConnection,
    run_id: str,
    *,
    status: str,
    pending_question: str | None,
) -> None:
    # `result` is intentionally untouched — a feedback answer resumes a run
    # that already has a submitted resume, and it stays visible during the
    # refinement pass.
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            UPDATE user_tailor_run
            SET status = %s, pending_question = %s
            WHERE id = %s
            """,
            (status, pending_question, run_id),
        )


async def clear_completed_tailor_runs(conn: PgConnection, user_id: str) -> None:
    """Drop resolved (COMPLETED) runs plus their checkpoints once a new run
    starts — anything worth keeping was snapshotted on save."""
    async with conn.cursor() as cursor:
        res = await cursor.execute(
            """
            DELETE FROM user_tailor_run
            WHERE user_id = %s AND status = 'COMPLETED'
            RETURNING id
            """,
            (user_id,),
        )
        run_ids = [row[0] for row in await res.fetchall()]
        for run_id in run_ids:
            for table in CHECKPOINT_TABLES:
                await cursor.execute(
                    f"DELETE FROM {table} WHERE thread_id = %s",
                    (run_id,),
                )


async def delete_tailor_run(conn: PgConnection, run_id: str, user_id: str) -> None:
    async with conn.cursor() as cursor:
        res = await cursor.execute(
            "DELETE FROM user_tailor_run WHERE id = %s AND user_id = %s RETURNING id",
            (run_id, user_id),
        )
        # Someone else's run (or none): its thread isn't the caller's to drop.
        if not await res.fetchall():
            return
        # The dispatcher's langgraph checkpointer keys conversation state on
        # thread_id = run_id — drop it with the run.
        for table in CHECKPOINT_TABLES:
            await cursor.execute(
                f"DELETE FROM {table} WHERE thread_id = %s",
                (run_id,),
            )

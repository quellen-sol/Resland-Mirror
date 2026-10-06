from dataclasses import dataclass
from datetime import datetime

from psycopg.rows import class_row
from shared.checkpoints import CHECKPOINT_TABLES

from ..deps import PgConnection


@dataclass
class UserSuggestionRow:
    id: str
    user_id: str
    experience_id: int
    bullet_id: int | None
    model: str | None
    pending_question: str | None
    result: str | None
    status: str
    created_at: datetime


async def create_sugg_session(
    conn: PgConnection,
    session_id: str,
    user_id: str,
    experience_id: int,
    bullet_id: int | None,
    model: str | None,
) -> str:
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            INSERT INTO user_suggestion
              (id, user_id, experience_id, bullet_id, model)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (session_id, user_id, experience_id, bullet_id, model),
        )
    return session_id


async def get_sugg_session(
    pg_conn: PgConnection, user_id: str, session_id: str
) -> UserSuggestionRow | None:
    async with pg_conn.cursor(row_factory=class_row(UserSuggestionRow)) as cursor:
        res = await cursor.execute(
            """
            SELECT * FROM user_suggestion WHERE id = %s AND user_id = %s
            """,
            (session_id, user_id),
        )

        row = await res.fetchone()

    return row


async def update_sugg_session(
    conn: PgConnection,
    session_id: str,
    *,
    status: str,
    pending_question: str | None,
    result: str | None,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            UPDATE user_suggestion
            SET status = %s, pending_question = %s, result = %s
            WHERE id = %s
            """,
            (status, pending_question, result, session_id),
        )


async def delete_inactive_sugg_sessions(
    conn: PgConnection, user_id: str, experience_id: int, bullet_id: int | None
) -> None:
    """Drop non-active sessions for the same target before a fresh insert.

    user_suggestion is unique on (user_id, experience_id, bullet_id), so a
    leftover FAILED row would make a retrying start hit a unique violation.
    Checkpoint rows go too — they are keyed on the doomed session ids."""
    async with conn.cursor() as cursor:
        res = await cursor.execute(
            """
            DELETE FROM user_suggestion
            WHERE user_id = %s AND experience_id = %s
              AND bullet_id IS NOT DISTINCT FROM %s
              AND status NOT IN ('PROCESSING', 'WAITING_FOR_INPUT', 'COMPLETED')
            RETURNING id
            """,
            (user_id, experience_id, bullet_id),
        )
        ids = [row[0] for row in await res.fetchall()]
        for session_id in ids:
            for table in CHECKPOINT_TABLES:
                await cursor.execute(
                    f"DELETE FROM {table} WHERE thread_id = %s",
                    (session_id,),
                )


async def delete_sugg_session(
    conn: PgConnection, session_id: str, user_id: str
) -> None:
    async with conn.cursor() as cursor:
        res = await cursor.execute(
            "DELETE FROM user_suggestion WHERE id = %s AND user_id = %s RETURNING id",
            (session_id, user_id),
        )
        # Someone else's session (or none): its thread isn't the caller's.
        if not await res.fetchall():
            return
        # The dispatcher's langgraph checkpointer keys conversation state on
        # thread_id = session_id — drop it with the session.
        for table in CHECKPOINT_TABLES:
            await cursor.execute(
                f"DELETE FROM {table} WHERE thread_id = %s",
                (session_id,),
            )

from dataclasses import dataclass
from datetime import datetime

from psycopg.rows import class_row

from ..deps import PgConnection


@dataclass
class UserSuggestionRow:
    id: str
    user_id: str
    experience_id: int
    bullet_id: int | None
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
) -> str:
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            INSERT INTO user_suggestion (id, user_id, experience_id, bullet_id)
            VALUES (%s, %s, %s, %s)
            """,
            (session_id, user_id, experience_id, bullet_id),
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


async def delete_sugg_session(
    conn: PgConnection, session_id: str, user_id: str
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            "DELETE FROM user_suggestion WHERE id = %s AND user_id = %s",
            (session_id, user_id),
        )
        # The dispatcher's langgraph checkpointer keys conversation state on
        # thread_id = session_id — drop it with the session.
        for table in ("checkpoints", "checkpoint_blobs", "checkpoint_writes"):
            await cursor.execute(
                f"DELETE FROM {table} WHERE thread_id = %s",
                (session_id,),
            )

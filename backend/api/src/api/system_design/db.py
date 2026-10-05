from dataclasses import dataclass
from datetime import datetime

from psycopg.rows import class_row
from shared.checkpoints import CHECKPOINT_TABLES

from ..deps import PgConnection


@dataclass
class SessionRow:
    id: str
    user_id: str
    source: str
    problem_id: str | None
    tailored_resume_id: str | None
    company_name: str | None
    role: str | None
    job_description: str | None
    level: str
    model: str | None
    status: str
    phase: str
    title: str | None
    prompt: str | None
    brief: str | None
    requirements: str
    estimates: str
    diagram: str
    agent_context: str | None
    last_turn_id: str | None
    notice: str | None
    phase_durations: str
    phase_started_at: datetime
    result: str | None
    letter_grade: str | None
    hire_signal: str | None
    created_at: datetime
    completed_at: datetime | None


@dataclass
class MessageRow:
    id: int
    session_id: str
    role: str
    phase: str
    content: str
    created_at: datetime


@dataclass
class TailoredPosting:
    company_name: str | None
    role: str | None
    job_description: str


async def create_session(
    conn: PgConnection,
    *,
    session_id: str,
    user_id: str,
    source: str,
    problem_id: str | None,
    tailored_resume_id: str | None,
    company_name: str | None,
    role: str | None,
    job_description: str | None,
    level: str,
    model: str | None,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            INSERT INTO user_system_design_session
                (id, user_id, source, problem_id, tailored_resume_id,
                 company_name, role, job_description, level, model)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session_id,
                user_id,
                source,
                problem_id,
                tailored_resume_id,
                company_name,
                role,
                job_description,
                level,
                model,
            ),
        )


async def get_session(
    conn: PgConnection, user_id: str, session_id: str
) -> SessionRow | None:
    async with conn.cursor(row_factory=class_row(SessionRow)) as cursor:
        res = await cursor.execute(
            """
            SELECT * FROM user_system_design_session
            WHERE id = %s AND user_id = %s
            """,
            (session_id, user_id),
        )
        return await res.fetchone()


async def get_outstanding_session(
    conn: PgConnection, user_id: str
) -> SessionRow | None:
    """The user's latest unfinished interview — anything short of COMPLETED,
    including FAILED (the user decides its fate)."""
    async with conn.cursor(row_factory=class_row(SessionRow)) as cursor:
        res = await cursor.execute(
            """
            SELECT * FROM user_system_design_session
            WHERE user_id = %s AND status <> 'COMPLETED'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        )
        return await res.fetchone()


async def list_messages(conn: PgConnection, session_id: str) -> list[MessageRow]:
    async with conn.cursor(row_factory=class_row(MessageRow)) as cursor:
        res = await cursor.execute(
            """
            SELECT * FROM system_design_message
            WHERE session_id = %s ORDER BY id
            """,
            (session_id,),
        )
        return await res.fetchall()


async def add_candidate_message(
    conn: PgConnection, session_id: str, phase: str, content: str
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            INSERT INTO system_design_message (session_id, role, phase, content)
            VALUES (%s, 'CANDIDATE', %s, %s)
            """,
            (session_id, phase, content),
        )


async def save_workspace(
    conn: PgConnection,
    session_id: str,
    *,
    diagram: str | None,
    requirements: str | None,
    estimates: str | None,
) -> None:
    """Overwrite the given workspace fields; None leaves a field as stored."""
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            UPDATE user_system_design_session
            SET diagram = COALESCE(%s, diagram),
                requirements = COALESCE(%s, requirements),
                estimates = COALESCE(%s, estimates)
            WHERE id = %s
            """,
            (diagram, requirements, estimates, session_id),
        )


async def begin_turn(
    conn: PgConnection, session_id: str, *, next_phase: str | None
) -> None:
    """Hand the turn to the dispatcher. Moving to `next_phase` closes out the
    current phase's time in phase_durations."""
    async with conn.cursor() as cursor:
        if next_phase is None:
            await cursor.execute(
                """
                UPDATE user_system_design_session
                SET status = 'PROCESSING', notice = NULL
                WHERE id = %s
                """,
                (session_id,),
            )
            return
        await cursor.execute(
            """
            UPDATE user_system_design_session
            SET status = 'PROCESSING', notice = NULL,
                phase_durations = (phase_durations::jsonb || jsonb_build_object(
                    phase,
                    GREATEST(0, EXTRACT(EPOCH FROM now() - phase_started_at))::int
                ))::text,
                phase = %s,
                phase_started_at = now()
            WHERE id = %s
            """,
            (next_phase, session_id),
        )


async def get_tailored_posting(
    conn: PgConnection, user_id: str, tailored_id: str
) -> TailoredPosting | None:
    async with conn.cursor(row_factory=class_row(TailoredPosting)) as cursor:
        res = await cursor.execute(
            """
            SELECT company_name, role, job_description
            FROM user_tailored_resume WHERE id = %s AND user_id = %s
            """,
            (tailored_id, user_id),
        )
        return await res.fetchone()


async def practiced_problem_ids(conn: PgConnection, user_id: str) -> set[str]:
    """Bank problems the user has already started, for the random picker."""
    async with conn.cursor() as cursor:
        res = await cursor.execute(
            """
            SELECT DISTINCT problem_id FROM user_system_design_session
            WHERE user_id = %s AND problem_id IS NOT NULL
            """,
            (user_id,),
        )
        return {row[0] for row in await res.fetchall()}


async def delete_session(conn: PgConnection, session_id: str, user_id: str) -> None:
    async with conn.cursor() as cursor:
        res = await cursor.execute(
            "SELECT 1 FROM user_system_design_session WHERE id = %s AND user_id = %s",
            (session_id, user_id),
        )
        if not await res.fetchone():
            return
        await cursor.execute(
            "DELETE FROM system_design_message WHERE session_id = %s", (session_id,)
        )
        await cursor.execute(
            "DELETE FROM user_system_design_session WHERE id = %s", (session_id,)
        )
        # The dispatcher's langgraph checkpointer keys the interviewer thread on
        # thread_id = session id. The tables only exist once a dispatcher has run.
        for table in CHECKPOINT_TABLES:
            res = await cursor.execute("SELECT to_regclass(%s)", (table,))
            exists = await res.fetchone()
            if exists and exists[0]:
                await cursor.execute(
                    f"DELETE FROM {table} WHERE thread_id = %s", (session_id,)
                )

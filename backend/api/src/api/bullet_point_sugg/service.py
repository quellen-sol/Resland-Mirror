import uuid

from fastapi import HTTPException
from shared.pg import get_pg_client

from ..deps import PgConnection
from ..env_vars import PG_URL
from . import model
from .db import (
    create_sugg_session,
    delete_sugg_session,
    get_sugg_session,
    update_sugg_session,
)

# --- Stub state -------------------------------------------------------------
# Ephemeral lifecycle counters so the frontend exercises a realistic flow
# (PROCESSING -> WAITING_FOR_INPUT -> COMPLETED) until the dispatcher agent
# writes real status transitions. AMQP publish points are marked TODO.
_polls: dict[str, int] = {}
_answered: set[str] = set()

_STUB_QUESTION = (
    "What measurable impact did this work have (e.g. latency %, users, revenue)?"
)
_STUB_RESULT = (
    "Led migration of the billing service to event-driven "
    "processing, cutting p95 latency 40% for 2M monthly users."
)


async def start_suggestion(
    req: model.StartSuggestionRequest, user_id: str, pg_conn: PgConnection
) -> model.StartSuggestionResponse:
    async with pg_conn.cursor() as cursor:
        # Verify that an experience with this id exists for the user
        exp = await cursor.execute(
            'SELECT 1 FROM user_base_experience WHERE user_id = %s AND id = %s',
            (user_id, req.experience_id),
        )
        exp = await exp.fetchone()
        if not exp:
            raise HTTPException(status_code=404, detail="Experience not found")

        if req.bullet_id is not None:
            # Verify that a bullet (if provided) with this id exists for the user
            bullet = await cursor.execute(
                """
                SELECT 1 FROM user_base_experience_bullet
                WHERE id = %s AND user_experience_id = %s
                """,
                (req.bullet_id, req.experience_id),
            )
            bullet = await bullet.fetchone()
            if not bullet:
                raise HTTPException(status_code=404, detail="Bullet not found")

        # Check if there is an active suggestion for this experience/bullet
        active = await cursor.execute(
            """
            SELECT 1 FROM user_suggestion
            WHERE user_id = %s AND experience_id = %s
              AND bullet_id IS NOT DISTINCT FROM %s
              AND status IN ('PROCESSING', 'WAITING_FOR_INPUT')
            LIMIT 1
            """,
            (user_id, req.experience_id, req.bullet_id),
        )
        active = await active.fetchone()
        if active:
            raise HTTPException(
                status_code=409,
                detail="A suggestion is already in progress for this target",
            )

    # If all good, make the suggestion, then frontend will poll for status updates
    session_id = str(uuid.uuid4())
    await create_sugg_session(
        pg_conn,
        session_id=session_id,
        user_id=user_id,
        experience_id=req.experience_id,
        bullet_id=req.bullet_id,
    )
    return model.StartSuggestionResponse(id=session_id)


def get_suggestion(pg_conn: PgConnection, user_id: str, session_id: str) -> model.SuggestionStatusResponse:
    pass


async def answer_suggestion(
    user_id: str, req: model.AnswerRequest, pg_conn: PgConnection
) -> dict:
    session_id = req.session_id
    async with pg_conn.cursor() as cursor:
        session = get_sugg_session(cursor, session_id, user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Suggestion session not found")
        if session.status != "WAITING_FOR_INPUT":
            raise HTTPException(status_code=409, detail="Session is not awaiting input")

        # TODO: publish AmqpSuggestionJob(session_id=..., type="answer",
        # text=req.text) to resume the agent's checkpoint.
        _answered.add(session_id)
        _polls[session_id] = 0
        update_sugg_session(cursor, session_id, status="PROCESSING", pending_question=None)
        return {"ok": True}


def accept_suggestion(user_id: str, session_id: str) -> dict:
    pg_client = get_pg_client(PG_URL)
    try:
        session = get_sugg_session(pg_client, session_id, user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Suggestion session not found")
        # TODO: apply session.result — update user_base_experience_bullet.bullet
        # for BULLET targets; each {bulletId, text} for EXPERIENCE targets.
        delete_sugg_session(pg_client, session_id, user_id)
        _polls.pop(session_id, None)
        _answered.discard(session_id)
        return {"ok": True}
    finally:
        pg_client.close()


def dismiss_suggestion(user_id: str, session_id: str) -> dict:
    pg_client = get_pg_client(PG_URL)
    try:
        delete_sugg_session(pg_client, session_id, user_id)
        _polls.pop(session_id, None)
        _answered.discard(session_id)
        return {"ok": True}
    finally:
        pg_client.close()

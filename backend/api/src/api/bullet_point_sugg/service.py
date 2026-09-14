import uuid

from fastapi import HTTPException
from shared.amqp import BULLET_SUGG_EXCHANGE_NAME, AmqpSuggestionJob

from ..deps import AmqpClientDep, PgConnection
from . import db, model


async def start_suggestion(
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
    req: model.StartSuggestionRequest,
    user_id: str,
) -> model.StartSuggestionResponse:
    async with pg_conn.cursor() as cursor:
        # Verify that an experience with this id exists for the user
        exp = await cursor.execute(
            "SELECT 1 FROM user_base_experience WHERE user_id = %s AND id = %s",
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
    await db.create_sugg_session(
        pg_conn,
        session_id=session_id,
        user_id=user_id,
        experience_id=req.experience_id,
        bullet_id=req.bullet_id,
    )
    # The pooled connection only commits on dependency teardown (after the
    # response) — commit now so the dispatcher sees the row when it consumes
    # the job below.
    await pg_conn.commit()

    job = AmqpSuggestionJob(session_id=session_id)
    publisher = await amqp_client.get_publisher(BULLET_SUGG_EXCHANGE_NAME, "#")
    await publisher.publish(job.to_message())
    # Dispatch a job for the agent to begin parsing
    return model.StartSuggestionResponse(session_id=session_id)


async def get_suggestion_status(
    pg_conn: PgConnection, user_id: str, session_id: str
) -> model.SuggestionStatusResponse:
    res = await db.get_sugg_session(
        pg_conn=pg_conn, user_id=user_id, session_id=session_id
    )
    if not res:
        raise HTTPException(status_code=404, detail="Suggestion session not found")

    return model.SuggestionStatusResponse(
        status=res.status,
        pending_question=res.pending_question,
        result=res.result,
    )


async def answer_suggestion(
    user_id: str, session_id: str, req: model.AnswerRequest, pg_conn: PgConnection
) -> dict:
    session = await db.get_sugg_session(
        conn=pg_conn, session_id=session_id, user_id=user_id
    )
    if not session:
        raise HTTPException(status_code=404, detail="Suggestion session not found")
    if session.status != "WAITING_FOR_INPUT":
        raise HTTPException(status_code=409, detail="Session is not awaiting input")

    await db.update_sugg_session(
        pg_conn, session_id, status="PROCESSING", pending_question=None, result=None
    )
    # TODO: publish an answer job carrying req.text so the agent's checkpoint
    # resumes with the user's reply.
    return {"ok": True}


async def accept_suggestion(
    user_id: str, session_id: str, pg_conn: PgConnection
) -> dict:
    session = await db.get_sugg_session(
        conn=pg_conn, session_id=session_id, user_id=user_id
    )
    if not session:
        raise HTTPException(status_code=404, detail="Suggestion session not found")

    # Single-bullet target: apply the suggested text directly. Experience-level
    # results are JSON {bullet_id, text}[] — apply once that shape lands.
    if session.bullet_id is not None and session.result:
        async with pg_conn.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE user_base_experience_bullet
                SET bullet = %s
                WHERE id = %s AND user_experience_id = %s
                """,
                (session.result, session.bullet_id, session.experience_id),
            )

    await db.delete_sugg_session(pg_conn, session_id, user_id)
    return {"ok": True}


async def dismiss_suggestion(
    user_id: str, session_id: str, pg_conn: PgConnection
) -> dict:
    await db.delete_sugg_session(pg_conn, session_id, user_id)
    return {"ok": True}

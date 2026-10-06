import json
import uuid

from fastapi import HTTPException
from shared.amqp import BULLET_SUGG_EXCHANGE_NAME, AmqpSuggestionJob

from ..balance import require_balance, validate_model_choice
from ..deps import AmqpClientDep, PgConnection
from ..user_row import share_user_row
from . import db, model


async def start_suggestion(
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
    req: model.StartSuggestionRequest,
    user_id: str,
) -> model.StartSuggestionResponse:
    async with pg_conn.cursor() as cursor:
        # Sessions are only deleted on accept/dismiss, so a surviving row is
        # work the user hasn't finished with — hand it back to resume instead
        # of erroring.
        active = await cursor.execute(
            """
            SELECT id FROM user_suggestion
            WHERE user_id = %s AND experience_id = %s
              AND bullet_id IS NOT DISTINCT FROM %s
              AND status IN ('PROCESSING', 'WAITING_FOR_INPUT', 'COMPLETED')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id, req.experience_id, req.bullet_id),
        )
        active = await active.fetchone()
        if active:
            return model.StartSuggestionResponse(session_id=active[0])

    await require_balance(pg_conn, user_id)
    chosen_model = await validate_model_choice(pg_conn, req.model)

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

    # Dead rows (e.g. FAILED) don't resume, but the unique index on
    # (user_id, experience_id, bullet_id) would still block a fresh insert —
    # sweep them first so "start over" always works.
    await db.delete_inactive_sugg_sessions(
        pg_conn,
        user_id=user_id,
        experience_id=req.experience_id,
        bullet_id=req.bullet_id,
    )

    # If all good, make the suggestion, then frontend will poll for status updates
    session_id = str(uuid.uuid4())
    await db.create_sugg_session(
        pg_conn,
        session_id=session_id,
        user_id=user_id,
        experience_id=req.experience_id,
        bullet_id=req.bullet_id,
        model=chosen_model,
    )
    # The pooled connection only commits on dependency teardown (after the
    # response) — commit now so the dispatcher sees the row when it consumes
    # the job below.
    await pg_conn.commit()

    job = AmqpSuggestionJob(session_id=session_id, prompt=req.prompt)
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
    user_id: str,
    session_id: str,
    req: model.AnswerRequest,
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
) -> dict:
    session = await db.get_sugg_session(
        pg_conn=pg_conn, session_id=session_id, user_id=user_id
    )
    if not session:
        raise HTTPException(status_code=404, detail="Suggestion session not found")
    if session.status != "WAITING_FOR_INPUT":
        raise HTTPException(status_code=409, detail="Session is not awaiting input")

    # Keep any options already shown — a reply asking for more that ends
    # without a resubmit leaves them as the ones to apply. The row lock keeps
    # an account deletion from missing (or racing) the new work.
    async with pg_conn.transaction():
        await share_user_row(pg_conn, user_id)
        await db.update_sugg_session(
            pg_conn,
            session_id,
            status="PROCESSING",
            pending_question=None,
            result=session.result,
        )
    # Commit before publishing — the pooled connection otherwise commits at
    # teardown and could overwrite the dispatcher's result write.
    await pg_conn.commit()

    job = AmqpSuggestionJob(session_id=session_id, answer=req.text)
    publisher = await amqp_client.get_publisher(BULLET_SUGG_EXCHANGE_NAME, "#")
    await publisher.publish(job.to_message())

    return {"ok": True}


async def retry_suggestion(
    user_id: str,
    session_id: str,
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
) -> dict:
    """Requeue a FAILED session. The dispatcher resumes the checkpointed
    graph, so the user never has to re-answer anything."""
    session = await db.get_sugg_session(
        pg_conn=pg_conn, session_id=session_id, user_id=user_id
    )
    if not session:
        raise HTTPException(status_code=404, detail="Suggestion session not found")
    if session.status != "FAILED":
        raise HTTPException(
            status_code=409, detail="Only a failed suggestion can be retried"
        )

    # Retrying burns tokens again — apply the same balance gate as start.
    await require_balance(pg_conn, user_id)

    async with pg_conn.transaction():
        await share_user_row(pg_conn, user_id)
        await db.update_sugg_session(
            pg_conn,
            session_id,
            status="PROCESSING",
            pending_question=None,
            result=session.result,
        )
    # Commit before publishing — the pooled connection otherwise commits at
    # teardown and could overwrite the dispatcher's result write.
    await pg_conn.commit()

    # No answer and no prompt — the runner sees the checkpointed graph still
    # has pending nodes and resumes it where it crashed.
    job = AmqpSuggestionJob(session_id=session_id)
    publisher = await amqp_client.get_publisher(BULLET_SUGG_EXCHANGE_NAME, "#")
    await publisher.publish(job.to_message())

    return {"ok": True}


def _options_by_bullet(result: list[dict]) -> dict[int, list[str]]:
    """bullet_id -> options from a stored result: a JSON array of
    {bullet_id, options}. Sessions from before options existed stored a
    single {bullet_id, suggestion} — that reads as one option."""
    options: dict[int, list[str]] = {}
    for entry in result:
        if "options" in entry:
            options[entry["bullet_id"]] = list(entry["options"])
        else:
            options[entry["bullet_id"]] = [entry["suggestion"]]
    return options


def _chosen_updates(
    options: dict[int, list[str]], choices: list[model.AcceptChoice]
) -> list[tuple[str, int]]:
    """(new text, bullet_id) per choice; 400 on any choice the session
    didn't offer, before anything is written."""
    if not choices:
        raise HTTPException(status_code=400, detail="Pick at least one option")
    updates: list[tuple[str, int]] = []
    seen: set[int] = set()
    for choice in choices:
        offered = options.get(choice.bullet_id)
        if offered is None:
            raise HTTPException(
                status_code=400,
                detail=f"No suggestion for bullet {choice.bullet_id}",
            )
        if choice.bullet_id in seen:
            raise HTTPException(
                status_code=400,
                detail=f"Bullet {choice.bullet_id} was chosen more than once",
            )
        seen.add(choice.bullet_id)
        if choice.option >= len(offered):
            raise HTTPException(
                status_code=400,
                detail=f"Bullet {choice.bullet_id} has no option {choice.option}",
            )
        updates.append((offered[choice.option], choice.bullet_id))
    return updates


async def accept_suggestion(
    user_id: str,
    session_id: str,
    pg_conn: PgConnection,
    req: model.AcceptSuggestionRequest | None = None,
) -> dict:
    session = await db.get_sugg_session(
        pg_conn=pg_conn, session_id=session_id, user_id=user_id
    )
    if not session:
        raise HTTPException(status_code=404, detail="Suggestion session not found")

    result = session.result
    if not result or not isinstance(result, str) or result == "":
        raise HTTPException(status_code=500, detail="No result to accept")

    options = _options_by_bullet(json.loads(result))
    if req is None:
        # Clients from before options existed send no body.
        choices = [
            model.AcceptChoice(bullet_id=bullet_id, option=0) for bullet_id in options
        ]
    else:
        choices = req.choices
    updates = _chosen_updates(options, choices)

    async with pg_conn.transaction(), pg_conn.cursor() as cursor:
        for text, bullet_id in updates:
            await cursor.execute(
                """
                    UPDATE user_base_experience_bullet
                    SET bullet = %s
                    WHERE id = %s AND user_experience_id = %s
                    """,
                (text, bullet_id, session.experience_id),
            )

    await db.delete_sugg_session(pg_conn, session_id, user_id)
    return {"ok": True}


async def dismiss_suggestion(
    user_id: str, session_id: str, pg_conn: PgConnection
) -> dict:
    await db.delete_sugg_session(pg_conn, session_id, user_id)
    return {"ok": True}

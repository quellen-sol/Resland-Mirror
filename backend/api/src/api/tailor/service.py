import uuid

from fastapi import HTTPException
from shared.amqp import TAILOR_EXCHANGE_NAME, AmqpTailorJob

from ..deps import AmqpClientDep, PgConnection
from . import db, model


async def start_tailor(
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
    req: model.StartTailorRequest,
    user_id: str,
) -> model.StartTailorResponse:
    async with pg_conn.cursor() as cursor:
        # One active run per user — a second run would race the first for the
        # same base profile.
        active = await cursor.execute(
            """
            SELECT 1 FROM user_tailor_run
            WHERE user_id = %s AND status IN ('PROCESSING', 'WAITING_FOR_INPUT')
            LIMIT 1
            """,
            (user_id,),
        )
        active = await active.fetchone()
        if active:
            raise HTTPException(
                status_code=409,
                detail="A tailor run is already in progress",
            )

    run_id = str(uuid.uuid4())
    await db.create_tailor_run(
        pg_conn,
        run_id=run_id,
        user_id=user_id,
        job_description=req.job_description,
    )
    # The pooled connection only commits on dependency teardown (after the
    # response) — commit now so the dispatcher sees the row when it consumes
    # the job below.
    await pg_conn.commit()

    job = AmqpTailorJob(run_id=run_id)
    publisher = await amqp_client.get_publisher(TAILOR_EXCHANGE_NAME, "#")
    await publisher.publish(job.to_message())
    return model.StartTailorResponse(run_id=run_id)


async def get_tailor_status(
    pg_conn: PgConnection, user_id: str, run_id: str
) -> model.TailorStatusResponse:
    res = await db.get_tailor_run(pg_conn=pg_conn, user_id=user_id, run_id=run_id)
    if not res:
        raise HTTPException(status_code=404, detail="Tailor run not found")

    return model.TailorStatusResponse(
        status=res.status,
        pending_question=res.pending_question,
        result=res.result,
    )


async def answer_tailor(
    user_id: str,
    run_id: str,
    req: model.AnswerRequest,
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
) -> dict:
    run = await db.get_tailor_run(pg_conn=pg_conn, run_id=run_id, user_id=user_id)
    if not run:
        raise HTTPException(status_code=404, detail="Tailor run not found")
    if run.status != "WAITING_FOR_INPUT":
        raise HTTPException(status_code=409, detail="Run is not awaiting input")

    await db.update_tailor_run(
        pg_conn, run_id, status="PROCESSING", pending_question=None, result=None
    )
    # Commit before publishing — the pooled connection otherwise commits at
    # teardown and could overwrite the dispatcher's result write.
    await pg_conn.commit()

    job = AmqpTailorJob(run_id=run_id, answer=req.text)
    publisher = await amqp_client.get_publisher(TAILOR_EXCHANGE_NAME, "#")
    await publisher.publish(job.to_message())

    return {"ok": True}


async def dismiss_tailor(user_id: str, run_id: str, pg_conn: PgConnection) -> dict:
    await db.delete_tailor_run(pg_conn, run_id, user_id)
    return {"ok": True}

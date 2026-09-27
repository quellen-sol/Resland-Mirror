import uuid

from fastapi import HTTPException
from shared.amqp import TAILOR_EXCHANGE_NAME, AmqpTailorJob

from ..balance import require_balance, validate_model_choice
from ..deps import AmqpClientDep, PgConnection
from ..tailored import service as tailored_service
from . import db, model


async def start_tailor(
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
    req: model.StartTailorRequest,
    user_id: str,
) -> model.StartTailorResponse:
    active = await db.get_outstanding_tailor_run(pg_conn, user_id)
    if active:
        # A surviving non-COMPLETED run is unresolved work — hand it back to
        # resume (and let the UI warn that its credits are still open).
        return model.StartTailorResponse(run_id=active.id, resumed=True)

    await db.clear_completed_tailor_runs(pg_conn, user_id)
    await require_balance(pg_conn, user_id)
    chosen_model = await validate_model_choice(pg_conn, req.model)

    run_id = str(uuid.uuid4())
    await db.create_tailor_run(
        pg_conn,
        run_id=run_id,
        user_id=user_id,
        job_description=req.job_description,
        company_name=req.company_name,
        role=req.role,
        model=chosen_model,
    )
    # The pooled connection only commits on dependency teardown (after the
    # response) — commit now so the dispatcher sees the row when it consumes
    # the job below.
    await pg_conn.commit()

    job = AmqpTailorJob(run_id=run_id)
    publisher = await amqp_client.get_publisher(TAILOR_EXCHANGE_NAME, "#")
    await publisher.publish(job.to_message())
    return model.StartTailorResponse(run_id=run_id)


def _to_status(res: db.UserTailorRunRow) -> model.TailorStatusResponse:
    return model.TailorStatusResponse(
        run_id=res.id,
        status=res.status,
        job_description=res.job_description,
        company_name=res.company_name,
        role=res.role,
        pending_question=res.pending_question,
        result=res.result,
    )


async def get_active_tailor(
    pg_conn: PgConnection, user_id: str
) -> model.TailorStatusResponse:
    res = await db.get_outstanding_tailor_run(pg_conn, user_id)
    if not res:
        raise HTTPException(status_code=404, detail="No outstanding tailor run")
    return _to_status(res)


async def get_tailor_status(
    pg_conn: PgConnection, user_id: str, run_id: str
) -> model.TailorStatusResponse:
    res = await db.get_tailor_run(pg_conn=pg_conn, user_id=user_id, run_id=run_id)
    if not res:
        raise HTTPException(status_code=404, detail="Tailor run not found")
    return _to_status(res)


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
        pg_conn, run_id, status="PROCESSING", pending_question=None
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


async def save_tailor(
    user_id: str, run_id: str, pg_conn: PgConnection
) -> model.SaveTailorResponse:
    tailored_id = await tailored_service.save_from_run(
        pg_conn, user_id=user_id, run_id=run_id
    )
    return model.SaveTailorResponse(tailored_id=tailored_id)

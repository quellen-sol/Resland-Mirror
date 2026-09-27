from fastapi import APIRouter

from ..auth import Auth0UserId
from ..deps import AmqpClientDep, PgConnection
from . import model, service

router = APIRouter()


@router.post("/tailor", response_model=model.StartTailorResponse)
async def start_tailor(
    req: model.StartTailorRequest,
    user_id: Auth0UserId,
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
):
    return await service.start_tailor(
        pg_conn=pg_conn, amqp_client=amqp_client, req=req, user_id=user_id
    )


# Literal routes before /{run_id} so FastAPI binds "active" correctly.
@router.get("/tailor/active", response_model=model.TailorStatusResponse)
async def get_active_tailor(user_id: Auth0UserId, pg_conn: PgConnection):
    return await service.get_active_tailor(pg_conn=pg_conn, user_id=user_id)


@router.get("/tailor/{run_id}", response_model=model.TailorStatusResponse)
async def get_tailor_run(user_id: Auth0UserId, run_id: str, pg_conn: PgConnection):
    return await service.get_tailor_status(
        pg_conn=pg_conn, user_id=user_id, run_id=run_id
    )


@router.post("/tailor/{run_id}/answer")
async def answer_tailor(
    user_id: Auth0UserId,
    run_id: str,
    req: model.AnswerRequest,
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
):
    return await service.answer_tailor(
        user_id=user_id,
        run_id=run_id,
        req=req,
        pg_conn=pg_conn,
        amqp_client=amqp_client,
    )


@router.post("/tailor/{run_id}/dismiss")
async def dismiss_tailor(user_id: Auth0UserId, run_id: str, pg_conn: PgConnection):
    return await service.dismiss_tailor(user_id=user_id, run_id=run_id, pg_conn=pg_conn)


@router.post("/tailor/{run_id}/save", response_model=model.SaveTailorResponse)
async def save_tailor(user_id: Auth0UserId, run_id: str, pg_conn: PgConnection):
    return await service.save_tailor(user_id=user_id, run_id=run_id, pg_conn=pg_conn)

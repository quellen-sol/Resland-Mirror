from fastapi import APIRouter

from ..auth import Auth0UserId
from ..deps import AmqpClientDep, PgConnection
from . import model, service

router = APIRouter(prefix="/bullets")


@router.post("/suggestions", response_model=model.StartSuggestionResponse)
async def start_suggestion(
    req: model.StartSuggestionRequest,
    user_id: Auth0UserId,
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
):
    return await service.start_suggestion(
        pg_conn=pg_conn, amqp_client=amqp_client, req=req, user_id=user_id
    )


@router.get("/suggestions/{session_id}", response_model=model.SuggestionStatusResponse)
async def get_suggestion(user_id: Auth0UserId, session_id: str, pg_conn: PgConnection):
    return await service.get_suggestion_status(
        pg_conn=pg_conn, user_id=user_id, session_id=session_id
    )


@router.post("/suggestions/{session_id}/answer")
async def answer_suggestion(
    user_id: Auth0UserId,
    session_id: str,
    req: model.AnswerRequest,
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
):
    return await service.answer_suggestion(
        user_id=user_id,
        session_id=session_id,
        req=req,
        pg_conn=pg_conn,
        amqp_client=amqp_client,
    )


@router.post("/suggestions/{session_id}/retry")
async def retry_suggestion(
    user_id: Auth0UserId,
    session_id: str,
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
):
    return await service.retry_suggestion(
        user_id=user_id,
        session_id=session_id,
        pg_conn=pg_conn,
        amqp_client=amqp_client,
    )


@router.post("/suggestions/{session_id}/accept")
async def accept_suggestion(
    user_id: Auth0UserId, session_id: str, pg_conn: PgConnection
):
    return await service.accept_suggestion(
        user_id=user_id, session_id=session_id, pg_conn=pg_conn
    )


@router.post("/suggestions/{session_id}/dismiss")
async def dismiss_suggestion(
    user_id: Auth0UserId, session_id: str, pg_conn: PgConnection
):
    return await service.dismiss_suggestion(
        user_id=user_id, session_id=session_id, pg_conn=pg_conn
    )

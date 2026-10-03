from fastapi import APIRouter

from ..auth import Auth0UserId
from ..deps import AmqpClientDep, PgConnection
from . import model, service

router = APIRouter()


# Literal routes before /{session_id} so FastAPI binds them correctly.
@router.get("/system-design/problems", response_model=model.ProblemsResponse)
async def list_problems(user_id: Auth0UserId):
    return service.list_problems()


@router.get("/system-design/active", response_model=model.SessionStatusResponse)
async def get_active(user_id: Auth0UserId, pg_conn: PgConnection):
    return await service.get_active(pg_conn=pg_conn, user_id=user_id)


@router.post("/system-design", response_model=model.StartSystemDesignResponse)
async def start_system_design(
    req: model.StartSystemDesignRequest,
    user_id: Auth0UserId,
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
):
    return await service.start_system_design(
        pg_conn=pg_conn, amqp_client=amqp_client, req=req, user_id=user_id
    )


@router.get("/system-design/{session_id}", response_model=model.SessionStatusResponse)
async def get_status(user_id: Auth0UserId, session_id: str, pg_conn: PgConnection):
    return await service.get_status(
        pg_conn=pg_conn, user_id=user_id, session_id=session_id
    )


@router.get(
    "/system-design/{session_id}/workspace", response_model=model.WorkspaceResponse
)
async def get_workspace(user_id: Auth0UserId, session_id: str, pg_conn: PgConnection):
    return await service.get_workspace(
        pg_conn=pg_conn, user_id=user_id, session_id=session_id
    )


@router.put(
    "/system-design/{session_id}/workspace", response_model=model.WorkspaceResponse
)
async def save_workspace(
    user_id: Auth0UserId,
    session_id: str,
    req: model.Workspace,
    pg_conn: PgConnection,
):
    return await service.save_workspace(
        pg_conn=pg_conn, user_id=user_id, session_id=session_id, req=req
    )


@router.post("/system-design/{session_id}/turn", response_model=model.TurnResponse)
async def take_turn(
    user_id: Auth0UserId,
    session_id: str,
    req: model.TurnRequest,
    pg_conn: PgConnection,
    amqp_client: AmqpClientDep,
):
    return await service.take_turn(
        pg_conn=pg_conn,
        amqp_client=amqp_client,
        user_id=user_id,
        session_id=session_id,
        req=req,
    )


@router.post("/system-design/{session_id}/dismiss")
async def dismiss(user_id: Auth0UserId, session_id: str, pg_conn: PgConnection):
    return await service.dismiss(
        pg_conn=pg_conn, user_id=user_id, session_id=session_id
    )

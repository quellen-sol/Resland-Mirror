from fastapi import APIRouter

from ..auth import Auth0UserId
from ..deps import PgConnection
from . import model, service

router = APIRouter()


@router.get("/memory", response_model=model.MemoryListResponse)
async def list_memory(user_id: Auth0UserId, pg_conn: PgConnection):
    return await service.list_memory(pg_conn=pg_conn, user_id=user_id)


@router.post("/memory", response_model=model.RememberResponse)
async def remember(
    user_id: Auth0UserId, req: model.RememberRequest, pg_conn: PgConnection
):
    return await service.remember(pg_conn=pg_conn, user_id=user_id, req=req)

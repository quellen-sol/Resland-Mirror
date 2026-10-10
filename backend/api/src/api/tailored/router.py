from fastapi import APIRouter

from ..auth import Auth0UserId
from ..deps import PgConnection
from . import model, service

router = APIRouter()


@router.get("/tailored", response_model=model.TailoredListResponse)
async def list_tailored(user_id: Auth0UserId, pg_conn: PgConnection):
    return await service.list_tailored(pg_conn=pg_conn, user_id=user_id)


@router.post("/tailored", response_model=model.CreateTailoredResponse)
async def create_tailored(
    user_id: Auth0UserId, req: model.CreateTailoredRequest, pg_conn: PgConnection
):
    return await service.create_tailored(pg_conn=pg_conn, user_id=user_id, req=req)


@router.get("/tailored/{tailored_id}", response_model=model.TailoredResumeResponse)
async def get_tailored(user_id: Auth0UserId, tailored_id: str, pg_conn: PgConnection):
    return await service.get_tailored(
        pg_conn=pg_conn, user_id=user_id, tailored_id=tailored_id
    )


@router.patch("/tailored/{tailored_id}", response_model=model.TailoredResumeResponse)
async def update_tailored(
    user_id: Auth0UserId,
    tailored_id: str,
    req: model.UpdateTailoredRequest,
    pg_conn: PgConnection,
):
    return await service.update_tailored(
        pg_conn=pg_conn, user_id=user_id, tailored_id=tailored_id, req=req
    )


@router.delete("/tailored/{tailored_id}")
async def delete_tailored(user_id: Auth0UserId, tailored_id: str, pg_conn: PgConnection):
    return await service.delete_tailored(
        pg_conn=pg_conn, user_id=user_id, tailored_id=tailored_id
    )


@router.post("/tailored/{tailored_id}/export", response_model=model.ExportTailoredResponse)
async def export_tailored(user_id: Auth0UserId, tailored_id: str, pg_conn: PgConnection):
    return await service.export_tailored(
        pg_conn=pg_conn, user_id=user_id, tailored_id=tailored_id
    )

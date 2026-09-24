from fastapi import APIRouter

from ..auth import Auth0UserId
from ..deps import PgConnection
from . import model, service

router = APIRouter()


@router.get("/resume/export", response_model=model.ExportResumeResponse)
async def export_resume(user_id: Auth0UserId, pg_conn: PgConnection):
    return await service.export_resume(pg_conn=pg_conn, user_id=user_id)

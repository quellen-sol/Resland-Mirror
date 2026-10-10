from fastapi import APIRouter

from ..auth import Auth0UserId
from ..deps import PgConnection
from . import model, service

router = APIRouter()


@router.get("/profile", response_model=model.ProfileResponse)
async def get_profile(user_id: Auth0UserId, pg_conn: PgConnection):
    return await service.get_profile(pg_conn=pg_conn, user_id=user_id)

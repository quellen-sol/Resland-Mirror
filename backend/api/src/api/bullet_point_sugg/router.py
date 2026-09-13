from fastapi import APIRouter
from shared.pg import get_pg_client

from ..auth import Auth0UserId
from ..env_vars import PG_URL

router = APIRouter("/bullets")

@router.post("/improve-entire-job")
async def improve_entire_job(userId: Auth0UserId, companyId: int):
    pg_client = get_pg_client(PG_URL)

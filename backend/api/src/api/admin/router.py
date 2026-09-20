from fastapi import APIRouter

from ..auth import SiteAdmin
from ..deps import PgConnection
from . import model, service

router = APIRouter(prefix="/admin")


@router.get("/users", response_model=model.AdminUsersResponse)
async def admin_users(user_id: SiteAdmin, pg_conn: PgConnection):
    return await service.list_users(pg_conn=pg_conn)


@router.get("/usage", response_model=model.AdminUsageResponse)
async def admin_usage(user_id: SiteAdmin, pg_conn: PgConnection):
    return await service.get_usage(pg_conn=pg_conn)


@router.get("/purchases", response_model=model.AdminPurchasesResponse)
async def admin_purchases(user_id: SiteAdmin, pg_conn: PgConnection):
    return await service.list_purchases(pg_conn=pg_conn)

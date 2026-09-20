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


@router.get("/models", response_model=model.AdminModelsResponse)
async def admin_models(user_id: SiteAdmin, pg_conn: PgConnection):
    return await service.list_models(pg_conn=pg_conn)


# :path — model ids contain slashes ("openrouter:openai/gpt-5-mini")
@router.put("/models/{model_id:path}", response_model=model.ModelPricingRow)
async def admin_upsert_model(
    model_id: str,
    body: model.ModelPricingUpsert,
    user_id: SiteAdmin,
    pg_conn: PgConnection,
):
    return await service.upsert_model(pg_conn=pg_conn, model_id=model_id, body=body)


@router.delete("/models/{model_id:path}", status_code=204)
async def admin_delete_model(
    model_id: str, user_id: SiteAdmin, pg_conn: PgConnection
):
    await service.delete_model(pg_conn=pg_conn, model_id=model_id)

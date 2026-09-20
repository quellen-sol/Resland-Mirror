from fastapi import APIRouter, Request

from ..auth import Auth0UserId
from ..deps import PgConnection
from . import model, service
from .model import TOKEN_PACKS

router = APIRouter()


@router.get("/billing/balance", response_model=model.BalanceResponse)
async def get_balance(user_id: Auth0UserId, pg_conn: PgConnection):
    return await service.get_balance(pg_conn=pg_conn, user_id=user_id)


@router.get("/billing/packs", response_model=list[model.TokenPack])
async def get_packs(user_id: Auth0UserId):
    return list(TOKEN_PACKS.values())


@router.get("/billing/purchases", response_model=model.PurchasesResponse)
async def get_purchases(user_id: Auth0UserId, pg_conn: PgConnection):
    return await service.list_purchases(pg_conn=pg_conn, user_id=user_id)


@router.post("/billing/checkout", response_model=model.CheckoutResponse)
async def checkout(
    req: model.CheckoutRequest, user_id: Auth0UserId, pg_conn: PgConnection
):
    return await service.create_checkout(pg_conn=pg_conn, user_id=user_id, req=req)


@router.get("/models", response_model=model.ModelsResponse)
async def list_models(user_id: Auth0UserId, pg_conn: PgConnection):
    return await service.list_models(pg_conn=pg_conn)


# Stripe calls this directly — no auth, verified by webhook signature instead.
@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, pg_conn: PgConnection):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    return await service.handle_webhook(
        pg_conn=pg_conn, payload=payload, sig_header=sig
    )

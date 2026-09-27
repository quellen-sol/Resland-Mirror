from collections.abc import Generator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from shared.amqp import AmqpClient

from . import deps
from .admin.router import router as admin_router
from .auth import (
    is_docs_request,
    is_site_admin_request,
    is_stripe_webhook_request,
)
from .billing.router import router as billing_router
from .bullet_point_sugg.router import router as bullet_sugg_router
from .env_vars import AMQP_URL, MAINTENANCE_MODE
from .resume_export.router import router as resume_export_router
from .resume_upload.router import router as resume_upload_router
from .tailor.router import router as tailor_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> Generator[None, Any, None]:
    # One shared client for the process — setup declares topology idempotently.
    deps.amqp_client = AmqpClient(AMQP_URL)
    await deps.amqp_client.setup()
    yield
    await deps.amqp_client.close()
    deps.amqp_client = None


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def maintenance_mode(request: Request, call_next):
    if (
        MAINTENANCE_MODE
        and not is_docs_request(request)
        and not is_stripe_webhook_request(request)
        and not await is_site_admin_request(request)
    ):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Resland is down for maintenance. Please try again later."
            },
            headers={"Retry-After": "600"},
        )
    return await call_next(request)


origins = [
    "http://localhost:3000",
    "http://192.168.1.8:3000",
    "https://resland.org",
    "https://www.resland.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_upload_router)
app.include_router(resume_export_router)
app.include_router(bullet_sugg_router)
app.include_router(tailor_router)
app.include_router(billing_router)
app.include_router(admin_router)

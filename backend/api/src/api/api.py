from collections.abc import Generator
from contextlib import asynccontextmanager
from typing import Any

import psycopg_pool
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.amqp import AmqpClient

from . import deps
from .bullet_point_sugg.router import router as bullet_sugg_router
from .env_vars import AMQP_URL, PG_URL
from .resume_upload.router import router as resume_upload_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> Generator[None, Any, None]:
    # One shared client for the process — setup declares topology idempotently.
    deps.amqp_client = AmqpClient(AMQP_URL)
    await deps.amqp_client.setup()

    deps.pg_pool = psycopg_pool.AsyncConnectionPool(conninfo=PG_URL, open=False)
    await deps.pg_pool.open()
    yield
    await deps.pg_pool.close()
    deps.pg_pool = None

    await deps.amqp_client.close()
    deps.amqp_client = None


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://192.168.1.8:3000",
    "http://192.168.1.8:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_upload_router)
app.include_router(bullet_sugg_router)

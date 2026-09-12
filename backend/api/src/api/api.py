import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.amqp import AMQPClient

from .env_vars import AMQP_URL
from .resume_upload.router import router as resume_upload_router

amqp_client = AMQPClient(AMQP_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await amqp_client.setup()
    yield
    await amqp_client.close()


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.amqp_client = amqp_client

app.include_router(resume_upload_router)

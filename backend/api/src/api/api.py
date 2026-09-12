import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.amqp import AMQPClient
from shared.s3 import get_s3_client

from .resume_upload.router import router as resume_upload_router
from .env_vars import S3_RESUME_BUCKET, AMQP_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

amqp_client = AMQPClient(AMQP_URL)
s3_client = get_s3_client(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


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
app.state.s3_client = s3_client

app.include_router(resume_upload_router)

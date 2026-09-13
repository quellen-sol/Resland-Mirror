import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.amqp import AMQPClient

from .env_vars import AMQP_URL
from .resume_upload.router import router as resume_upload_router

setup_amqp_client = AMQPClient(AMQP_URL)
asyncio.run(setup_amqp_client.setup())
setup_amqp_client.close()
setup_amqp_client = None

app = FastAPI()

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

app.include_router(resume_upload_router)

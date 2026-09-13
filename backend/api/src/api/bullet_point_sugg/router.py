import asyncio

from fastapi import APIRouter
from shared.amqp import BULLET_SUGG_EXCHANGE_NAME, AMQPClient
from shared.pg import get_pg_client

from ..auth import Auth0UserId
from ..env_vars import AMQP_URL, PG_URL

amqp_client = AMQPClient(AMQP_URL)
asyncio.run(amqp_client.setup())
amqp_publisher = asyncio.run(amqp_client.get_publisher(BULLET_SUGG_EXCHANGE_NAME, "#"))

router = APIRouter("/bullets")


@router.post("/start-exp-improvement")
async def start_exp_improvement(userId: Auth0UserId, companyId: int):
    pg_client = get_pg_client(PG_URL)

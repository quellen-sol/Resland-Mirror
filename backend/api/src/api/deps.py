from typing import Annotated

from fastapi import Depends
from psycopg import AsyncConnection
from psycopg.rows import TupleRow
from shared.amqp import AmqpClient

from .env_vars import PG_URL

# Set during the FastAPI lifespan (see api.py) so the client's AMQP connection
# lives on the app's event loop instead of a throwaway asyncio.run() loop.
amqp_client: AmqpClient | None = None


async def get_pg_conn():
    conn = await AsyncConnection.connect(conninfo=PG_URL, autocommit=True)
    try:
        yield conn
    finally:
        await conn.close()


def get_amqp_client() -> AmqpClient:
    if amqp_client is None:
        raise RuntimeError("AMQP client not initialized — lifespan not running?")
    return amqp_client


PgConnection = Annotated[AsyncConnection[TupleRow], Depends(get_pg_conn)]
AmqpClientDep = Annotated[AmqpClient, Depends(get_amqp_client)]

from typing import Annotated

from fastapi import Depends
from psycopg import AsyncConnection
from psycopg.rows import TupleRow
from psycopg_pool import AsyncConnectionPool
from shared.amqp import AmqpClient

# Set during the FastAPI lifespan (see api.py) so the client's AMQP connection
# lives on the app's event loop instead of a throwaway asyncio.run() loop.
amqp_client: AmqpClient | None = None
pg_pool: AsyncConnectionPool | None = None


async def get_pg_conn() -> AsyncConnection:
    if pg_pool is None:
        raise RuntimeError("PostgreSQL pool not initialized — lifespan not running?")
    async with pg_pool.connection() as conn:
        yield conn


def get_amqp_client() -> AmqpClient:
    if amqp_client is None:
        raise RuntimeError("AMQP client not initialized — lifespan not running?")
    return amqp_client


PgConnection = Annotated[AsyncConnection[TupleRow], Depends(get_pg_conn)]
AmqpClientDep = Annotated[AmqpClient, Depends(get_amqp_client)]

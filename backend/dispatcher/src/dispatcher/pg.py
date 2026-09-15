from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from .env_vars import PG_URL

pg_pool = ConnectionPool(conninfo=PG_URL, open=False)
pg_pool.open()

# Create langgraph checkpoint tables once at startup.
with pg_pool.connection() as _conn:
    _conn.autocommit = True
    PostgresSaver(_conn).setup()

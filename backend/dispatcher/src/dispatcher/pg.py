from psycopg_pool import ConnectionPool

from .env_vars import PG_URL

pg_pool = ConnectionPool(conninfo=PG_URL, open=False)
pg_pool.open()

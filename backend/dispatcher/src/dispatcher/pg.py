import psycopg
from langgraph.checkpoint.postgres import PostgresSaver

from .env_vars import PG_URL

with psycopg.connect(conninfo=PG_URL, autocommit=True) as conn:
    PostgresSaver(conn).setup()

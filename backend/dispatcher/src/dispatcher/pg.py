import psycopg
from langgraph.checkpoint.postgres import PostgresSaver

from .env_vars import PG_URL

def do_pg_setup():
    print("Connecting to pg for checkpointer table setup")
    with psycopg.connect(conninfo=PG_URL, autocommit=True) as conn:
        print("Setting up checkpoint tables...")
        PostgresSaver(conn).setup()
        print("Checkpoints set up!")

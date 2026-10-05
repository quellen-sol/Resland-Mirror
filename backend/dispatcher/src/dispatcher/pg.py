import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import sql
from shared.checkpoints import (
    CHECKPOINT_CONN_OPTIONS,
    CHECKPOINT_SCHEMA,
    CHECKPOINTER_TABLES,
)

from .env_vars import PG_URL


def do_pg_setup(url: str | None = None):
    print("Connecting to pg for checkpointer table setup")
    with psycopg.connect(conninfo=url or PG_URL, autocommit=True) as conn:
        moved = move_checkpoint_tables(conn)
        if moved:
            print(f"Moved {', '.join(moved)} into the {CHECKPOINT_SCHEMA} schema")
    with psycopg.connect(
        conninfo=url or PG_URL, autocommit=True, options=CHECKPOINT_CONN_OPTIONS
    ) as conn:
        print("Setting up checkpoint tables...")
        PostgresSaver(conn).setup()
        print("Checkpoints set up!")


def move_checkpoint_tables(conn: psycopg.Connection) -> list[str]:
    """Create the checkpointer's schema and move into it any tables a
    dispatcher from before the schema left in `public`. Returns the tables
    moved."""
    schema = sql.Identifier(CHECKPOINT_SCHEMA)
    moved = []
    with conn.transaction():
        # Dispatchers booting together would otherwise race on the move.
        conn.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))",
            (f"{CHECKPOINT_SCHEMA}.move_checkpoint_tables",),
        )
        conn.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(schema))
        for table in CHECKPOINTER_TABLES:
            legacy, current = conn.execute(
                "SELECT to_regclass(%s), to_regclass(%s)",
                (f"public.{table}", f"{CHECKPOINT_SCHEMA}.{table}"),
            ).fetchone()
            # Never replace a table already in the schema — the public one
            # is the stale copy.
            if legacy and not current:
                conn.execute(
                    sql.SQL("ALTER TABLE {} SET SCHEMA {}").format(
                        sql.Identifier("public", table), schema
                    )
                )
                moved.append(table)
    return moved

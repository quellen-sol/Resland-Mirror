import psycopg


def get_pg_client(url: str, autocommit=True, row_factory=None) -> psycopg.Connection:
    # This is managed via a connection pool, so we can jsut call connect without worrying about excess connections
    # autocommit: each execute() persists immediately — without it, close() rolls back writes.
    return psycopg.connect(url, autocommit=autocommit, row_factory=row_factory)

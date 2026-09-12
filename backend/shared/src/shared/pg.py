import psycopg


def get_pg_client(url: str, autocommit=True):
    # This is managed via a connection pool, so we can jsut call connect without worrying about excess connections
    # autocommit: each execute() persists immediately — without it, close() rolls back writes.
    return psycopg.connect(url, autocommit=autocommit)

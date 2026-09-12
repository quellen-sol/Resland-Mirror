import psycopg


def get_pg_client(url: str):
    # This is managed via a connection pool, so we can jsut call connect without worrying about excess connections
    return psycopg.connect(url)

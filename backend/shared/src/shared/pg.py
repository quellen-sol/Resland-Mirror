import psycopg


def get_pg_client(
    url: str, autocommit=True, row_factory=None, options: str | None = None
) -> psycopg.Connection:
    # No pool — every call is a fresh connection. Use as `with get_pg_client(...)`
    # or close() it yourself, or you'll exhaust the DB's client limit.
    # autocommit: each execute() persists immediately — without it, close() rolls back writes.
    # options: libpq startup options, e.g. shared.checkpoints.CHECKPOINT_CONN_OPTIONS.
    return psycopg.connect(
        url, autocommit=autocommit, row_factory=row_factory, options=options
    )

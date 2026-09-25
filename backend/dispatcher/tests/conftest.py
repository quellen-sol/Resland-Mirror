"""Shared fixtures for dispatcher tests.

These exercise real SQL, so they need a Postgres database — compose's
`postgres` service works, or point TEST_PG_URL elsewhere. They skip cleanly
when no database is reachable.
"""

import os

import psycopg
import pytest

TEST_PG_URL = os.getenv(
    "TEST_PG_URL", "postgres://resland:resland@localhost:5432/resland"
)

# db_ops' import chain reads env vars; point them at the test database so any
# module that connects at import time lands here.
os.environ.setdefault("PG_URL", TEST_PG_URL)

_conn = None
try:
    _conn = psycopg.connect(TEST_PG_URL, connect_timeout=3, autocommit=True)
except Exception:
    pass

# Lazy skip inside the fixture so unit tests that don't need Postgres still
# run when no database is reachable.
PG_AVAILABLE = _conn is not None
if _conn is not None:
    _conn.close()


@pytest.fixture
def pg():
    if not PG_AVAILABLE:
        pytest.skip(
            f"dispatcher tests need Postgres at TEST_PG_URL ({TEST_PG_URL})"
        )
    with psycopg.connect(TEST_PG_URL, autocommit=True) as conn:
        conn.execute(
            'TRUNCATE balance_purchase, token_usage, model_pricing, "user"'
            " CASCADE"
        )
        yield conn

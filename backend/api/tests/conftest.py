"""Shared fixtures for API tests.

These tests exercise real SQL, so they need a Postgres database — the compose
stack's `postgres` service works (`docker compose up postgres`), or point
TEST_PG_URL anywhere else. They skip cleanly when no database is reachable.
"""

import os

import psycopg
import pytest
from shared.testing import destructive_db_ok

# Default to a *_test database so the safe path is the default path; the
# destructive fixtures below refuse to run against anything else.
TEST_PG_URL = os.getenv(
    "TEST_PG_URL", "postgres://resland:resland@localhost:5432/resland_test"
)

_DESTRUCTIVE_OK, _DESTRUCTIVE_REASON = destructive_db_ok(TEST_PG_URL)

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
async def pg():
    if not PG_AVAILABLE:
        pytest.skip(f"needs Postgres at TEST_PG_URL ({TEST_PG_URL})")
    if not _DESTRUCTIVE_OK:
        pytest.skip(_DESTRUCTIVE_REASON)
    conn = await psycopg.AsyncConnection.connect(TEST_PG_URL, autocommit=True)
    await conn.execute(
        'TRUNCATE balance_purchase, token_usage, model_pricing, "user" CASCADE'
    )
    yield conn
    await conn.close()


@pytest.fixture
async def user(pg):
    await pg.execute(
        'INSERT INTO "user" (auth0_id, balance_cents) VALUES (%s, %s)',
        ("u1", 0),
    )
    return "u1"

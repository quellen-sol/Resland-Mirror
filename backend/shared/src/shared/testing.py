"""Test-support helpers shared by the backend suites.

Lives in ``shared`` so the api and dispatcher ``conftest.py`` files use a single
implementation of the destructive-fixture guard.
"""

from __future__ import annotations

import os
from urllib.parse import unquote, urlparse

OPT_IN_ENV = "ALLOW_DESTRUCTIVE_TESTS"

# Substrings that mark a database as safe to wipe. Deliberately generous on the
# safe side: a database whose name mentions any of these is treated as scratch.
_SCRATCH_MARKERS = ("test", "scratch", "sandbox", "tmp")


def pg_database_name(url: str) -> str:
    """Return the database name from a Postgres URL ('' when absent)."""
    return unquote((urlparse(url).path or "").lstrip("/"))


def destructive_db_ok(url: str) -> tuple[bool, str]:
    """Decide whether destructive fixtures may run against ``url``.

    Returns ``(allowed, reason)`` — ``reason`` is a human-readable explanation
    suitable for ``pytest.skip``. Tests are only allowed to TRUNCATE when the
    database is provably scratch (name matches a marker) or the operator has
    explicitly opted in with ``ALLOW_DESTRUCTIVE_TESTS=1``.
    """
    if os.environ.get(OPT_IN_ENV) == "1":
        return True, f"{OPT_IN_ENV}=1 opt-in"

    name = pg_database_name(url)
    if not name:
        return False, (
            f"cannot determine the database name in TEST_PG_URL {url!r}; "
            f"set {OPT_IN_ENV}=1 to run destructive fixtures anyway"
        )
    if any(marker in name.lower() for marker in _SCRATCH_MARKERS):
        return True, f"database {name!r} looks like a scratch/test database"
    return False, (
        f"refusing to TRUNCATE non-test database {name!r}; "
        f"point TEST_PG_URL at a *_test database or set {OPT_IN_ENV}=1"
    )

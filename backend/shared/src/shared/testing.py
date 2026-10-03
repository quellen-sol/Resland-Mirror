"""Test-support helpers shared by the backend suites.

Lives in ``shared`` so the api and dispatcher ``conftest.py`` files use a single
implementation of the destructive-fixture guard.
"""

from __future__ import annotations

import os
import re
from urllib.parse import parse_qs, unquote, urlparse

OPT_IN_ENV = "ALLOW_DESTRUCTIVE_TESTS"

# A database is implicitly considered scratch only when its name's *last*
# token is one of these (``resland_test``, ``resland-scratch``, ``test``…).
# Matching whole tokens instead of substrings keeps names like ``contest_prod``
# from being treated as disposable.
_SCRATCH_TOKENS = {"test", "tests", "scratch", "sandbox", "tmp", "temp"}

# libpq lets the query string override the database in the URL path, so the
# effective name has to account for these.
_DBNAME_PARAMS = ("dbname", "database")


def pg_database_name(url: str) -> str:
    """Return the database name libpq will actually connect to ('' if none).

    Query-string overrides (``?dbname=``/``?database=``) win over the path,
    matching libpq's own precedence.
    """
    query = parse_qs(urlparse(url).query)
    for param in _DBNAME_PARAMS:
        values = query.get(param)
        if values and values[0]:
            return unquote(values[0])
    return unquote((urlparse(url).path or "").lstrip("/"))


def is_scratch_db_name(name: str) -> bool:
    """True when ``name``'s final token marks it as disposable."""
    tokens = [token for token in re.split(r"[^a-z0-9]+", name.lower()) if token]
    return bool(tokens) and tokens[-1] in _SCRATCH_TOKENS


def destructive_db_ok(url: str) -> tuple[bool, str]:
    """Decide whether destructive fixtures may run against ``url``.

    Returns ``(allowed, reason)`` — ``reason`` is a human-readable explanation
    suitable for ``pytest.skip``. Tests are only allowed to TRUNCATE when the
    effective database name is unambiguously scratch (its last token is a
    scratch marker) or the operator has explicitly opted in with
    ``ALLOW_DESTRUCTIVE_TESTS=1``.
    """
    if os.environ.get(OPT_IN_ENV) == "1":
        return True, f"{OPT_IN_ENV}=1 opt-in"

    name = pg_database_name(url)
    if not name:
        return False, (
            f"cannot determine the database name in TEST_PG_URL {url!r}; "
            f"set {OPT_IN_ENV}=1 to run destructive fixtures anyway"
        )
    if is_scratch_db_name(name):
        return True, f"database {name!r} looks like a scratch/test database"
    return False, (
        f"refusing to TRUNCATE non-test database {name!r}; "
        f"point TEST_PG_URL at a *_test database or set {OPT_IN_ENV}=1"
    )

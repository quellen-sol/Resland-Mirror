"""DB-backed site settings behind a short-TTL in-process cache.

The `site_settings` table holds the admin-toggled kill switches
(maintenance mode, payments paused). Every request path consults these —
the maintenance middleware and checkout guard — so reads are cached and the
row is hit at most once per TTL per process. Writes go through update(),
which upserts the row and writes through to the cache, so the toggling
instance sees the new value immediately.
"""

import time
from dataclasses import dataclass
from datetime import datetime

from psycopg import AsyncConnection
from psycopg.rows import TupleRow

from .env_vars import MAINTENANCE_MODE, PG_URL

_ROW_ID = 1
_TTL_SECONDS = 15.0


@dataclass(frozen=True)
class SiteSettings:
    maintenance_mode: bool
    payments_paused: bool
    updated_at: datetime | None = None


_cache: SiteSettings | None = None
_cache_expires_at = 0.0


async def _fetch(pg_conn: AsyncConnection[TupleRow]) -> SiteSettings:
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            "SELECT maintenance_mode, payments_paused, updated_at "
            "FROM site_settings WHERE id = %s",
            (_ROW_ID,),
        )
        row = await res.fetchone()
        if not row:
            # First-ever read: seed maintenance_mode from the retired env var
            # so a deploy paused via MAINTENANCE_MODE stays paused, then the
            # dashboard owns the flag.
            await cursor.execute(
                "INSERT INTO site_settings (id, maintenance_mode) "
                "VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
                (_ROW_ID, MAINTENANCE_MODE),
            )
            res = await cursor.execute(
                "SELECT maintenance_mode, payments_paused, updated_at "
                "FROM site_settings WHERE id = %s",
                (_ROW_ID,),
            )
            row = await res.fetchone()
    if not row:
        return SiteSettings(maintenance_mode=False, payments_paused=False)
    return SiteSettings(
        maintenance_mode=bool(row[0]),
        payments_paused=bool(row[1]),
        updated_at=row[2],
    )


async def get(pg_conn: AsyncConnection[TupleRow] | None = None) -> SiteSettings:
    """Cached read; refreshes from Postgres at most once per TTL."""
    global _cache, _cache_expires_at
    now = time.monotonic()
    if _cache is not None and now < _cache_expires_at:
        return _cache
    try:
        if pg_conn is not None:
            value = await _fetch(pg_conn)
        else:
            async with await AsyncConnection.connect(
                conninfo=PG_URL, autocommit=True
            ) as conn:
                value = await _fetch(conn)
    except Exception as e:
        # Fail open on the last-known (or all-off) values — a DB blip must
        # not throw the site into maintenance on its own.
        print(f"site_settings read failed: {e}")
        return _cache or SiteSettings(
            maintenance_mode=False, payments_paused=False
        )
    _cache = value
    _cache_expires_at = now + _TTL_SECONDS
    return value


async def update(
    pg_conn: AsyncConnection[TupleRow],
    *,
    maintenance_mode: bool | None = None,
    payments_paused: bool | None = None,
) -> SiteSettings:
    """Upsert the singleton row and write through to the cache."""
    global _cache, _cache_expires_at
    current = await get(pg_conn)
    merged = SiteSettings(
        maintenance_mode=(
            current.maintenance_mode if maintenance_mode is None else maintenance_mode
        ),
        payments_paused=(
            current.payments_paused if payments_paused is None else payments_paused
        ),
    )
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            UPDATE site_settings
            SET maintenance_mode = %s, payments_paused = %s, updated_at = now()
            WHERE id = %s
            RETURNING maintenance_mode, payments_paused, updated_at
            """,
            (merged.maintenance_mode, merged.payments_paused, _ROW_ID),
        )
        row = await res.fetchone()
    value = SiteSettings(
        maintenance_mode=bool(row[0]),
        payments_paused=bool(row[1]),
        updated_at=row[2],
    )
    _cache = value
    _cache_expires_at = time.monotonic() + _TTL_SECONDS
    return value


async def is_maintenance_mode() -> bool:
    return (await get()).maintenance_mode


async def payments_paused(pg_conn: AsyncConnection[TupleRow]) -> bool:
    return (await get(pg_conn)).payments_paused


def _reset_cache() -> None:
    global _cache, _cache_expires_at
    _cache = None
    _cache_expires_at = 0.0

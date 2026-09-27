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
_TTL_SECONDS = 600.0


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
        # Serve the last-known values when we have them. With nothing cached
        # fall back to the env seed for maintenance (so an env-paused deploy
        # stays paused) and fail payments closed — a checkout needs the DB
        # anyway, so this only guards a read-path blip.
        print(f"site_settings read failed: {e}")
        return _cache or SiteSettings(
            maintenance_mode=MAINTENANCE_MODE, payments_paused=True
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
    """Atomically patch only the provided fields; write through to cache.

    None means "don't touch" — each field is COALESCE'd against the stored
    row so concurrent admin writes on different replicas can't undo each
    other via a stale TTL cache. The INSERT path seeds maintenance_mode
    from the env var for a never-created row.
    """
    global _cache, _cache_expires_at
    if maintenance_mode is None and payments_paused is None:
        return await get(pg_conn)
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            INSERT INTO site_settings (id, maintenance_mode, payments_paused)
            VALUES (%s, COALESCE(%s, %s), COALESCE(%s, %s))
            ON CONFLICT (id) DO UPDATE SET
                maintenance_mode = COALESCE(%s, site_settings.maintenance_mode),
                payments_paused = COALESCE(%s, site_settings.payments_paused),
                updated_at = now()
            RETURNING maintenance_mode, payments_paused, updated_at
            """,
            (
                _ROW_ID,
                maintenance_mode,
                MAINTENANCE_MODE,
                payments_paused,
                False,
                maintenance_mode,
                payments_paused,
            ),
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

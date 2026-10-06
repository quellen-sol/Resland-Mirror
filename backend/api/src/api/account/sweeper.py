"""Finishes account deletions in the background.

DELETE /account commits the erase, records it in account_deletion, then asks
Auth0 to delete the login. If that call fails, or the process dies between the
commit and the call, the login would otherwise survive unnoticed. Every API
process runs this sweep on an interval: it retries the Auth0 deletion for
every row still waiting on it, and drops rows once Auth0 is done and every
session from before the deletion has expired. Auth0 treats deleting an
already-deleted user as done, so overlapping sweeps across replicas are safe.
"""

import asyncio
from dataclasses import dataclass

from psycopg import AsyncConnection

from ..deps import PgConnection
from ..env_vars import PG_URL
from . import db
from .auth0_mgmt import Auth0Management, Auth0ManagementError, auth0_management

SWEEP_INTERVAL_S = 600.0


@dataclass
class SweepResult:
    logins_deleted: int
    purged: int


async def sweep_once(conn: PgConnection, auth0: Auth0Management) -> SweepResult:
    """One pass: retry pending Auth0 deletions (skipped when the Management
    API isn't configured), then purge finished rows. Auth0 failures are
    logged and left for the next pass."""
    deleted = 0
    if auth0.configured:
        for user_id in await db.pending_auth0_deletions(conn):
            try:
                await auth0.delete_user(user_id)
            except Auth0ManagementError as e:
                # No account id in the log: it's a deleted account's.
                print(f"Deletion sweep: Auth0 login not deleted yet: {e!r}")
                continue
            await db.mark_auth0_deleted(conn, user_id)
            deleted += 1
    purged = await db.purge_finished_deletions(conn)
    return SweepResult(logins_deleted=deleted, purged=purged)


async def run_forever(interval_s: float = SWEEP_INTERVAL_S) -> None:
    """sweep_once on a fresh connection every `interval_s`, until cancelled.
    A failed pass (database down) is logged and retried next interval."""
    while True:
        try:
            async with await AsyncConnection.connect(PG_URL, autocommit=True) as conn:
                result = await sweep_once(conn, auth0_management())
            if result.logins_deleted or result.purged:
                print(
                    f"Deletion sweep: {result.logins_deleted} login(s) deleted,"
                    f" {result.purged} record(s) purged"
                )
        except Exception as e:
            print(f"Deletion sweep failed: {e!r}")
        await asyncio.sleep(interval_s)

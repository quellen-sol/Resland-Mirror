"""Finishes account deletions in the background.

DELETE /account commits the erase, records it in account_deletion, then asks
Auth0 to delete the login. If that call fails, or the process dies between the
commit and the call, the login would otherwise survive unnoticed. Every API
process runs this sweep on an interval: it retries the Auth0 deletion for
every row still waiting on it, and drops rows once Auth0 is done and every
session from before the deletion has expired. Auth0 treats deleting an
already-deleted user as done, so overlapping sweeps across replicas are safe.
"""

from dataclasses import dataclass

from ..deps import PgConnection
from .auth0_mgmt import Auth0Management

SWEEP_INTERVAL_S = 600.0


@dataclass
class SweepResult:
    logins_deleted: int
    purged: int


async def sweep_once(conn: PgConnection, auth0: Auth0Management) -> SweepResult:
    """One pass: retry pending Auth0 deletions (skipped when the Management
    API isn't configured), then purge finished rows. Auth0 failures are
    logged and left for the next pass."""
    raise NotImplementedError


async def run_forever(interval_s: float = SWEEP_INTERVAL_S) -> None:
    """sweep_once on a fresh connection every `interval_s`, until cancelled.
    A failed pass (database down) is logged and retried next interval."""
    raise NotImplementedError

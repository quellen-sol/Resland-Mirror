"""Self-serve data export and account deletion.

Deletion order (all inside one transaction holding FOR UPDATE on the user's
row, except the Auth0 step):

1. Lock the row; refuse (409) while a job is in flight.
2. Delete every S3 object under resumes/<auth0_id>/. Losing files early is
   harmless — they're the person's own uploads and regenerable exports — and
   any writer racing us is parked on the row lock, so nothing lands after.
3. Erase the DB rows: billing rows re-pointed to a tombstone, everything else
   deleted child-first along with the LangGraph checkpoint threads.
4. Expire open Stripe Checkout sessions and delete the Stripe customer — last
   before commit, because a failure here still rolls everything back, and the
   customer id is only on the row we're about to delete.
5. Commit.
6. Delete the Auth0 user. Last on purpose: until it's gone the person can
   still sign in and retry, and every step above is idempotent, so a retry
   after any failure finishes the job.
"""

from typing import IO

from shared.s3 import get_s3_client

from ..deps import PgConnection
from ..env_vars import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    S3_RESUME_BUCKET,
    STRIPE_SECRET_KEY,
)
from . import db, model
from .auth0_mgmt import auth0_management

EXPORT_CONTENT_TYPE = "application/zip"
# Spill the archive to disk past this size instead of holding it in memory.
SPOOL_MAX_BYTES = 16 * 1024 * 1024


class StepFailed(Exception):
    """An external system refused part of a deletion. `step` names it."""

    def __init__(self, step: str, cause: Exception):
        super().__init__(f"{step}: {cause}")
        self.step = step
        self.cause = cause


def export_filename(today=None) -> str:
    """resland-data-YYYY-MM-DD.zip"""
    raise NotImplementedError


async def export_account(pg_conn: PgConnection, user_id: str) -> IO[bytes]:
    """Build the export archive; returns a file positioned at its start."""
    raise NotImplementedError


def delete_stripe_customer(customer_id: str, open_checkout_ids: list[str]) -> None:
    """Expire still-payable Checkout sessions, then delete the customer.
    Already-expired/completed sessions and an already-deleted customer are
    fine — the step is idempotent. Blocking (stripe-python)."""
    raise NotImplementedError


async def delete_account(
    pg_conn: PgConnection, user_id: str
) -> model.DeleteAccountResponse:
    raise NotImplementedError

"""Self-serve data export and account deletion.

Deletion order — steps 1-5 run inside one transaction that holds FOR UPDATE
on the user's row, so nothing new can be written for the account meanwhile:

1. Lock the row; refuse (409) while a job is in flight.
2. Delete every S3 object under resumes/<auth0_id>/. Losing files early is
   harmless if a later step fails — they're the person's own uploads and
   regenerable exports — and writers racing us are parked on the row lock.
3. Expire open Stripe Checkout sessions and delete the Stripe customer. Its
   id lives only on the row we're about to delete, so this must happen
   while the row still exists; a failure rolls everything back.
4. Erase the DB rows: billing rows re-pointed to a tombstone, everything else
   deleted child-first along with the LangGraph checkpoint threads.
5. Commit. If anything after step 3 fails, the row is re-pointed away from
   the now-deleted Stripe customer so checkout keeps working.
6. Delete the Auth0 user. Last on purpose: until it's gone the person can
   still sign in and retry, and every step above is idempotent, so a retry
   after any failure finishes the job.
"""

import asyncio
import tempfile
from datetime import UTC, date, datetime
from typing import IO

import stripe
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException
from shared.s3 import get_s3_client

from ..deps import PgConnection
from ..env_vars import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    S3_RESUME_BUCKET,
    STRIPE_SECRET_KEY,
)
from . import archive, db, model, storage
from .auth0_mgmt import Auth0ManagementError, auth0_management

EXPORT_CONTENT_TYPE = "application/zip"
# Spill the archive to disk past this size instead of holding it in memory.
SPOOL_MAX_BYTES = 16 * 1024 * 1024

UNAVAILABLE = "Account deletion isn't available right now. Please try again later."
INCOMPLETE = (
    "We couldn't delete your account just now, and nothing in your profile "
    "was removed. Please try again in a few minutes."
)
LOGIN_REMAINS = (
    "Your Resland data has been deleted, but we couldn't remove your sign-in "
    "yet. Please try again to finish."
)


class StepFailed(Exception):
    """An external system refused part of a deletion. `step` names it."""

    def __init__(self, step: str, cause: Exception):
        super().__init__(f"{step}: {cause}")
        self.step = step
        self.cause = cause


def export_filename(today: date | None = None) -> str:
    """resland-data-YYYY-MM-DD.zip"""
    return f"resland-data-{(today or datetime.now(UTC).date()).isoformat()}.zip"


def _s3():
    return get_s3_client(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


async def export_account(pg_conn: PgConnection, user_id: str) -> IO[bytes]:
    """Build the export archive; returns a file positioned at its start."""
    # One snapshot for every table, so the export is internally consistent.
    async with pg_conn.transaction():
        async with pg_conn.cursor() as cursor:
            await cursor.execute(
                "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
            )
        rows = await db.fetch_export(pg_conn, user_id)

    identity = None
    auth0 = auth0_management()
    if auth0.configured:
        try:
            identity = await auth0.get_user(user_id)
        except Auth0ManagementError as e:
            # Still export everything we hold; the README says what's missing.
            print(f"Export: Auth0 profile unavailable: {e}")

    document = {
        "format_version": model.EXPORT_FORMAT_VERSION,
        "exported_at": datetime.now(UTC).isoformat(),
        "account": rows.pop("account"),
        "login_identity": identity,
        **rows,
    }

    s3 = _s3()
    prefix = storage.user_prefix(user_id)
    # Returned open: the route streams it, then closes it.
    dest = tempfile.SpooledTemporaryFile(max_size=SPOOL_MAX_BYTES)  # noqa: SIM115
    try:
        keys = await asyncio.to_thread(storage.list_keys, s3, S3_RESUME_BUCKET, prefix)
        await asyncio.to_thread(
            archive.write_archive,
            dest,
            data=document,
            s3=s3,
            bucket=S3_RESUME_BUCKET,
            prefix=prefix,
            keys=keys,
            login_identity_included=identity is not None,
        )
    except (storage.StorageError, BotoCoreError, ClientError) as e:
        dest.close()
        print(f"Export: file storage failed: {e}")
        # Never hand out an archive silently missing the person's files.
        raise HTTPException(
            status_code=502,
            detail="We couldn't collect your files just now. Please try again.",
        ) from e
    dest.seek(0)
    return dest


def delete_stripe_customer(customer_id: str, open_checkout_ids: list[str]) -> None:
    """Expire still-payable Checkout sessions, then delete the customer.
    Already-expired/completed sessions and an already-deleted customer are
    fine — the step is idempotent. Blocking (stripe-python)."""
    for session_id in open_checkout_ids:
        try:
            stripe.checkout.Session.expire(session_id)
        except stripe.InvalidRequestError:
            # Already completed or expired — nothing left to pay.
            pass
    try:
        stripe.Customer.delete(customer_id)
    except stripe.InvalidRequestError as e:
        if e.code != "resource_missing":
            raise


def _busy_message(kinds: list[str]) -> str:
    labels = [db.JOB_KIND_LABELS[k] for k in kinds]
    running = (
        labels[0] if len(labels) == 1 else ", ".join(labels[:-1]) + f" and {labels[-1]}"
    )
    return (
        f"Something is still running on your account ({running}). Let it "
        "finish, or dismiss it, then try again."
    )


async def delete_account(
    pg_conn: PgConnection, user_id: str
) -> model.DeleteAccountResponse:
    auth0 = auth0_management()
    if not auth0.configured:
        # Never start erasing data we can't finish erasing.
        print("Account deletion refused: Auth0 Management API not configured")
        raise HTTPException(status_code=503, detail=UNAVAILABLE)

    s3 = _s3()
    prefix = storage.user_prefix(user_id)
    customer_deleted: str | None = None
    try:
        async with pg_conn.transaction():
            account = await db.lock_account(pg_conn, user_id)
            if account:
                busy = await db.in_flight_jobs(pg_conn, user_id)
                if busy:
                    raise HTTPException(status_code=409, detail=_busy_message(busy))
                if account.stripe_customer_id and not STRIPE_SECRET_KEY:
                    print("Account deletion refused: Stripe not configured")
                    raise HTTPException(status_code=503, detail=UNAVAILABLE)

            try:
                await asyncio.to_thread(
                    storage.delete_prefix, s3, S3_RESUME_BUCKET, prefix
                )
            except Exception as e:
                raise StepFailed("file storage", e) from e

            if account and account.stripe_customer_id:
                stripe.api_key = STRIPE_SECRET_KEY
                try:
                    await asyncio.to_thread(
                        delete_stripe_customer,
                        account.stripe_customer_id,
                        account.open_checkout_ids,
                    )
                except Exception as e:
                    raise StepFailed("Stripe", e) from e
                customer_deleted = account.stripe_customer_id

            if account:
                await db.erase_account(pg_conn, user_id)
    except StepFailed as e:
        # The account id stays out of the log: the account may be gone by
        # the time anyone reads it.
        print(f"Account deletion stopped at {e.step}: {e.cause!r}")
        raise HTTPException(status_code=502, detail=INCOMPLETE) from e
    except HTTPException:
        raise
    except BaseException:
        if customer_deleted:
            try:
                await db.forget_stripe_customer(pg_conn, user_id, customer_deleted)
            except Exception as e:
                print(f"Couldn't clear a deleted Stripe customer id: {e!r}")
        raise

    try:
        await auth0.delete_user(user_id)
    except Auth0ManagementError as e:
        print(f"Account deletion stopped at Auth0: {e!r}")
        raise HTTPException(status_code=502, detail=LOGIN_REMAINS) from e
    return model.DeleteAccountResponse()

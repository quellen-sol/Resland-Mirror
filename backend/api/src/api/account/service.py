"""Self-serve data export and account deletion.

Deletion order — steps 1-6 run inside one transaction that holds FOR UPDATE
on the user's row, so nothing new can be written for the account meanwhile:

1. Lock the row; refuse (409) while a job is in flight.
2. Expire still-payable Stripe Checkout sessions, so nobody pays for an
   account that's about to vanish. A checkout that was already paid but
   whose webhook hasn't credited the balance yet refuses (409) instead: the
   person should see that balance before agreeing to forfeit it.
3. Delete every S3 object under resumes/<auth0_id>/. Losing files is
   harmless if a later step fails — they're the person's own uploads and
   regenerable exports — and writers racing us are parked on the row lock.
4. Delete the Stripe customer. Its id lives only on the row we're about to
   delete, so this has to happen while the row still exists.
5. Erase the DB rows: billing rows re-pointed to a tombstone, everything else
   deleted child-first along with the LangGraph checkpoint threads.
6. Commit. If step 5 or the commit fails after step 4, the row is pointed
   away from the now-deleted Stripe customer so checkout keeps working.
7. Delete the Auth0 user. Last on purpose: until it's gone the person can
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
    "We couldn't finish deleting your account, so your profile and history "
    "are still here. Please try again in a few minutes."
)
PAYMENT_SETTLING = (
    "A payment you just made is still being added to your balance. Try again "
    "in a minute, once it shows up."
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


class CheckoutStillSettling(Exception):
    """A Checkout session is paid, but its webhook hasn't credited the
    balance yet."""


def export_filename(today: date | None = None) -> str:
    """resland-data-YYYY-MM-DD.zip"""
    return f"resland-data-{(today or datetime.now(UTC).date()).isoformat()}.zip"


def _s3():
    return get_s3_client(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


async def _login_identity(user_id: str) -> tuple[dict | None, str | None]:
    """(Auth0 profile, README note explaining why it's missing)."""
    auth0 = auth0_management()
    if not auth0.configured:
        return None, archive.IDENTITY_NOT_FETCHED
    try:
        identity = await auth0.get_user(user_id)
    except Auth0ManagementError as e:
        # Still export everything we hold; the README says what's missing.
        print(f"Export: Auth0 profile unavailable: {e}")
        return None, archive.IDENTITY_UNAVAILABLE
    if identity is None:
        return None, archive.IDENTITY_NOT_FOUND
    return identity, None


async def export_account(pg_conn: PgConnection, user_id: str) -> IO[bytes]:
    """Build the export archive; returns a file positioned at its start."""
    # One snapshot for every table, so the export is internally consistent.
    async with pg_conn.transaction():
        async with pg_conn.cursor() as cursor:
            await cursor.execute(
                "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
            )
        rows = await db.fetch_export(pg_conn, user_id)

    identity, identity_note = await _login_identity(user_id)
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
            login_identity_note=identity_note,
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


def expire_open_checkouts(session_ids: list[str]) -> None:
    """Expire still-payable Checkout sessions. Raises CheckoutStillSettling
    for one that's already paid but not yet credited (its row is still
    PENDING). Expired ones, and completed-but-unpaid async payments, are
    left as they are. Blocking (stripe-python)."""
    for session_id in session_ids:
        try:
            stripe.checkout.Session.expire(session_id)
        except stripe.InvalidRequestError:
            # Not open any more: expired, or completed. A paid one whose
            # webhook hasn't landed would credit the balance after the
            # account is gone — make the person wait for it instead.
            session = stripe.checkout.Session.retrieve(session_id)
            if session.status == "complete" and session.payment_status == "paid":
                raise CheckoutStillSettling(session_id) from None


def delete_stripe_customer(customer_id: str) -> None:
    """Delete the Stripe customer; an already-deleted one counts as done.
    Stripe keeps its own payment records. Blocking (stripe-python)."""
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


async def _external(step: str, fn, *args) -> None:
    """Run a blocking external call off the event loop; any failure becomes
    StepFailed(step) so the transaction rolls back and the user can retry."""
    try:
        await asyncio.to_thread(fn, *args)
    except CheckoutStillSettling:
        raise
    except Exception as e:
        raise StepFailed(step, e) from e


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
                uses_stripe = account.stripe_customer_id or account.open_checkout_ids
                if uses_stripe and not STRIPE_SECRET_KEY:
                    print("Account deletion refused: Stripe not configured")
                    raise HTTPException(status_code=503, detail=UNAVAILABLE)
                stripe.api_key = STRIPE_SECRET_KEY

            if account and account.open_checkout_ids:
                await _external(
                    "Stripe checkout", expire_open_checkouts, account.open_checkout_ids
                )

            await _external(
                "file storage", storage.delete_prefix, s3, S3_RESUME_BUCKET, prefix
            )

            if account and account.stripe_customer_id:
                await _external(
                    "Stripe customer",
                    delete_stripe_customer,
                    account.stripe_customer_id,
                )
                customer_deleted = account.stripe_customer_id

            if account:
                await db.erase_account(pg_conn, user_id)
    except CheckoutStillSettling as e:
        raise HTTPException(status_code=409, detail=PAYMENT_SETTLING) from e
    except StepFailed as e:
        # The causes carry no account id (StorageError omits keys), so the
        # log can't outlive the account with it.
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

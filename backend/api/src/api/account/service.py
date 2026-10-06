"""Self-serve data export and account deletion.

Deletion:

0. Before anything else, get an Auth0 Management token and check it carries
   delete:users. A bad secret, a missing scope or the wrong domain is a 503
   with nothing touched — not a login left behind after the data is gone.

Steps 1-6 run in one transaction holding FOR UPDATE on the user's purchase
rows and then their user row (the Stripe webhook's lock order), so nothing new
can be written for the account meanwhile:

1. Lock; refuse (409) while a job is in flight.
2. Expire still-payable Stripe Checkout sessions, so nobody pays for an
   account that's about to vanish. One that Stripe says is already paid but
   the webhook never credited is credited now (through the webhook's own
   path, after rolling back) and the request stops with 409 showing the new
   balance, so the person confirms with the amount they'd really forfeit.
3. Delete the user's S3 files. Losing files is harmless if a later step
   fails — they're the person's own uploads and regenerable exports — and
   writers racing us are parked on the row lock.
4. Delete the Stripe customer. Its id lives only on the row we're about to
   delete, so this has to happen while the row still exists.
5. Erase the DB rows (billing rows re-pointed to a tombstone, everything else
   deleted child-first with the LangGraph threads) and record the deletion
   in account_deletion.
6. Commit. If step 5 or the commit fails after step 4, the row is pointed
   away from the now-deleted Stripe customer so checkout keeps working. A
   deadlock or serialization failure is the same retryable 502 as a failed
   external call.
7. Delete the Auth0 user with the token from step 0. If that fails, or the
   process dies first, the account_deletion row is still there and the
   sweeper (account.sweeper) retries until Auth0 confirms. Meanwhile, and
   until the old sessions have expired, account_deletion makes the API and
   the frontend refuse every session/token of the deleted login, so another
   signed-in device can't rebuild the account.
"""

import asyncio
import tempfile
from datetime import UTC, date, datetime
from typing import IO

import psycopg
import stripe
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException
from shared.s3 import get_s3_client

from ..billing import service as billing_service
from ..deps import PgConnection
from ..env_vars import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    S3_RESUME_BUCKET,
    STRIPE_SECRET_KEY,
)
from . import archive, db, model, storage
from .auth0_mgmt import Auth0ManagementError, Auth0NotReady, auth0_management

# Postgres aborted the transaction to resolve a conflict; retrying is safe.
# (psycopg 3 doesn't group these under TransactionRollback.)
_ROLLED_BACK_BY_DB = (
    psycopg.errors.DeadlockDetected,
    psycopg.errors.SerializationFailure,
    psycopg.errors.TransactionRollback,
)

EXPORT_CONTENT_TYPE = "application/zip"
# Spill the archive to disk past this size instead of holding it in memory.
SPOOL_MAX_BYTES = 16 * 1024 * 1024

UNAVAILABLE = "Account deletion isn't available right now. Please try again later."
INCOMPLETE = (
    "We couldn't finish deleting your account, so your profile and history "
    "are still here. Please try again in a few minutes."
)


class StepFailed(Exception):
    """An external system refused part of a deletion. `step` names it."""

    def __init__(self, step: str, cause: Exception):
        super().__init__(f"{step}: {cause}")
        self.step = step
        self.cause = cause


class CheckoutStillSettling(Exception):
    """A Checkout session is paid, but its webhook hasn't credited the
    balance yet. Carries the Stripe session so it can be credited."""

    def __init__(self, session):
        super().__init__("paid checkout not yet credited")
        self.session = session


def payment_credited_message(balance_cents: float) -> str:
    """The 409 after crediting a paid checkout the webhook never delivered:
    the balance the person is about to forfeit just changed."""
    return (
        "A payment you made hadn't reached your balance yet. It's there now, "
        f"so your balance is ${balance_cents / 100:,.2f}, and deleting your "
        "account would forfeit it. Review it, then confirm again if you still "
        "want to delete your account."
    )


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
    try:
        await auth0.ensure_scopes("read:users")
    except Auth0NotReady as e:
        print(f"Export: Auth0 profile not fetched: {e}")
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
        keys = await asyncio.to_thread(
            storage.list_user_files, s3, S3_RESUME_BUCKET, prefix
        )
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
    PENDING). Expired ones, ones Stripe has never heard of, and
    completed-but-unpaid async payments are left as they are. Blocking
    (stripe-python)."""
    for session_id in session_ids:
        try:
            stripe.checkout.Session.expire(session_id)
            continue
        except stripe.InvalidRequestError as e:
            if e.code == "resource_missing":
                # Not this Stripe account's (e.g. a test-mode leftover):
                # nothing can pay it.
                continue
        # Not open any more: expired, or completed. A paid one the webhook
        # never credited would land on the tombstone after the person
        # agreed to forfeit a smaller balance.
        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.InvalidRequestError as e:
            if e.code == "resource_missing":
                continue
            raise
        if session.status == "complete" and session.payment_status == "paid":
            raise CheckoutStillSettling(session)


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


async def _forget_customer(pg_conn: PgConnection, user_id: str, customer_id) -> None:
    if not customer_id:
        return
    try:
        await db.forget_stripe_customer(pg_conn, user_id, customer_id)
    except Exception as e:
        print(f"Couldn't clear a deleted Stripe customer id: {e!r}")


async def _credit_and_read_balance(
    pg_conn: PgConnection, user_id: str, session
) -> float:
    """Credit a paid checkout the webhook never delivered, the same way the
    webhook would (idempotent), and return the balance it left."""
    payload = session if isinstance(session, dict) else session.to_dict()
    await billing_service.apply_paid_checkout(pg_conn, payload)
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            'SELECT balance_cents FROM "user" WHERE auth0_id = %s', (user_id,)
        )
        row = await res.fetchone()
    return float(row[0]) if row else 0.0


async def delete_account(
    pg_conn: PgConnection, user_id: str
) -> model.DeleteAccountResponse:
    auth0 = auth0_management()
    try:
        # Never start erasing data unless the login can be deleted after.
        await auth0.ensure_scopes("delete:users")
    except Auth0NotReady as e:
        print(f"Account deletion refused: Auth0 Management API not usable: {e}")
        raise HTTPException(status_code=503, detail=UNAVAILABLE) from e

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
                "file storage", storage.delete_user_files, s3, S3_RESUME_BUCKET, prefix
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
            # Commits with the erase, so the login deletion survives a crash
            # right after it (the sweeper picks it up).
            await db.record_deletion(pg_conn, user_id)
    except CheckoutStillSettling as e:
        # Everything above rolled back; nothing was deleted.
        balance = await _credit_and_read_balance(pg_conn, user_id, e.session)
        raise HTTPException(
            status_code=409, detail=payment_credited_message(balance)
        ) from e
    except StepFailed as e:
        # The causes carry no account id (StorageError omits keys), so the
        # log can't outlive the account with it.
        print(f"Account deletion stopped at {e.step}: {e.cause!r}")
        raise HTTPException(status_code=502, detail=INCOMPLETE) from e
    except HTTPException:
        raise
    except _ROLLED_BACK_BY_DB as e:
        # Deadlock or serialization failure: rolled back, safe to retry.
        await _forget_customer(pg_conn, user_id, customer_deleted)
        print(f"Account deletion rolled back by the database: {e!r}")
        raise HTTPException(status_code=502, detail=INCOMPLETE) from e
    except BaseException:
        await _forget_customer(pg_conn, user_id, customer_deleted)
        raise

    try:
        await auth0.delete_user(user_id)
    except Auth0ManagementError as e:
        # The data is gone; the sweeper finishes the login.
        print(f"Account deletion: Auth0 login left for the sweeper: {e!r}")
        return model.DeleteAccountResponse(login_deleted=False)
    try:
        await db.mark_auth0_deleted(pg_conn, user_id)
    except Exception as e:
        # The sweeper re-deletes (404 counts as done) and marks it.
        print(f"Account deletion: couldn't record the Auth0 deletion: {e!r}")
    return model.DeleteAccountResponse(login_deleted=True)

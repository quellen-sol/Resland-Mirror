"""SQL for account export and deletion.

Every function here runs inside a transaction the caller owns, so the
deletion's row lock spans its whole sequence (see service.delete_account).
"""

from dataclasses import dataclass
from typing import Any

from ..deps import PgConnection

# Child-first deletion order for the tables holding a user's rows. Tables
# owned through a parent (bullets via experience, transcript via session)
# come right before that parent; user_suggestion goes before the experience
# and bullet rows it references. A live-schema test checks this list against
# every foreign key that leads back to "user".
ERASED_TABLES = (
    "system_design_message",
    "user_system_design_session",
    "user_suggestion",
    "user_base_experience_bullet",
    "user_base_experience",
    "user_base_skill",
    "user_base_education",
    "user_base_project",
    "user_social_link",
    "user_tailored_resume",
    "user_tailor_run",
    "user_resume_format",
    "user_generated_resume",
    "user_upload_job",
    "user_dsa_progress",
)

# Billing ledger: kept for accounting, re-pointed at a tombstone user.
REPOINTED_TABLES = ("balance_purchase", "token_usage")

# Tables whose ids are LangGraph thread ids (langgraph.* checkpoints).
THREAD_TABLES = (
    "user_suggestion",
    "user_tailor_run",
    "user_system_design_session",
)

# A resume upload still PENDING/PROCESSING after this long has crashed (the
# dispatcher drops a job whose account is gone), so it can't block deletion
# forever. Sessions have no such window: the user can dismiss a stuck one.
STALE_UPLOAD_INTERVAL = "30 minutes"

# in_flight_jobs() kinds, worded for the 409 message.
JOB_KIND_LABELS = {
    "resume_upload": "resume upload",
    "suggestion": "bullet suggestion",
    "tailor_run": "tailoring run",
    "system_design": "System Design Mock turn",
}


@dataclass
class LockedAccount:
    stripe_customer_id: str | None
    balance_cents: float
    # Stripe Checkout session ids of PENDING purchases — still payable until
    # they're expired.
    open_checkout_ids: list[str]


async def lock_account(conn: PgConnection, user_id: str) -> LockedAccount | None:
    """Take FOR UPDATE on the user's row for the rest of the transaction and
    read what deletion needs. None when there's no row.

    The lock serializes deletion against everything that adds work for the
    user: inserts into user-owned tables take FOR KEY SHARE on this row via
    their foreign key, and the paths that flip an existing row back to
    PROCESSING take it explicitly (api.user_row.share_user_row)."""
    raise NotImplementedError


async def in_flight_jobs(conn: PgConnection, user_id: str) -> list[str]:
    """Kinds (keys of JOB_KIND_LABELS) of work the dispatcher may still be
    doing for the user. WAITING_FOR_INPUT/COMPLETED/FAILED rows are idle."""
    raise NotImplementedError


async def erase_account(conn: PgConnection, user_id: str) -> str | None:
    """Delete everything the user owns, inside the caller's transaction:
    re-point billing rows at a fresh tombstone (only when there are any),
    delete every ERASED_TABLES row child-first along with the LangGraph
    checkpoint threads of their sessions/runs, then the user row.

    Returns the tombstone id, or None when no billing rows existed."""
    raise NotImplementedError


async def forget_stripe_customer(
    conn: PgConnection, user_id: str, customer_id: str
) -> None:
    """Null user.stripe_customer_id if it still names `customer_id` — used
    when the Stripe customer was deleted but the rest of the deletion rolled
    back, so a later checkout makes a fresh customer instead of failing."""
    raise NotImplementedError


async def fetch_export(conn: PgConnection, user_id: str) -> dict[str, Any]:
    """Every row the user owns, shaped per model.EXPORT_SECTIONS — the body
    of data.json minus the archive metadata. JSON-safe values only."""
    raise NotImplementedError

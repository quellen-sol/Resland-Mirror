"""SQL for account export and deletion.

Every function here runs inside a transaction the caller owns, so the
deletion's row lock spans its whole sequence (see service.delete_account).
"""

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from shared.accounts import new_tombstone_id
from shared.checkpoints import CHECKPOINT_TABLES, THREAD_OWNER_TABLES

from ..deps import PgConnection
from ..resume_upload.model import STALE_UPLOAD_INTERVAL
from .model import (
    ACCOUNT_COLUMNS,
    BULLET_COLUMNS,
    EXPORT_SECTIONS,
    MESSAGE_COLUMNS,
    PROFILE_COLUMNS,
    SINGLETON_SECTIONS,
    ExportSection,
)

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

# Uploads past STALE_UPLOAD_INTERVAL don't block deletion: they crashed (the
# dispatcher drops a job whose account is gone). Sessions have no such
# window: the user can dismiss a stuck one.

# How long an account_deletion row outlives the Auth0 login it records: the
# frontend's absolute session lifetime (3 days, nextjs-auth0's default), which
# also covers Auth0's default 24-hour access tokens. Raise it if either grows.
REVOCATION_WINDOW = "3 days"

# in_flight_jobs() kinds, worded for the 409 message.
JOB_KIND_LABELS = {
    "resume_upload": "resume upload",
    "suggestion": "bullet suggestion",
    "tailor_run": "tailoring run",
    "system_design": "System Design Mock turn",
}

# Rows reached through a parent rather than a user_id column.
_ERASE_VIA_PARENT = {
    "system_design_message": (
        "DELETE FROM system_design_message WHERE session_id IN ("
        " SELECT id FROM user_system_design_session WHERE user_id = %s)"
    ),
    "user_base_experience_bullet": (
        "DELETE FROM user_base_experience_bullet WHERE user_experience_id IN ("
        " SELECT id FROM user_base_experience WHERE user_id = %s)"
    ),
}


@dataclass
class LockedAccount:
    stripe_customer_id: str | None
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
    async with conn.cursor() as cursor:
        res = await cursor.execute(
            'SELECT stripe_customer_id FROM "user" WHERE auth0_id = %s FOR UPDATE',
            (user_id,),
        )
        row = await res.fetchone()
        if not row:
            return None
        res = await cursor.execute(
            """
            SELECT id FROM balance_purchase
            WHERE user_id = %s AND status = 'PENDING' ORDER BY created_at
            """,
            (user_id,),
        )
        open_ids = [r[0] for r in await res.fetchall()]
    return LockedAccount(stripe_customer_id=row[0], open_checkout_ids=open_ids)


async def in_flight_jobs(conn: PgConnection, user_id: str) -> list[str]:
    """Kinds (keys of JOB_KIND_LABELS) of work the dispatcher may still be
    doing for the user. WAITING_FOR_INPUT/COMPLETED/FAILED rows are idle."""
    async with conn.cursor() as cursor:
        res = await cursor.execute(
            """
            SELECT 'resume_upload' FROM user_upload_job
            WHERE user_id = %s AND status IN ('PENDING', 'PROCESSING')
              AND created_at > now() - %s::interval
            UNION
            SELECT 'suggestion' FROM user_suggestion
            WHERE user_id = %s AND status = 'PROCESSING'
            UNION
            SELECT 'tailor_run' FROM user_tailor_run
            WHERE user_id = %s AND status = 'PROCESSING'
            UNION
            SELECT 'system_design' FROM user_system_design_session
            WHERE user_id = %s AND status = 'PROCESSING'
            """,
            (user_id, STALE_UPLOAD_INTERVAL, user_id, user_id, user_id),
        )
        busy = {r[0] for r in await res.fetchall()}
    return [kind for kind in JOB_KIND_LABELS if kind in busy]


async def _delete_threads(cursor, thread_ids: list[str]) -> None:
    """Drop LangGraph checkpoint threads. The tables only exist once a
    dispatcher has run its setup, so a missing table is skipped."""
    if not thread_ids:
        return
    for table in CHECKPOINT_TABLES:
        res = await cursor.execute("SELECT to_regclass(%s)", (table,))
        exists = await res.fetchone()
        if exists and exists[0]:
            await cursor.execute(
                f"DELETE FROM {table} WHERE thread_id = ANY(%s)", (thread_ids,)
            )


async def erase_account(conn: PgConnection, user_id: str) -> str | None:
    """Delete everything the user owns, inside the caller's transaction:
    re-point billing rows at a fresh tombstone (only when there are any),
    delete every ERASED_TABLES row child-first along with the LangGraph
    checkpoint threads of their sessions/runs, then the user row.

    Returns the tombstone id, or None when no billing rows existed."""
    async with conn.cursor() as cursor:
        thread_ids: list[str] = []
        for table in THREAD_OWNER_TABLES:
            res = await cursor.execute(
                f"SELECT id FROM {table} WHERE user_id = %s", (user_id,)
            )
            thread_ids.extend(r[0] for r in await res.fetchall())

        tombstone = None
        res = await cursor.execute(
            """
            SELECT EXISTS (SELECT 1 FROM balance_purchase WHERE user_id = %s)
                OR EXISTS (SELECT 1 FROM token_usage WHERE user_id = %s)
            """,
            (user_id, user_id),
        )
        if (await res.fetchone())[0]:
            # A bare row: no name, contact details, balance, Stripe link or
            # admin flag — just something for the ledger to point at.
            tombstone = new_tombstone_id()
            await cursor.execute(
                'INSERT INTO "user" (auth0_id) VALUES (%s)', (tombstone,)
            )
            for table in REPOINTED_TABLES:
                await cursor.execute(
                    f"UPDATE {table} SET user_id = %s WHERE user_id = %s",
                    (tombstone, user_id),
                )

        for table in ERASED_TABLES:
            await cursor.execute(
                _ERASE_VIA_PARENT.get(table, f"DELETE FROM {table} WHERE user_id = %s"),
                (user_id,),
            )
        await _delete_threads(cursor, thread_ids)
        await cursor.execute('DELETE FROM "user" WHERE auth0_id = %s', (user_id,))
    return tombstone


async def token_revoked(
    conn: PgConnection, user_id: str, issued_at: float | None
) -> bool:
    """True when a session or token for `user_id` belongs to an account that
    was deleted: while Auth0 still has the old login (auth0_deleted_at is
    null) every one does; after that, those issued at or before the moment
    Auth0 deleted it. A sign-up after that, even with the same social login
    (same sub), is a new account and passes. `issued_at` is epoch seconds
    (a token's iat, a session's createdAt); None counts as old."""
    raise NotImplementedError


async def mark_auth0_deleted(conn: PgConnection, user_id: str) -> None:
    """Record that Auth0 confirmed the login is deleted."""
    raise NotImplementedError


async def pending_auth0_deletions(conn: PgConnection) -> list[str]:
    """Deleted accounts whose Auth0 login hasn't been deleted yet."""
    raise NotImplementedError


async def purge_finished_deletions(conn: PgConnection) -> int:
    """Drop account_deletion rows whose Auth0 login has been gone longer than
    REVOCATION_WINDOW — every session from before has expired by then.
    Returns how many were dropped."""
    raise NotImplementedError


async def forget_stripe_customer(
    conn: PgConnection, user_id: str, customer_id: str
) -> None:
    """Null user.stripe_customer_id if it still names `customer_id` — used
    when the Stripe customer was deleted but the rest of the deletion rolled
    back, so a later checkout makes a fresh customer instead of failing."""
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            UPDATE "user" SET stripe_customer_id = NULL
            WHERE auth0_id = %s AND stripe_customer_id = %s
            """,
            (user_id, customer_id),
        )


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _decode(raw: Any) -> Any:
    """JSON stored as text, decoded so the export nests; kept as the raw
    string if it doesn't parse."""
    if not isinstance(raw, str):
        return raw
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def _row(columns: tuple[str, ...], row: tuple, json_columns=()) -> dict[str, Any]:
    out = {}
    for column, value in zip(columns, row, strict=True):
        out[column] = _decode(value) if column in json_columns else _json_value(value)
    return out


async def _section_rows(cursor, section: ExportSection, user_id: str) -> list[dict]:
    res = await cursor.execute(
        f"SELECT {', '.join(section.columns)} FROM {section.table}"
        f" WHERE user_id = %s ORDER BY {section.order_by}",
        (user_id,),
    )
    return [
        _row(section.columns, r, section.json_columns) for r in await res.fetchall()
    ]


async def fetch_export(conn: PgConnection, user_id: str) -> dict[str, Any]:
    """Every row the user owns, shaped per model.EXPORT_SECTIONS — the body
    of data.json minus the archive metadata. JSON-safe values only."""
    async with conn.cursor() as cursor:
        user_columns = ACCOUNT_COLUMNS + PROFILE_COLUMNS
        res = await cursor.execute(
            f'SELECT {", ".join(user_columns)} FROM "user" WHERE auth0_id = %s',
            (user_id,),
        )
        row = await res.fetchone()
        values = _row(user_columns, row) if row else None
        data: dict[str, Any] = {
            "account": ({c: values[c] for c in ACCOUNT_COLUMNS} if values else None),
            "profile": ({c: values[c] for c in PROFILE_COLUMNS} if values else None),
        }

        for section in EXPORT_SECTIONS:
            rows = await _section_rows(cursor, section, user_id)
            if section.key in SINGLETON_SECTIONS:
                data[section.key] = rows[0] if rows else None
            else:
                data[section.key] = rows

        bullets: dict[int, list[dict]] = {}
        if data["experiences"]:
            res = await cursor.execute(
                f"SELECT user_experience_id, {', '.join(BULLET_COLUMNS)}"
                " FROM user_base_experience_bullet"
                " WHERE user_experience_id = ANY(%s)"
                " ORDER BY user_experience_id, bullet_order, id",
                ([e["id"] for e in data["experiences"]],),
            )
            for r in await res.fetchall():
                bullets.setdefault(r[0], []).append(_row(BULLET_COLUMNS, r[1:]))
        for exp in data["experiences"]:
            exp["bullets"] = bullets.get(exp["id"], [])

        messages: dict[str, list[dict]] = {}
        if data["system_design_sessions"]:
            res = await cursor.execute(
                f"SELECT session_id, {', '.join(MESSAGE_COLUMNS)}"
                " FROM system_design_message WHERE session_id = ANY(%s)"
                " ORDER BY session_id, id",
                ([s["id"] for s in data["system_design_sessions"]],),
            )
            for r in await res.fetchall():
                messages.setdefault(r[0], []).append(_row(MESSAGE_COLUMNS, r[1:]))
        for session in data["system_design_sessions"]:
            session["messages"] = messages.get(session["id"], [])
    return data

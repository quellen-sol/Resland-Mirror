"""Account export + deletion against a live Postgres (TEST_PG_URL), with fake
S3 / Stripe / Auth0. Proves, among other things:

- no row anywhere still names the deleted account or carries its PII;
- billing rows survive, re-pointed at one PII-free tombstone;
- the account's LangGraph checkpoint threads are gone, others untouched;
- S3 deletes covered the whole resumes/<id>/ prefix across pages, and nothing
  outside it;
- each external failure leaves a state a retry can finish;
- the row lock serializes deletion against job submission and exports.

Run: .venv/bin/python -m pytest backend/api/tests/test_account_pg.py -v
"""

import asyncio
import io
import json
import zipfile

import psycopg
import pytest
import stripe
from fastapi import HTTPException
from psycopg.errors import ForeignKeyViolation
from shared.accounts import is_tombstone_id
from shared.checkpoints import CHECKPOINT_TABLES

from api.account import db as account_db
from api.account import service
from api.account.auth0_mgmt import Auth0ManagementError
from api.account.model import EXPORT_SECTIONS
from api.admin import service as admin_service
from api.billing import service as billing_service
from api.bullet_point_sugg import model as sugg_model
from api.bullet_point_sugg import service as sugg_service
from api.resume_export import service as export_service
from api.resume_upload import service as upload_service
from api.system_design import model as sd_model
from api.system_design import service as sd_service
from api.tailor import model as tailor_model
from api.tailor import service as tailor_service

from .conftest import TEST_PG_URL
from .helpers import FakeAuth0, FakeS3, _Amqp

USER = "google-oauth2|111"
# Its id extends USER's, so its S3 prefix and its id both start with USER's —
# the deletion must match exactly, never by prefix.
OTHER = "google-oauth2|1112"
BUCKET = "test-bucket"


def pii(tag):
    """Personal text seeded for one user — distinct per tag, so a scan for
    one user's values never matches the other's."""
    return {
        "name": f"Jane {tag}",
        "email": f"jane.{tag}@example.com",
        "phone": f"+1 555 {tag} 0100",
        "location": f"Brooklyn ({tag})",
        "summary": f"Distributed systems engineer ({tag})",
        "job": f"Senior Engineer at Initech ({tag})",
        "answer": f"My private interview answer ({tag})",
        "bullet": f"Scaled the payments ledger ({tag})",
    }


# Fixtures ---------------------------------------------------------------


@pytest.fixture
async def checkpoint_tables(pg):
    """The langgraph checkpoint tables: the dispatcher's own when a
    dispatcher already set them up, else minimal stand-ins dropped again
    afterwards so a later dispatcher setup() starts clean."""
    res = await pg.execute("SELECT to_regclass('langgraph.checkpoints')")
    existed = (await res.fetchone())[0] is not None
    if not existed:
        await pg.execute(
            """
            CREATE SCHEMA IF NOT EXISTS langgraph;
            CREATE TABLE langgraph.checkpoints (
                thread_id text NOT NULL, checkpoint_ns text NOT NULL DEFAULT '',
                checkpoint_id text NOT NULL, checkpoint jsonb NOT NULL,
                metadata jsonb NOT NULL DEFAULT '{}');
            CREATE TABLE langgraph.checkpoint_blobs (
                thread_id text NOT NULL, checkpoint_ns text NOT NULL DEFAULT '',
                channel text NOT NULL, version text NOT NULL, type text NOT NULL,
                blob bytea);
            CREATE TABLE langgraph.checkpoint_writes (
                thread_id text NOT NULL, checkpoint_ns text NOT NULL DEFAULT '',
                checkpoint_id text NOT NULL, task_id text NOT NULL,
                idx integer NOT NULL, channel text NOT NULL, type text,
                blob bytea NOT NULL, task_path text NOT NULL DEFAULT '');
            """
        )
    for table in CHECKPOINT_TABLES:
        await pg.execute(f"DELETE FROM {table}")
    yield
    if existed:
        for table in CHECKPOINT_TABLES:
            await pg.execute(f"DELETE FROM {table}")
    else:
        await pg.execute(
            "DROP TABLE langgraph.checkpoints, langgraph.checkpoint_blobs,"
            " langgraph.checkpoint_writes"
        )


@pytest.fixture
def externals(monkeypatch):
    """Fake S3 + Auth0 + Stripe wired into the account service."""
    s3 = FakeS3(page_size=1000)
    auth0 = FakeAuth0(profile={"user_id": USER, "email": "jane@login.example"})
    stripe_calls = []

    def expire(session_id):
        stripe_calls.append(("expire", session_id))

    def delete(customer_id):
        stripe_calls.append(("delete", customer_id))

    monkeypatch.setattr(stripe.checkout.Session, "expire", expire)
    monkeypatch.setattr(stripe.Customer, "delete", delete)
    monkeypatch.setattr(service, "get_s3_client", lambda **_kw: s3)
    monkeypatch.setattr(service, "auth0_management", lambda: auth0)
    monkeypatch.setattr(service, "S3_RESUME_BUCKET", BUCKET)
    monkeypatch.setattr(service, "STRIPE_SECRET_KEY", "sk_test_x")

    class Externals:
        pass

    ext = Externals()
    ext.s3, ext.auth0, ext.stripe_calls = s3, auth0, stripe_calls
    return ext


# Seeding ----------------------------------------------------------------


async def _one(pg, query, params=()):
    res = await pg.execute(query, params)
    return await res.fetchone()


async def _all(pg, query, params=()):
    res = await pg.execute(query, params)
    return await res.fetchall()


async def seed_user(pg, uid, *, tag="alpha", stripe_customer="cus_1"):
    """A user with a row in every user-owned table. Ids and personal text
    are derived from `tag` so two seeded users never collide."""
    t = tag
    p = pii(tag)
    await pg.execute(
        """
        INSERT INTO "user" (auth0_id, has_onboarded, balance_cents, site_admin,
            stripe_customer_id, full_name, email, phone, location, summary)
        VALUES (%s, true, 12.5, true, %s, %s, %s, %s, %s, %s)
        """,
        (
            uid,
            stripe_customer,
            p["name"],
            p["email"],
            p["phone"],
            p["location"],
            p["summary"],
        ),
    )
    await pg.execute(
        "INSERT INTO user_social_link (user_id, link, type)"
        " VALUES (%s, 'https://linkedin.com/in/jane', 'LINKEDIN')",
        (uid,),
    )
    await pg.execute(
        "INSERT INTO user_upload_job (id, user_id, s3_key, status)"
        " VALUES (%s, %s, %s, 'COMPLETED')",
        (f"job-{t}", uid, f"resumes/{uid}/resume_doc.docx"),
    )
    exp = (
        await _one(
            pg,
            "INSERT INTO user_base_experience (user_id, company_name, title,"
            " start_date) VALUES (%s, 'Initech', 'Engineer', '2020') RETURNING id",
            (uid,),
        )
    )[0]
    bullet = (
        await _one(
            pg,
            "INSERT INTO user_base_experience_bullet (user_experience_id, bullet,"
            " bullet_order) VALUES (%s, %s, 0) RETURNING id",
            (exp, p["bullet"]),
        )
    )[0]
    await pg.execute(
        "INSERT INTO user_base_experience_bullet (user_experience_id, bullet,"
        " bullet_order) VALUES (%s, 'Cut p99 latency', 1)",
        (exp,),
    )
    await pg.execute(
        "INSERT INTO user_base_skill (user_id, name, category) VALUES (%s, 'Go', 'Langs')",
        (uid,),
    )
    await pg.execute(
        "INSERT INTO user_base_education (user_id, institution, degree,"
        " field_of_study, start_date) VALUES (%s, 'MIT', 'BS', 'CS', '2016')",
        (uid,),
    )
    await pg.execute(
        "INSERT INTO user_base_project (user_id, name, start_date)"
        " VALUES (%s, 'Ledger', '2021')",
        (uid,),
    )
    sugg = f"sugg-{t}"
    await pg.execute(
        "INSERT INTO user_suggestion (id, user_id, experience_id, bullet_id,"
        " status, pending_question, result) VALUES (%s, %s, %s, %s,"
        " 'WAITING_FOR_INPUT', 'How many users?', %s)",
        (sugg, uid, exp, bullet, json.dumps([{"bullet_id": bullet, "options": ["a"]}])),
    )
    run = f"run-{t}"
    await pg.execute(
        "INSERT INTO user_tailor_run (id, user_id, job_description, company_name,"
        " status, result) VALUES (%s, %s, %s, 'Initech',"
        " 'COMPLETED', '{\"summary\": \"Tailored\"}')",
        (run, uid, p["job"]),
    )
    await pg.execute(
        "INSERT INTO user_tailored_resume (id, user_id, tailor_run_id,"
        " job_description, content, s3_key, source_hash) VALUES (%s, %s, %s,"
        " %s, '{\"summary\": \"Tailored\"}', %s, 'h')",
        (f"tr-{t}", uid, run, p["job"], f"resumes/{uid}/tailored/tr-{t}.docx"),
    )
    await pg.execute(
        "INSERT INTO user_resume_format (user_id, format) VALUES (%s, '{\"columns\": 1}')",
        (uid,),
    )
    await pg.execute(
        "INSERT INTO user_generated_resume (user_id, s3_key, source_hash)"
        " VALUES (%s, %s, 'h')",
        (uid, f"resumes/{uid}/generated.docx"),
    )
    await pg.execute(
        "INSERT INTO token_usage (user_id, job_kind, job_id, model, input_tokens,"
        " output_tokens, amount_cents, actual_cost_cents, openrouter_generation_ids)"
        " VALUES (%s, 'TAILOR', %s, 'openrouter:m', 100, 50, 2.5, 2.0, %s),"
        "        (%s, 'SUGGESTION', %s, 'openrouter:m', 10, 5, 0.5, NULL, '{}')",
        (uid, f"{run}:t1", ["gen-1"], uid, f"{sugg}:t1"),
    )
    sd = f"sd-{t}"
    await pg.execute(
        "INSERT INTO user_system_design_session (id, user_id, source, problem_id,"
        " job_description, status, brief, agent_context, diagram, phase_durations,"
        " result) VALUES (%s, %s, 'JOB', NULL, %s,"
        " 'WAITING_FOR_INPUT', '{\"secret\": \"brief\"}', '{\"ctx\": 1}',"
        " '[{\"id\": \"box\"}]', '{\"REQUIREMENTS\": 60}', NULL)",
        (sd, uid, p["job"]),
    )
    await pg.execute(
        "INSERT INTO system_design_message (session_id, role, phase, content)"
        " VALUES (%s, 'INTERVIEWER', 'REQUIREMENTS', 'What are the requirements?'),"
        "        (%s, 'CANDIDATE', 'REQUIREMENTS', %s)",
        (sd, sd, p["answer"]),
    )
    await pg.execute(
        "INSERT INTO balance_purchase (id, user_id, cents, amount_cents, currency,"
        " status, payment_intent_id) VALUES"
        " (%s, %s, 1100, 1000, 'usd', 'COMPLETED', %s),"
        " (%s, %s, 500, 500, 'usd', 'PENDING', NULL)",
        (f"cs_paid_{t}", uid, f"pi_{t}", f"cs_open_{t}", uid),
    )
    await pg.execute(
        "INSERT INTO user_dsa_progress (user_id, topic) VALUES (%s, 'two-pointers')",
        (uid,),
    )
    return {
        "experience": exp,
        "bullet": bullet,
        "suggestion": sugg,
        "tailor_run": run,
        "system_design": sd,
        "threads": [sugg, run, sd],
        "open_checkout": f"cs_open_{t}",
        "paid_checkout": f"cs_paid_{t}",
    }


async def seed_checkpoints(pg, thread_ids):
    for thread in thread_ids:
        await pg.execute(
            "INSERT INTO langgraph.checkpoints (thread_id, checkpoint_ns,"
            " checkpoint_id, checkpoint, metadata) VALUES (%s, '', 'c1', '{}', '{}')",
            (thread,),
        )
        await pg.execute(
            "INSERT INTO langgraph.checkpoint_blobs (thread_id, checkpoint_ns,"
            " channel, version, type) VALUES (%s, '', 'messages', '1', 'empty')",
            (thread,),
        )
        await pg.execute(
            "INSERT INTO langgraph.checkpoint_writes (thread_id, checkpoint_ns,"
            " checkpoint_id, task_id, idx, channel, blob)"
            " VALUES (%s, '', 'c1', 't1', 0, 'messages', '')",
            (thread,),
        )


def seed_files(s3, uid, n_tailored=0):
    s3.objects[f"resumes/{uid}/resume_doc.docx"] = b"original docx"
    s3.objects[f"resumes/{uid}/resume_doc.pdf"] = b"%PDF original"
    s3.objects[f"resumes/{uid}/generated.docx"] = b"generated"
    for i in range(n_tailored):
        s3.objects[f"resumes/{uid}/tailored/{i:05}.docx"] = b"tailored"


# Schema introspection ---------------------------------------------------


async def tables_reaching_user(pg) -> set[str]:
    """Every public table with a foreign-key path to "user" — today's
    contract or any table added later."""
    rows = await _all(
        pg,
        """
        WITH RECURSIVE fk AS (
            SELECT c.conrelid::regclass::text AS child,
                   c.confrelid::regclass::text AS parent
            FROM pg_constraint c
            WHERE c.contype = 'f'
              AND c.connamespace = 'public'::regnamespace
        ), reach AS (
            SELECT child FROM fk WHERE parent = '"user"'
            UNION
            SELECT fk.child FROM fk JOIN reach ON fk.parent = reach.child
        )
        SELECT child FROM reach
        """,
    )
    return {r[0].strip('"') for r in rows}


async def rows_mentioning(pg, needle: str) -> dict[str, int]:
    """{table: n} for every public table with a row whose text form contains
    `needle` — catches PII in any column, including ones added later."""
    tables = [
        r[0]
        for r in await _all(
            pg,
            "SELECT quote_ident(tablename) FROM pg_tables WHERE schemaname = 'public'",
        )
    ]
    found = {}
    for table in tables:
        n = (
            await _one(
                pg,
                f"SELECT count(*) FROM {table} t WHERE t::text LIKE %s",
                (f"%{needle}%",),
            )
        )[0]
        if n:
            found[table] = n
    return found


async def rows_naming(pg, uid: str) -> dict[str, int]:
    """rows_mentioning for an account id, matched as a whole value — row
    text ends a value with `,` or `)`, a key path with `/`, JSON with `"`."""
    found: dict[str, int] = {}
    for end in (",", ")", "/", '"'):
        for table, n in (await rows_mentioning(pg, uid + end)).items():
            found[table] = found.get(table, 0) + n
    return found


async def thread_rows(pg, thread_ids) -> int:
    total = 0
    for table in CHECKPOINT_TABLES:
        total += (
            await _one(
                pg,
                f"SELECT count(*) FROM {table} WHERE thread_id = ANY(%s)",
                (list(thread_ids),),
            )
        )[0]
    return total


async def test_every_table_reaching_user_is_erased_or_repointed(pg):
    expected = set(account_db.ERASED_TABLES) | set(account_db.REPOINTED_TABLES)
    assert await tables_reaching_user(pg) == expected


async def test_every_table_reaching_user_is_exported(pg):
    exported = {s.table for s in EXPORT_SECTIONS} | {
        "user_base_experience_bullet",
        "system_design_message",
    }
    assert await tables_reaching_user(pg) == exported


# Deletion: the happy path ------------------------------------------------


async def test_delete_erases_every_trace(pg, checkpoint_tables, externals):
    mine = await seed_user(pg, USER)
    theirs = await seed_user(pg, OTHER, tag="beta", stripe_customer="cus_other")
    await seed_checkpoints(pg, mine["threads"] + theirs["threads"])
    seed_files(externals.s3, USER, n_tailored=2500)  # 3 list pages
    seed_files(externals.s3, OTHER)
    their_files = {k for k in externals.s3.objects if k.startswith(f"resumes/{OTHER}/")}

    resp = await service.delete_account(pg, USER)
    assert resp.ok is True

    # No row in any table still carries the person or their PII…
    assert await rows_naming(pg, USER) == {}
    for needle in pii("alpha").values():
        assert await rows_mentioning(pg, needle) == {}, needle
    for table in await tables_reaching_user(pg):
        if table in ("user_base_experience_bullet", "system_design_message"):
            continue
        n = (
            await _one(pg, f"SELECT count(*) FROM {table} WHERE user_id = %s", (USER,))
        )[0]
        assert n == 0, table
    assert (
        await _one(
            pg,
            "SELECT count(*) FROM user_base_experience_bullet WHERE user_experience_id = %s",
            (mine["experience"],),
        )
    )[0] == 0
    assert (
        await _one(
            pg,
            "SELECT count(*) FROM system_design_message WHERE session_id = %s",
            (mine["system_design"],),
        )
    )[0] == 0

    # …billing rows survive on one PII-free tombstone…
    owners = {
        r[0]
        for r in await _all(
            pg,
            "SELECT user_id FROM balance_purchase WHERE id = ANY(%s)"
            " UNION ALL SELECT user_id FROM token_usage WHERE job_id = ANY(%s)",
            (
                [mine["paid_checkout"], mine["open_checkout"]],
                [f"{mine['tailor_run']}:t1", f"{mine['suggestion']}:t1"],
            ),
        )
    }
    assert len(owners) == 1
    (tomb,) = owners
    assert is_tombstone_id(tomb)
    tomb_row = await _one(
        pg,
        'SELECT full_name, email, phone, location, summary, balance_cents,'
        ' site_admin, stripe_customer_id, has_onboarded FROM "user"'
        " WHERE auth0_id = %s",
        (tomb,),
    )
    assert tomb_row == (None, None, None, None, None, 0, False, None, False)
    usage_count = (
        await _one(pg, "SELECT count(*) FROM token_usage WHERE user_id = %s", (tomb,))
    )[0]
    assert usage_count == 2

    # …the account's checkpoint threads are gone, the other user's kept…
    assert await thread_rows(pg, mine["threads"]) == 0
    assert await thread_rows(pg, theirs["threads"]) == 3 * len(theirs["threads"])

    # …S3: the whole prefix, across pages, and nothing else.
    assert not [k for k in externals.s3.objects if k.startswith(f"resumes/{USER}/")]
    assert set(externals.s3.objects) == their_files
    deleted = [k for batch in externals.s3.delete_calls for k in batch]
    assert len(deleted) == 2503
    assert all(k.startswith(f"resumes/{USER}/") for k in deleted)

    # Stripe: the open checkout expired, then the customer deleted.
    assert externals.stripe_calls == [
        ("expire", mine["open_checkout"]),
        ("delete", "cus_1"),
    ]
    # Auth0 last.
    assert externals.auth0.deleted == [USER]

    # The other account is untouched.
    other = await _one(
        pg, 'SELECT full_name, stripe_customer_id FROM "user" WHERE auth0_id = %s', (OTHER,)
    )
    assert other == (pii("beta")["name"], "cus_other")
    assert await rows_mentioning(pg, pii("beta")["answer"]) == {
        "system_design_message": 1
    }
    for table in ("user_suggestion", "user_tailor_run", "user_system_design_session"):
        n = (
            await _one(pg, f"SELECT count(*) FROM {table} WHERE user_id = %s", (OTHER,))
        )[0]
        assert n == 1, table


async def test_delete_without_billing_makes_no_tombstone(pg, checkpoint_tables, externals):
    await pg.execute('INSERT INTO "user" (auth0_id, full_name) VALUES (%s, %s)', (USER, "Jane"))
    await service.delete_account(pg, USER)
    assert await _one(pg, 'SELECT count(*) FROM "user"') == (0,)
    assert externals.stripe_calls == []
    assert externals.auth0.deleted == [USER]


async def test_delete_works_before_any_dispatcher_made_checkpoint_tables(
    pg, externals
):
    # Park an existing langgraph schema under another name for the test.
    res = await pg.execute("SELECT to_regnamespace('langgraph')")
    parked = (await res.fetchone())[0] is not None
    if parked:
        await pg.execute("ALTER SCHEMA langgraph RENAME TO langgraph_parked_by_test")
    try:
        await seed_user(pg, USER)
        await service.delete_account(pg, USER)
        assert await rows_naming(pg, USER) == {}
    finally:
        if parked:
            await pg.execute(
                "ALTER SCHEMA langgraph_parked_by_test RENAME TO langgraph"
            )


async def test_delete_with_no_user_row_still_clears_files_and_login(
    pg, checkpoint_tables, externals
):
    seed_files(externals.s3, USER)
    await service.delete_account(pg, USER)
    assert externals.s3.objects == {}
    assert externals.auth0.deleted == [USER]


async def test_repeating_a_finished_deletion_succeeds(pg, checkpoint_tables, externals):
    await seed_user(pg, USER)
    await service.delete_account(pg, USER)
    await service.delete_account(pg, USER)
    assert externals.auth0.deleted == [USER, USER]
    tombstones = (
        await _one(pg, "SELECT count(*) FROM \"user\" WHERE auth0_id LIKE 'deleted|%'")
    )[0]
    assert tombstones == 1


# Deletion: in-flight jobs --------------------------------------------------


@pytest.mark.parametrize(
    "table, status, kind",
    [
        ("user_suggestion", "PROCESSING", "suggestion"),
        ("user_tailor_run", "PROCESSING", "tailor_run"),
        ("user_system_design_session", "PROCESSING", "system_design"),
    ],
)
async def test_running_job_blocks_deletion(
    pg, checkpoint_tables, externals, table, status, kind
):
    mine = await seed_user(pg, USER)
    ids = {
        "user_suggestion": mine["suggestion"],
        "user_tailor_run": mine["tailor_run"],
        "user_system_design_session": mine["system_design"],
    }
    await pg.execute(f"UPDATE {table} SET status = %s WHERE id = %s", (status, ids[table]))
    seed_files(externals.s3, USER)

    with pytest.raises(HTTPException) as exc:
        await service.delete_account(pg, USER)
    assert exc.value.status_code == 409
    assert account_db.JOB_KIND_LABELS[kind] in exc.value.detail

    # Nothing was touched anywhere.
    assert await _one(pg, 'SELECT full_name FROM "user" WHERE auth0_id = %s', (USER,)) == (
        pii("alpha")["name"],
    )
    assert len(externals.s3.objects) == 3
    assert externals.stripe_calls == []
    assert externals.auth0.deleted == []


async def test_fresh_upload_blocks_deletion(pg, checkpoint_tables, externals):
    await seed_user(pg, USER)
    await pg.execute(
        "INSERT INTO user_upload_job (id, user_id, s3_key, status)"
        " VALUES ('j-new', %s, 'k', 'PENDING')",
        (USER,),
    )
    with pytest.raises(HTTPException) as exc:
        await service.delete_account(pg, USER)
    assert exc.value.status_code == 409
    assert "resume upload" in exc.value.detail


async def test_crashed_upload_does_not_block_deletion_forever(
    pg, checkpoint_tables, externals
):
    await seed_user(pg, USER)
    await pg.execute(
        "INSERT INTO user_upload_job (id, user_id, s3_key, status, created_at)"
        " VALUES ('j-stuck', %s, 'k', 'PROCESSING', now() - interval '2 hours')",
        (USER,),
    )
    await service.delete_account(pg, USER)
    assert await rows_naming(pg, USER) == {}


async def test_idle_sessions_do_not_block_deletion(pg, checkpoint_tables, externals):
    # seed_user's sessions are WAITING_FOR_INPUT / COMPLETED — idle.
    await seed_user(pg, USER)
    await pg.execute("UPDATE user_tailor_run SET status = 'FAILED'")
    await service.delete_account(pg, USER)
    assert externals.auth0.deleted == [USER]


# Deletion: failure modes ---------------------------------------------------


async def test_unconfigured_auth0_refuses_before_touching_anything(
    pg, checkpoint_tables, externals
):
    await seed_user(pg, USER)
    seed_files(externals.s3, USER)
    externals.auth0.configured = False
    with pytest.raises(HTTPException) as exc:
        await service.delete_account(pg, USER)
    assert exc.value.status_code == 503
    assert len(externals.s3.objects) == 3
    assert externals.stripe_calls == []


async def test_stripe_customer_without_stripe_configured_refuses(
    pg, checkpoint_tables, externals, monkeypatch
):
    await seed_user(pg, USER)
    seed_files(externals.s3, USER)
    monkeypatch.setattr(service, "STRIPE_SECRET_KEY", "")
    with pytest.raises(HTTPException) as exc:
        await service.delete_account(pg, USER)
    assert exc.value.status_code == 503
    assert len(externals.s3.objects) == 3
    assert await _one(pg, 'SELECT count(*) FROM "user" WHERE auth0_id = %s', (USER,)) == (1,)


async def test_storage_failure_rolls_back_and_a_retry_finishes(
    pg, checkpoint_tables, externals
):
    mine = await seed_user(pg, USER)
    await seed_checkpoints(pg, mine["threads"])
    seed_files(externals.s3, USER)
    externals.s3.fail_delete_keys = {f"resumes/{USER}/generated.docx"}

    with pytest.raises(HTTPException) as exc:
        await service.delete_account(pg, USER)
    assert exc.value.status_code == 502
    # The database is exactly as it was, and Stripe/Auth0 were never called.
    assert await _one(pg, 'SELECT full_name FROM "user" WHERE auth0_id = %s', (USER,)) == (
        pii("alpha")["name"],
    )
    assert await thread_rows(pg, mine["threads"]) == 9
    assert externals.stripe_calls == []
    assert externals.auth0.deleted == []

    externals.s3.fail_delete_keys = set()
    await service.delete_account(pg, USER)
    assert await rows_naming(pg, USER) == {}
    assert externals.s3.objects == {}
    assert externals.auth0.deleted == [USER]


async def test_stripe_failure_rolls_back_and_a_retry_finishes(
    pg, checkpoint_tables, externals, monkeypatch
):
    await seed_user(pg, USER)

    def down(customer_id):
        raise stripe.APIConnectionError("stripe is down")

    monkeypatch.setattr(stripe.Customer, "delete", down)
    with pytest.raises(HTTPException) as exc:
        await service.delete_account(pg, USER)
    assert exc.value.status_code == 502
    row = await _one(
        pg, 'SELECT full_name, stripe_customer_id FROM "user" WHERE auth0_id = %s', (USER,)
    )
    assert row == (pii("alpha")["name"], "cus_1")
    assert externals.auth0.deleted == []

    monkeypatch.setattr(stripe.Customer, "delete", lambda customer_id: None)
    await service.delete_account(pg, USER)
    assert await rows_naming(pg, USER) == {}


async def test_failure_after_stripe_forgets_the_deleted_customer(
    pg, checkpoint_tables, externals, monkeypatch
):
    """The Stripe customer is gone but the erase rolled back: the row must
    not keep pointing at a deleted customer, or the next checkout breaks."""
    await seed_user(pg, USER)

    async def broken_erase(conn, user_id):
        raise RuntimeError("erase failed")

    monkeypatch.setattr(account_db, "erase_account", broken_erase)
    with pytest.raises(RuntimeError):
        await service.delete_account(pg, USER)
    row = await _one(
        pg, 'SELECT full_name, stripe_customer_id FROM "user" WHERE auth0_id = %s', (USER,)
    )
    assert row == (pii("alpha")["name"], None)
    assert ("delete", "cus_1") in externals.stripe_calls
    assert externals.auth0.deleted == []


async def test_auth0_failure_keeps_the_login_for_a_retry(
    pg, checkpoint_tables, externals
):
    await seed_user(pg, USER)
    externals.auth0.fail_delete = Auth0ManagementError("auth0 down")

    with pytest.raises(HTTPException) as exc:
        await service.delete_account(pg, USER)
    assert exc.value.status_code == 502
    assert "sign-in" in exc.value.detail
    # The data is already gone…
    assert await rows_mentioning(pg, pii("alpha")["email"]) == {}

    # …the still-signed-in frontend re-creates a bare row on its next page
    # load, and the retry clears that too and finishes with Auth0.
    await pg.execute('INSERT INTO "user" (auth0_id) VALUES (%s)', (USER,))
    externals.auth0.fail_delete = None
    await service.delete_account(pg, USER)
    assert await rows_naming(pg, USER) == {}
    assert externals.auth0.deleted == [USER]
    tombstones = (
        await _one(pg, "SELECT count(*) FROM \"user\" WHERE auth0_id LIKE 'deleted|%'")
    )[0]
    assert tombstones == 1


# After deletion -------------------------------------------------------------


async def test_admin_views_show_the_tombstone_as_an_anonymous_user(
    pg, checkpoint_tables, externals
):
    await seed_user(pg, USER)
    revenue_before = (await admin_service.list_purchases(pg)).revenue_cents
    await service.delete_account(pg, USER)

    users = (await admin_service.list_users(pg)).users
    (tomb,) = users
    assert is_tombstone_id(tomb.auth0_id)
    assert (tomb.email, tomb.full_name, tomb.balance_cents) == (None, None, 0.0)
    assert tomb.cents_purchased == 1100
    assert tomb.cents_used == pytest.approx(3.0)

    usage = await admin_service.get_usage(pg)
    assert {r.user_id for r in usage.recent} == {tomb.auth0_id}
    purchases = await admin_service.list_purchases(pg)
    assert purchases.revenue_cents == revenue_before
    assert {p.user_id for p in purchases.purchases} == {tomb.auth0_id}


async def test_late_checkout_completion_lands_on_the_tombstone(
    pg, checkpoint_tables, externals, monkeypatch
):
    """A checkout paid in the instant before deletion expired it: the
    webhook must still succeed (no FK error, no Stripe retry storm)."""
    mine = await seed_user(pg, USER)
    await service.delete_account(pg, USER)
    monkeypatch.setattr(billing_service, "STRIPE_WEBHOOK_SECRET", "whsec_x")
    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": mine["open_checkout"],
                "client_reference_id": USER,
                "metadata": {"pack_id": "starter", "cents": "500"},
                "amount_total": 500,
                "currency": "usd",
                "payment_intent": "pi_late",
                "payment_status": "paid",
            }
        },
    }
    monkeypatch.setattr(
        stripe.Webhook,
        "construct_event",
        staticmethod(lambda *a, **kw: stripe.Event.construct_from(event, key=None)),
    )
    assert await billing_service.handle_webhook(pg, b"{}", "sig") == {"ok": True}
    row = await _one(
        pg, "SELECT user_id, status FROM balance_purchase WHERE id = %s", (mine["open_checkout"],)
    )
    assert is_tombstone_id(row[0]) and row[1] == "COMPLETED"
    assert await rows_naming(pg, USER) == {}


# Export ---------------------------------------------------------------------


async def _export(pg):
    archive_file = await service.export_account(pg, USER)
    zf = zipfile.ZipFile(io.BytesIO(archive_file.read()))
    archive_file.close()
    return zf


async def test_export_contains_every_row_and_file(pg, checkpoint_tables, externals):
    mine = await seed_user(pg, USER)
    await seed_user(pg, OTHER, tag="beta", stripe_customer="cus_other")
    seed_files(externals.s3, USER, n_tailored=1)
    seed_files(externals.s3, OTHER)

    zf = await _export(pg)
    data = json.loads(zf.read("data.json"))

    assert data["format_version"] == 1
    assert data["exported_at"]
    assert data["account"]["auth0_id"] == USER
    assert data["account"]["balance_cents"] == 12.5
    assert data["account"]["stripe_customer_id"] == "cus_1"
    assert "site_admin" not in data["account"]
    assert data["login_identity"] == {"user_id": USER, "email": "jane@login.example"}
    p = pii("alpha")
    assert data["profile"] == {
        "full_name": p["name"],
        "email": p["email"],
        "phone": p["phone"],
        "location": p["location"],
        "summary": p["summary"],
    }
    assert [link["link"] for link in data["links"]] == ["https://linkedin.com/in/jane"]
    (exp,) = data["experiences"]
    assert [b["bullet"] for b in exp["bullets"]] == [p["bullet"], "Cut p99 latency"]
    assert [s["name"] for s in data["skills"]] == ["Go"]
    assert len(data["education"]) == len(data["projects"]) == 1
    assert data["resume_format"]["format"] == {"columns": 1}
    assert data["generated_resume"]["template"] == "original"
    assert "s3_key" not in data["generated_resume"]
    assert [u["status"] for u in data["resume_uploads"]] == ["COMPLETED"]
    (sugg,) = data["suggestions"]
    assert sugg["result"] == [{"bullet_id": mine["bullet"], "options": ["a"]}]
    assert sugg["pending_question"] == "How many users?"
    (run,) = data["tailor_runs"]
    assert run["result"] == {"summary": "Tailored"}
    (tailored,) = data["tailored_resumes"]
    assert tailored["content"] == {"summary": "Tailored"}
    assert "source_hash" not in tailored and "s3_key" not in tailored
    (session,) = data["system_design_sessions"]
    assert session["diagram"] == [{"id": "box"}]
    assert session["phase_durations"] == {"REQUIREMENTS": 60}
    for hidden in ("brief", "agent_context", "last_turn_id", "notice"):
        assert hidden not in session
    assert [m["content"] for m in session["messages"]] == [
        "What are the requirements?",
        p["answer"],
    ]
    assert [d["topic"] for d in data["dsa_progress"]] == ["two-pointers"]
    assert sorted(p["id"] for p in data["purchases"]) == sorted(
        [mine["paid_checkout"], mine["open_checkout"]]
    )
    assert all("payment_intent_id" not in p for p in data["purchases"])
    assert len(data["usage"]) == 2
    for row in data["usage"]:
        assert "actual_cost_cents" not in row
        assert "openrouter_generation_ids" not in row

    # Nothing of the other user's leaks in.
    raw = zf.read("data.json").decode()
    for needle in pii("beta").values():
        assert needle not in raw

    names = set(zf.namelist())
    assert {
        "data.json",
        "README.txt",
        "files/resume_doc.docx",
        "files/resume_doc.pdf",
        "files/generated.docx",
        "files/tailored/00000.docx",
    } == names
    assert zf.read("files/resume_doc.pdf") == b"%PDF original"


async def test_export_survives_an_auth0_outage(pg, checkpoint_tables, externals):
    await seed_user(pg, USER)
    externals.auth0.fail_get = Auth0ManagementError("down")
    zf = await _export(pg)
    assert json.loads(zf.read("data.json"))["login_identity"] is None
    assert "couldn't be retrieved" in zf.read("README.txt").decode()


async def test_export_without_a_profile_yet(pg, checkpoint_tables, externals):
    await pg.execute('INSERT INTO "user" (auth0_id) VALUES (%s)', (USER,))
    zf = await _export(pg)
    data = json.loads(zf.read("data.json"))
    assert data["experiences"] == [] and data["resume_format"] is None
    assert [n for n in zf.namelist() if n.startswith("files/")] == []


async def test_export_fails_loudly_when_storage_is_down(pg, checkpoint_tables, externals):
    from botocore.exceptions import ClientError

    await seed_user(pg, USER)
    externals.s3.fail_list = ClientError({"Error": {"Code": "AccessDenied"}}, "List")
    with pytest.raises(HTTPException) as exc:
        await service.export_account(pg, USER)
    assert exc.value.status_code == 502


# Races: the row lock -------------------------------------------------------


async def _second_conn():
    return await psycopg.AsyncConnection.connect(TEST_PG_URL, autocommit=True)


async def _parked(task) -> bool:
    """True when `task` is still blocked (on a row lock) after a beat."""
    await asyncio.sleep(0.3)
    return not task.done()


async def test_job_queued_during_deletion_waits_then_404s(pg, checkpoint_tables, externals):
    mine = await seed_user(pg, USER)
    other = await _second_conn()
    amqp = _Amqp()
    try:
        async with pg.transaction():
            # Mid-deletion: the row lock is held, nothing erased yet.
            assert await account_db.lock_account(pg, USER)
            answer = asyncio.create_task(
                sugg_service.answer_suggestion(
                    USER,
                    mine["suggestion"],
                    sugg_model.AnswerRequest(text="hi"),
                    other,
                    amqp,
                )
            )
            assert await _parked(answer)
            await account_db.erase_account(pg, USER)
        with pytest.raises(HTTPException) as exc:
            await answer
        assert exc.value.status_code == 404
        assert amqp.publisher.published == []
    finally:
        await other.close()


async def test_interview_turn_during_deletion_waits_then_404s(
    pg, checkpoint_tables, externals
):
    mine = await seed_user(pg, USER)
    other = await _second_conn()
    amqp = _Amqp()
    try:
        async with pg.transaction():
            assert await account_db.lock_account(pg, USER)
            turn = asyncio.create_task(
                sd_service.take_turn(
                    other,
                    amqp,
                    USER,
                    mine["system_design"],
                    sd_model.TurnRequest(action="message", text="My answer"),
                )
            )
            assert await _parked(turn)
            await account_db.erase_account(pg, USER)
        with pytest.raises(HTTPException) as exc:
            await turn
        assert exc.value.status_code == 404
        assert amqp.publisher.published == []
    finally:
        await other.close()


async def test_new_run_during_deletion_fails_without_publishing(
    pg, checkpoint_tables, externals
):
    await seed_user(pg, USER)
    await pg.execute("DELETE FROM user_tailor_run")
    other = await _second_conn()
    amqp = _Amqp()
    try:
        async with pg.transaction():
            assert await account_db.lock_account(pg, USER)
            start = asyncio.create_task(
                tailor_service.start_tailor(
                    other,
                    amqp,
                    tailor_model.StartTailorRequest(job_description="A job"),
                    USER,
                )
            )
            assert await _parked(start)
            await account_db.erase_account(pg, USER)
        # The insert's foreign-key check waited on the lock, then found the
        # account gone.
        with pytest.raises(ForeignKeyViolation):
            await start
        assert amqp.publisher.published == []
    finally:
        await other.close()


async def test_upload_during_deletion_stores_no_file(
    pg, checkpoint_tables, externals, monkeypatch
):
    import docx
    from fastapi import UploadFile

    await seed_user(pg, USER)
    buf = io.BytesIO()
    docx.Document().save(buf)
    monkeypatch.setattr(upload_service, "get_s3_client", lambda **_kw: externals.s3)
    other = await _second_conn()
    amqp = _Amqp()
    try:
        async with pg.transaction():
            assert await account_db.lock_account(pg, USER)
            upload = asyncio.create_task(
                upload_service.upload_resume(
                    UploadFile(file=io.BytesIO(buf.getvalue()), filename="r.docx"),
                    USER,
                    amqp,
                    other,
                )
            )
            assert await _parked(upload)
            await account_db.erase_account(pg, USER)
        with pytest.raises(ForeignKeyViolation):
            await upload
        # The job row comes first now, so the file never reached S3.
        assert externals.s3.objects == {}
        assert amqp.publisher.published == []
    finally:
        await other.close()


async def test_resume_export_during_deletion_writes_no_file(
    pg, checkpoint_tables, externals, monkeypatch
):
    await seed_user(pg, USER)
    await pg.execute("DELETE FROM user_generated_resume")
    monkeypatch.setattr(export_service, "get_s3_client", lambda **_kw: externals.s3)
    other = await _second_conn()
    try:
        async with pg.transaction():
            assert await account_db.lock_account(pg, USER)
            export = asyncio.create_task(export_service.export_resume(other, USER))
            assert await _parked(export)
            await account_db.erase_account(pg, USER)
        with pytest.raises(HTTPException) as exc:
            await export
        assert exc.value.status_code == 404
        assert externals.s3.objects == {}
    finally:
        await other.close()


async def test_deletion_waits_for_a_job_being_queued_then_409s(
    pg, checkpoint_tables, externals
):
    """The other order: a submission holds the row first, so the deletion
    waits for it and then sees its PROCESSING row."""
    mine = await seed_user(pg, USER)
    other = await _second_conn()
    try:
        async with other.transaction():
            from api.user_row import share_user_row

            await share_user_row(other, USER)
            await other.execute(
                "UPDATE user_suggestion SET status = 'PROCESSING' WHERE id = %s",
                (mine["suggestion"],),
            )
            deletion = asyncio.create_task(service.delete_account(pg, USER))
            assert await _parked(deletion)
        with pytest.raises(HTTPException) as exc:
            await deletion
        assert exc.value.status_code == 409
        assert externals.auth0.deleted == []
    finally:
        await other.close()

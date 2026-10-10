import json
import math
import time
from dataclasses import asdict

from openrouter import OpenRouter, errors
from psycopg import Connection
from psycopg.rows import class_row
from shared.accounts import new_tombstone_id
from shared.checkpoints import CHECKPOINT_TABLES, THREAD_OWNER_TABLES
from shared.docgen import FormatProfile

from ..agents.docx_parser import UserDocxProfile
from ..agents.suggestions import FetchSuggestionRow, SuggestionsResult
from ..agents.system_design import (
    FetchSystemDesignSessionRow,
    GradeReport,
    TranscriptRow,
)
from ..agents.tailor import (
    FetchTailorRunRow,
    TailoredResume,
    TailorEducationRow,
    TailorExperienceRow,
    TailorHeaderRow,
    TailorProfile,
    TailorProjectRow,
    TailorSkillRow,
    TailorSocialLinkRow,
)
from ..env_vars import OPENROUTER_API_KEY


class DbOpError(Exception):
    pass


# Charged when a job's model has no model_pricing row (e.g. the env-default
# model isn't in the catalog). Roughly gpt-5 rates — mid-tier, so unpriced
# models never run free.
FALLBACK_CENTS_PER_1K_INPUT = 0.16
FALLBACK_CENTS_PER_1K_OUTPUT = 1.25

# Markup applied on top of OpenRouter's reported cost.
COST_MARKUP = 1.25


# Generation stats are written asynchronously — a lookup right after the
# response can 404 for ~15s — so poll on 404 until this shared deadline.
STATS_LOOKUP_TIMEOUT_S = 30.0


def fetch_generation_cost_cents(generation_ids: list[str]) -> float | None:
    """Sum OpenRouter's actual billed cost (in cents) for the given generation
    ids. Returns None when no ids were captured, the key is unset, or any
    lookup failed — callers then fall back to the rate card."""
    if not generation_ids or not OPENROUTER_API_KEY:
        return None
    client = OpenRouter(api_key=OPENROUTER_API_KEY)
    deadline = time.monotonic() + STATS_LOOKUP_TIMEOUT_S
    total = 0.0
    resolved = 0
    for gen_id in generation_ids:
        data = None
        delay = 1.0
        while True:
            try:
                data = client.generations.get_generation(id=gen_id).data
                break
            except errors.NotFoundResponseError:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    print(f"Generation stats lookup timed out for {gen_id}")
                    break
                time.sleep(min(delay, remaining))
                delay = min(delay * 2, 8.0)
            except Exception as e:
                print(f"Generation stats lookup failed for {gen_id}: {e}")
                break
        if data is not None:
            resolved += 1
            total += float(data.total_cost or 0)
    # All-or-nothing: a partially-resolved job would undercharge, so any
    # failed lookup falls the whole job back to the rate card.
    if resolved != len(generation_ids):
        return None
    # total_cost is USD (dollars); store cents.
    print(f"OpenRouter actual cost: ${total:.6f} across {resolved} generation(s)")
    return total * 100


def usage_job_id(base_id: str, job_data: dict) -> str:
    """token_usage key for one turn of a multi-turn session/run.

    Each published turn carries its own turn_id (see shared.amqp), so every
    turn gets its own ledger row while a redelivery of the same turn still
    conflicts. Jobs published before turn ids existed fall back to the bare
    id — one row per session, as before."""
    turn_id = job_data.get("turn_id")
    if isinstance(turn_id, str) and turn_id:
        return f"{base_id}:{turn_id}"
    return base_id


def record_token_usage(
    pg_client: Connection,
    *,
    user_id: str,
    job_kind: str,
    job_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    generation_ids: list[str],
    cost_usd: float | None = None,
) -> float:
    """Insert one token_usage row and deduct from the user's balance.
    Floors at 0 — a job that overruns still finishes. Returns cents charged.

    cost_usd is the pre-markup USD cost summed from the inline `usage.cost`
    field on each response, or None if any response lacked it — in that case
    the generation stats endpoint is tried, then the rate card."""
    if not input_tokens and not output_tokens:
        return 0.0

    if cost_usd is not None:
        actual_cost_cents = cost_usd * 100
    else:
        actual_cost_cents = fetch_generation_cost_cents(generation_ids)
    if actual_cost_cents is not None:
        # Round up to 1/10,000¢ so sub-cent charges never round down to free.
        amount_cents = math.ceil(actual_cost_cents * COST_MARKUP * 10_000) / 10_000
    else:
        row = pg_client.execute(
            """
            SELECT cents_per_1k_input, cents_per_1k_output
            FROM model_pricing WHERE id = %s
            """,
            (model,),
        ).fetchone()
        rate_in = float(row[0]) if row else FALLBACK_CENTS_PER_1K_INPUT
        rate_out = float(row[1]) if row else FALLBACK_CENTS_PER_1K_OUTPUT
        amount_cents = (
            math.ceil(
                (input_tokens * rate_in + output_tokens * rate_out) / 1000 * 10_000
            )
            / 10_000
        )

    with pg_client.transaction():
        # FOR KEY SHARE parks this behind an in-progress account deletion
        # (which holds FOR UPDATE), so the check below sees its outcome.
        owner = pg_client.execute(
            'SELECT 1 FROM "user" WHERE auth0_id = %s FOR KEY SHARE', (user_id,)
        ).fetchone()
        if not owner:
            # The account was deleted while the job ran. The ledger still
            # records what the job cost — on a fresh tombstone, the same
            # de-identified shape deletion gives the account's other billing
            # rows — and the person is never re-created.
            row = pg_client.execute(
                """
                SELECT amount_cents FROM token_usage
                WHERE job_kind = %s AND job_id = %s
                """,
                (job_kind, job_id),
            ).fetchone()
            if row:
                return float(row[0])
            user_id = new_tombstone_id()
            pg_client.execute('INSERT INTO "user" (auth0_id) VALUES (%s)', (user_id,))
        res = pg_client.execute(
            """
            INSERT INTO token_usage
              (user_id, job_kind, job_id, model,
               input_tokens, output_tokens, amount_cents,
               actual_cost_cents, openrouter_generation_ids)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_kind, job_id) DO NOTHING
            """,
            (
                user_id,
                job_kind,
                job_id,
                model,
                input_tokens,
                output_tokens,
                amount_cents,
                actual_cost_cents,
                generation_ids,
            ),
        )
        if res.rowcount == 0:
            # A redelivered AMQP message re-ran this job and the first run
            # already charged — return that charge without debiting again.
            row = pg_client.execute(
                """
                SELECT amount_cents FROM token_usage
                WHERE job_kind = %s AND job_id = %s
                """,
                (job_kind, job_id),
            ).fetchone()
            return float(row[0]) if row else 0.0
        pg_client.execute(
            """
            UPDATE "user"
            SET balance_cents = GREATEST(0, balance_cents - %s)
            WHERE auth0_id = %s
            """,
            (amount_cents, user_id),
        )
    return amount_cents


def delete_checkpoint_threads(pg_client: Connection, thread_ids: list[str]) -> None:
    """Drop the LangGraph checkpoint rows of these threads. The tables only
    exist once a dispatcher has run setup, so a missing table is skipped."""
    if not thread_ids:
        return
    for table in CHECKPOINT_TABLES:
        exists = pg_client.execute("SELECT to_regclass(%s)", (table,)).fetchone()
        if exists and exists[0]:
            pg_client.execute(
                f"DELETE FROM {table} WHERE thread_id = ANY(%s)", (list(thread_ids),)
            )


def suggestion_exists(pg_client: Connection, session_id: str) -> bool:
    row = pg_client.execute(
        "SELECT 1 FROM user_suggestion WHERE id = %s", (session_id,)
    ).fetchone()
    return row is not None


def discard_orphaned_thread(pg_client: Connection, table: str, thread_id: str) -> bool:
    """If `thread_id`'s row in `table` is gone — dismissed, or the account
    deleted, while the agent ran — delete the checkpoints the agent wrote
    after the row's own cleanup, and return True."""
    if table not in THREAD_OWNER_TABLES:
        raise ValueError(f"{table!r} doesn't own LangGraph threads")
    row = pg_client.execute(
        f"SELECT 1 FROM {table} WHERE id = %s", (thread_id,)
    ).fetchone()
    if row is not None:
        return False
    delete_checkpoint_threads(pg_client, [thread_id])
    return True


def default_model_spec(pg_client: Connection) -> str | None:
    """The admin-selected default model (is_default + enabled)."""
    row = pg_client.execute(
        """
        SELECT id FROM model_pricing
        WHERE is_default AND enabled ORDER BY sort_order LIMIT 1
        """
    ).fetchone()
    return row[0] if row else None


def fetch_suggestion_rows(
    pg_client: Connection, session_id: str
) -> list[FetchSuggestionRow]:
    with pg_client.cursor(row_factory=class_row(FetchSuggestionRow)) as cursor:
        return cursor.execute(
            """
            SELECT
                us.pending_question,
                us.status,
                us.result,
                us.model,
                us.user_id,
                ue.company_name,
                ue.description,
                ue.start_date,
                ue.end_date,
                ue.title,
                ub.id as bullet_id,
                ub.bullet
            FROM user_suggestion us
            JOIN user_base_experience ue ON ue.id = us.experience_id
            join user_base_experience_bullet ub on ub.user_experience_id = ue.id
            WHERE us.id = %s
            and (us.bullet_id is null or ub.id = us.bullet_id)
            ORDER BY ub.bullet_order
            """,
            [session_id],
        ).fetchall()


def _suggestions_json(result: SuggestionsResult) -> str:
    return json.dumps([asdict(s) for s in result.suggestions])


def set_suggestion_question(
    pg_client: Connection,
    session_id: str,
    question: str | None,
    result: SuggestionsResult | None = None,
):
    # `result` is set when the review interrupt fired — the options are
    # pickable while the session waits for the user's reply.
    payload = _suggestions_json(result) if result else None
    with pg_client.transaction():
        pg_client.execute(
            """
            UPDATE user_suggestion
            SET pending_question = %s, status = 'WAITING_FOR_INPUT',
                result = COALESCE(%s, result)
            WHERE id = %s
            """,
            (question, payload, session_id),
        )


def complete_suggestion(pg_client: Connection, session_id: str) -> bool:
    """Mark the session finished — only valid once options exist (the agent
    can end without resubmitting when the user replies that they're happy)."""
    with pg_client.transaction():
        res = pg_client.execute(
            """
            UPDATE user_suggestion
            SET status = 'COMPLETED', pending_question = NULL
            WHERE id = %s AND result IS NOT NULL
            """,
            (session_id,),
        )
        return res.rowcount > 0


def set_suggestion_result(
    pg_client: Connection, session_id: str, result: SuggestionsResult
):
    payload = _suggestions_json(result)
    with pg_client.transaction():
        pg_client.execute(
            """
            UPDATE user_suggestion
            SET result = %s, status = 'COMPLETED', pending_question = NULL
            WHERE id = %s
            """,
            (payload, session_id),
        )


def set_suggestion_failed(pg_client: Connection, session_id: str):
    # Don't clobber a result or a pending question that was already written —
    # the session is still usable in those states.
    with pg_client.transaction():
        pg_client.execute(
            """
            UPDATE user_suggestion
            SET status = 'FAILED'
            WHERE id = %s AND status NOT IN ('COMPLETED', 'WAITING_FOR_INPUT')
            """,
            (session_id,),
        )


def fetch_tailor_run(pg_client: Connection, run_id: str) -> FetchTailorRunRow | None:
    with pg_client.cursor(row_factory=class_row(FetchTailorRunRow)) as cursor:
        return cursor.execute(
            """
            SELECT id, user_id, job_description, company_name, role,
                   status, model
            FROM user_tailor_run WHERE id = %s
            """,
            [run_id],
        ).fetchone()


def fetch_tailor_profile(pg_client: Connection, user_id: str) -> TailorProfile:
    with pg_client.cursor(row_factory=class_row(TailorHeaderRow)) as cursor:
        header = cursor.execute(
            """
            SELECT full_name, email, phone, location
            FROM "user" WHERE auth0_id = %s
            """,
            [user_id],
        ).fetchone()

    with pg_client.cursor(row_factory=class_row(TailorSocialLinkRow)) as cursor:
        social_links = cursor.execute(
            """
            SELECT link, type FROM user_social_link WHERE user_id = %s
            """,
            [user_id],
        ).fetchall()

    with pg_client.cursor(row_factory=class_row(TailorExperienceRow)) as cursor:
        experiences = cursor.execute(
            """
            SELECT
                e.id AS experience_id,
                e.company_name,
                e.title,
                e.start_date,
                e.end_date,
                e.description,
                b.id AS bullet_id,
                b.bullet,
                b.bullet_order
            FROM user_base_experience e
            LEFT JOIN user_base_experience_bullet b
                ON b.user_experience_id = e.id
            WHERE e.user_id = %s
            ORDER BY e.created_at DESC, b.bullet_order ASC
            """,
            [user_id],
        ).fetchall()

    with pg_client.cursor(row_factory=class_row(TailorSkillRow)) as cursor:
        skills = cursor.execute(
            """
            SELECT name, category FROM user_base_skill
            WHERE user_id = %s ORDER BY sort_order, id
            """,
            [user_id],
        ).fetchall()

    with pg_client.cursor(row_factory=class_row(TailorEducationRow)) as cursor:
        education = cursor.execute(
            """
            SELECT institution, degree, field_of_study, start_date, end_date,
                   description
            FROM user_base_education WHERE user_id = %s
            """,
            [user_id],
        ).fetchall()

    with pg_client.cursor(row_factory=class_row(TailorProjectRow)) as cursor:
        projects = cursor.execute(
            """
            SELECT name, link, description, start_date, end_date
            FROM user_base_project WHERE user_id = %s
            """,
            [user_id],
        ).fetchall()

    return TailorProfile(
        header=header,
        social_links=social_links,
        experiences=experiences,
        skills=skills,
        education=education,
        projects=projects,
    )


def set_tailor_question(
    pg_client: Connection,
    run_id: str,
    question: str | None,
    result: TailoredResume | None = None,
):
    # `result` is set when the post-submit feedback interrupt fired — the
    # resume is reviewable while the run still waits for the user's reply.
    payload = result.model_dump_json() if result else None
    with pg_client.transaction():
        pg_client.execute(
            """
            UPDATE user_tailor_run
            SET pending_question = %s, status = 'WAITING_FOR_INPUT',
                result = COALESCE(%s, result)
            WHERE id = %s
            """,
            (question, payload, run_id),
        )


def complete_tailor_run(pg_client: Connection, run_id: str) -> bool:
    """Mark the run finished — only valid once a result exists (the agent can
    end without a fresh submit when the user accepts the resume)."""
    with pg_client.transaction():
        res = pg_client.execute(
            """
            UPDATE user_tailor_run
            SET status = 'COMPLETED', pending_question = NULL
            WHERE id = %s AND result IS NOT NULL
            """,
            (run_id,),
        )
        return res.rowcount > 0


def set_tailor_result(pg_client: Connection, run_id: str, result: TailoredResume):
    payload = result.model_dump_json()
    with pg_client.transaction():
        pg_client.execute(
            """
            UPDATE user_tailor_run
            SET result = %s, status = 'COMPLETED', pending_question = NULL
            WHERE id = %s
            """,
            (payload, run_id),
        )


def set_tailor_failed(pg_client: Connection, run_id: str):
    with pg_client.transaction():
        pg_client.execute(
            """
            UPDATE user_tailor_run
            SET status = 'FAILED'
            WHERE id = %s AND status NOT IN ('COMPLETED')
            """,
            (run_id,),
        )


# Closes out the current phase: its elapsed seconds land in phase_durations.
# Shared by every write that moves a session into FEEDBACK.
_SYSTEM_DESIGN_ENTER_FEEDBACK = """
    phase_durations = CASE WHEN phase = 'FEEDBACK' THEN phase_durations ELSE
        (phase_durations::jsonb || jsonb_build_object(
            phase,
            GREATEST(0, EXTRACT(EPOCH FROM now() - phase_started_at))::int
        ))::text END,
    phase_started_at = CASE WHEN phase = 'FEEDBACK' THEN phase_started_at
        ELSE now() END,
    phase = 'FEEDBACK'
"""


def fetch_system_design_session(
    pg_client: Connection, session_id: str
) -> FetchSystemDesignSessionRow | None:
    with pg_client.cursor(
        row_factory=class_row(FetchSystemDesignSessionRow)
    ) as cursor:
        return cursor.execute(
            """
            SELECT id, user_id, source, problem_id, company_name, role,
                   job_description, level, model, status, phase, title, prompt,
                   brief, requirements, estimates, diagram, agent_context,
                   last_turn_id, phase_durations, phase_started_at, created_at
            FROM user_system_design_session WHERE id = %s
            """,
            [session_id],
        ).fetchone()


def fetch_system_design_transcript(
    pg_client: Connection, session_id: str
) -> list[TranscriptRow]:
    with pg_client.cursor(row_factory=class_row(TranscriptRow)) as cursor:
        return cursor.execute(
            """
            SELECT role, phase, content FROM system_design_message
            WHERE session_id = %s ORDER BY id
            """,
            [session_id],
        ).fetchall()


def _add_interviewer_message(
    pg_client: Connection, session_id: str, phase: str, content: str
) -> None:
    pg_client.execute(
        """
        INSERT INTO system_design_message (session_id, role, phase, content)
        VALUES (%s, 'INTERVIEWER', %s, %s)
        """,
        (session_id, phase, content),
    )


def start_system_design_session(
    pg_client: Connection,
    session_id: str,
    *,
    title: str,
    prompt: str,
    brief_json: str,
    opening: str,
    turn_id: str | None,
) -> None:
    """Store the problem and brief and post the interviewer's opening."""
    with pg_client.transaction():
        pg_client.execute(
            """
            UPDATE user_system_design_session
            SET title = %s, prompt = %s, brief = %s,
                status = 'WAITING_FOR_INPUT', notice = NULL, last_turn_id = %s,
                phase_started_at = now()
            WHERE id = %s
            """,
            (title, prompt, brief_json, turn_id, session_id),
        )
        _add_interviewer_message(pg_client, session_id, "REQUIREMENTS", opening)


def save_system_design_turn(
    pg_client: Connection,
    session_id: str,
    *,
    reply: str,
    phase: str,
    agent_context: str,
    interview_over: bool,
    turn_id: str | None,
) -> None:
    """Post the interviewer's reply. A finished interview moves to FEEDBACK
    and stays PROCESSING for grading; otherwise it's the candidate's turn."""
    with pg_client.transaction():
        _add_interviewer_message(pg_client, session_id, phase, reply)
        if interview_over:
            pg_client.execute(
                f"""
                UPDATE user_system_design_session
                SET agent_context = %s, notice = NULL,
                    {_SYSTEM_DESIGN_ENTER_FEEDBACK}
                WHERE id = %s
                """,
                (agent_context, session_id),
            )
        else:
            pg_client.execute(
                """
                UPDATE user_system_design_session
                SET agent_context = %s, notice = NULL,
                    status = 'WAITING_FOR_INPUT', last_turn_id = %s
                WHERE id = %s
                """,
                (agent_context, turn_id, session_id),
            )


def complete_system_design_session(
    pg_client: Connection,
    session_id: str,
    report: GradeReport,
    turn_id: str | None,
) -> None:
    with pg_client.transaction():
        pg_client.execute(
            """
            UPDATE user_system_design_session
            SET result = %s, letter_grade = %s, hire_signal = %s,
                status = 'COMPLETED', notice = NULL, last_turn_id = %s,
                completed_at = now()
            WHERE id = %s
            """,
            (
                report.to_json(),
                report.letter_grade,
                report.hire_signal,
                turn_id,
                session_id,
            ),
        )
        # A graded interview takes no more turns, and its transcript lives in
        # system_design_message — the interviewer thread is dead weight.
        delete_checkpoint_threads(pg_client, [session_id])


def set_system_design_notice(
    pg_client: Connection, session_id: str, notice: str
) -> None:
    """A turn crashed — hand the turn back to the candidate with a retry
    notice. The checkpointed thread lets the retry pick up where it died."""
    with pg_client.transaction():
        pg_client.execute(
            """
            UPDATE user_system_design_session
            SET status = 'WAITING_FOR_INPUT', notice = %s
            WHERE id = %s
            """,
            (notice, session_id),
        )


def set_system_design_failed(pg_client: Connection, session_id: str) -> None:
    # A waiting session is still usable (retry notice) — leave it be.
    with pg_client.transaction():
        pg_client.execute(
            """
            UPDATE user_system_design_session
            SET status = 'FAILED'
            WHERE id = %s AND status NOT IN ('COMPLETED', 'WAITING_FOR_INPUT')
            """,
            (session_id,),
        )


def upsert_resume_format(
    pg_client: Connection, user_id: str, fmt: FormatProfile, source_job_id: str
):
    """Store the layout profile captured from the user's uploaded doc — the
    renderer reads this back to regenerate a matching resume. A no-op when
    the account has been deleted meanwhile."""
    with pg_client.transaction():
        pg_client.execute(
            """
            INSERT INTO user_resume_format (user_id, format, source_job_id)
            SELECT auth0_id, %s, %s FROM "user" WHERE auth0_id = %s
            ON CONFLICT (user_id) DO UPDATE SET
                format = EXCLUDED.format,
                source_job_id = EXCLUDED.source_job_id,
                captured_at = now()
            """,
            [fmt.to_json(), source_job_id, user_id],
        )


def _social_link_type(link: str) -> str:
    """Map a profile link onto the SocialLinkType enum (contract.prisma)."""
    low = link.lower()
    if "linkedin.com" in low:
        return "LINKEDIN"
    if "github.com" in low:
        return "GITHUB"
    return "WEBSITE"


def upsert_user_profile(
    pg_client: Connection, user_id: str, profile: UserDocxProfile
) -> bool:
    """Replace the user's profile with a freshly parsed resume. Returns False,
    writing nothing, when the user row is gone: the account was deleted while
    the resume was parsing, and inserting it again would resurrect the person.
    (The row always exists otherwise — the frontend creates it at sign-in and
    the upload's job row references it.)"""
    with pg_client.transaction():
        # The UPDATE's row lock also holds off a concurrent account deletion
        # until this profile is committed — the deletion then erases it.
        res = pg_client.execute(
            """
            UPDATE "user"
            SET full_name = %s, email = %s, phone = %s, location = %s,
                summary = %s
            WHERE auth0_id = %s
            """,
            [
                profile.basic_info.name,
                profile.basic_info.email,
                profile.basic_info.phone,
                profile.basic_info.location,
                profile.summary or None,
                user_id,
            ],
        )
        if res.rowcount == 0:
            return False

        # Header links feed the exported resume's contact line — replace the
        # set wholesale like the other profile-owned rows. The table is
        # unique on (user_id, type), so the first link per type wins.
        pg_client.execute(
            "DELETE FROM user_social_link WHERE user_id = %s", [user_id]
        )
        # unique(user_id, type) holds one row per type — keep the first
        # link of each in header order and log whatever is dropped.
        seen_types: set[str] = set()
        for link in getattr(profile.basic_info, "links", None) or []:
            link_type = _social_link_type(link)
            if link_type in seen_types:
                print(
                    f"user_social_link: dropping extra {link_type} link "
                    f"for {user_id}: {link}"
                )
                continue
            seen_types.add(link_type)
            pg_client.execute(
                """
                INSERT INTO user_social_link (user_id, link, type)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, type) DO NOTHING
                """,
                [user_id, link, link_type],
            )

        # Bullets FK to experiences — delete children before parents.
        # Suggestions reference both, so they go first, and their LangGraph
        # threads with them (thread_id = session id) — nothing else ever
        # points at those threads again.
        stale_sessions = pg_client.execute(
            """
            DELETE FROM user_suggestion WHERE experience_id IN (
                SELECT id FROM user_base_experience WHERE user_id = %s
            )
            RETURNING id
            """,
            [user_id],
        ).fetchall()
        delete_checkpoint_threads(pg_client, [row[0] for row in stale_sessions])

        pg_client.execute(
            """
            DELETE FROM user_base_experience_bullet WHERE user_experience_id IN (
                SELECT id FROM user_base_experience WHERE user_id = %s
            )
            """,
            [user_id],
        )

        pg_client.execute(
            """
            DELETE FROM user_base_experience WHERE user_id = %s
            """,
            [user_id],
        )

        for experience in profile.experience:
            experience_id = pg_client.execute(
                """
                INSERT INTO user_base_experience (user_id, company_name, title, start_date, end_date)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
                """,
                [
                    user_id,
                    experience.company,
                    experience.position,
                    experience.start_date,
                    experience.end_date,
                ],
            ).fetchone()
            if not experience_id:
                raise DbOpError("Failed to insert experience")
            experience_id = experience_id[0]

            for i, bullet in enumerate(experience.bullets):
                pg_client.execute(
                    """
                    INSERT INTO user_base_experience_bullet (user_experience_id, bullet, bullet_order)
                    VALUES (%s, %s, %s)
                    """,
                    [experience_id, bullet.text, i],
                )

        pg_client.execute(
            """
            DELETE FROM user_base_skill WHERE user_id = %s
            """,
            [user_id],
        )

        sort_order = 0
        for skill_category in profile.skills:
            for skill in skill_category.skills:
                pg_client.execute(
                    """
                    INSERT INTO user_base_skill (user_id, name, category, sort_order)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id, name) DO NOTHING
                    """,
                    [user_id, skill, skill_category.category, sort_order],
                )
                sort_order += 1

        pg_client.execute(
            """
            DELETE FROM user_base_education WHERE user_id = %s
            """,
            [user_id],
        )

        for education in profile.education:
            pg_client.execute(
                """
                INSERT INTO user_base_education (user_id, institution, degree, field_of_study, start_date, end_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    user_id,
                    education.institution,
                    education.degree,
                    education.field_of_study,
                    education.start_date,
                    education.end_date,
                ],
            )

        pg_client.execute(
            """
            DELETE FROM user_base_project WHERE user_id = %s
            """,
            [user_id],
        )

        for project in profile.projects:
            pg_client.execute(
                """
                INSERT INTO user_base_project (user_id, name, link, description, start_date, end_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    user_id,
                    project.name,
                    project.link,
                    project.description,
                    project.start_date,
                    project.end_date,
                ],
            )
    return True

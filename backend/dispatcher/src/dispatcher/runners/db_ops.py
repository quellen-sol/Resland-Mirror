import json
import math
import time
from dataclasses import asdict

from openrouter import OpenRouter, errors
from psycopg import Connection
from psycopg.rows import class_row
from shared.docgen import FormatProfile

from ..agents.docx_parser import UserDocxProfile
from ..agents.suggestions import FetchSuggestionRow, SuggestionsResult
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


def set_suggestion_question(
    pg_client: Connection, session_id: str, question: str | None
):
    with pg_client.transaction():
        pg_client.execute(
            """
            UPDATE user_suggestion
            SET pending_question = %s, status = 'WAITING_FOR_INPUT'
            WHERE id = %s
            """,
            (question, session_id),
        )


def set_suggestion_result(
    pg_client: Connection, session_id: str, result: SuggestionsResult
):
    payload = json.dumps([asdict(s) for s in result.suggestions])
    with pg_client.transaction():
        pg_client.execute(
            """
            UPDATE user_suggestion
            SET result = %s, status = 'COMPLETED', pending_question = NULL
            WHERE id = %s
            """,
            (payload, session_id),
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


def set_tailor_question(pg_client: Connection, run_id: str, question: str | None):
    with pg_client.transaction():
        pg_client.execute(
            """
            UPDATE user_tailor_run
            SET pending_question = %s, status = 'WAITING_FOR_INPUT'
            WHERE id = %s
            """,
            (question, run_id),
        )


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


def upsert_resume_format(
    pg_client: Connection, user_id: str, fmt: FormatProfile, source_job_id: str
):
    """Store the layout profile captured from the user's uploaded doc — the
    renderer reads this back to regenerate a matching resume."""
    with pg_client.transaction():
        pg_client.execute(
            """
            INSERT INTO user_resume_format (user_id, format, source_job_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                format = EXCLUDED.format,
                source_job_id = EXCLUDED.source_job_id,
                captured_at = now()
            """,
            [user_id, fmt.to_json(), source_job_id],
        )


def _social_link_type(link: str) -> str:
    """Map a profile link onto the SocialLinkType enum (contract.prisma)."""
    low = link.lower()
    if "linkedin.com" in low:
        return "LINKEDIN"
    if "github.com" in low:
        return "GITHUB"
    return "WEBSITE"


def upsert_user_profile(pg_client: Connection, user_id: str, profile: UserDocxProfile):
    with pg_client.transaction():
        pg_client.execute(
            """
            INSERT INTO "user" (auth0_id, full_name, email, phone, location, summary)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (auth0_id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    email = EXCLUDED.email,
                    phone = EXCLUDED.phone,
                    location = EXCLUDED.location,
                    summary = EXCLUDED.summary
            """,
            [
                user_id,
                profile.basic_info.name,
                profile.basic_info.email,
                profile.basic_info.phone,
                profile.basic_info.location,
                profile.summary or None,
            ],
        )

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
        # Also from suggestions
        pg_client.execute(
            """
            DELETE FROM user_suggestion WHERE experience_id IN (
                SELECT id FROM user_base_experience WHERE user_id = %s
            )
            """,
            [user_id],
        )

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

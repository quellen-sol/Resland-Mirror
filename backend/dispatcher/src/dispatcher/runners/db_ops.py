import json
import math
from dataclasses import asdict

from psycopg import Connection
from psycopg.rows import class_row

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


class DbOpError(Exception):
    pass


# Charged when a job's model has no model_pricing row (e.g. the env-default
# model isn't in the catalog). Roughly gpt-5 rates — mid-tier, so unpriced
# models never run free.
FALLBACK_CREDITS_PER_1K_INPUT = 160
FALLBACK_CREDITS_PER_1K_OUTPUT = 1250


def record_token_usage(
    pg_client: Connection,
    *,
    user_id: str,
    job_kind: str,
    job_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> int:
    """Insert one token_usage row and deduct credits from the user's balance.
    Floors at 0 — a job that overruns still finishes. Returns credits charged."""
    if not input_tokens and not output_tokens:
        return 0

    row = pg_client.execute(
        """
        SELECT credits_per_1k_input, credits_per_1k_output
        FROM model_pricing WHERE id = %s
        """,
        (model,),
    ).fetchone()
    rate_in = row[0] if row else FALLBACK_CREDITS_PER_1K_INPUT
    rate_out = row[1] if row else FALLBACK_CREDITS_PER_1K_OUTPUT
    credits = math.ceil(
        (input_tokens * rate_in + output_tokens * rate_out) / 1000
    )

    with pg_client.transaction():
        pg_client.execute(
            """
            INSERT INTO token_usage
              (user_id, job_kind, job_id, model,
               input_tokens, output_tokens, credits_charged)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                job_kind,
                job_id,
                model,
                input_tokens,
                output_tokens,
                credits,
            ),
        )
        pg_client.execute(
            """
            UPDATE "user"
            SET token_balance = GREATEST(0, token_balance - %s)
            WHERE auth0_id = %s
            """,
            (credits, user_id),
        )
    return credits


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


def fetch_tailor_run(
    pg_client: Connection, run_id: str
) -> FetchTailorRunRow | None:
    with pg_client.cursor(row_factory=class_row(FetchTailorRunRow)) as cursor:
        return cursor.execute(
            """
            SELECT id, user_id, job_description, status, model
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
            SELECT name, category FROM user_base_skill WHERE user_id = %s
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


def upsert_user_profile(pg_client: Connection, user_id: str, profile: UserDocxProfile):
    with pg_client.transaction():
        pg_client.execute(
            """
            INSERT INTO "user" (auth0_id, full_name, email, phone, location)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (auth0_id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    email = EXCLUDED.email,
                    phone = EXCLUDED.phone,
                    location = EXCLUDED.location
            """,
            [
                user_id,
                profile.basic_info.name,
                profile.basic_info.email,
                profile.basic_info.phone,
                profile.basic_info.location,
            ],
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

        for skill_category in profile.skills:
            for skill in skill_category.skills:
                pg_client.execute(
                    """
                    INSERT INTO user_base_skill (user_id, name, category)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, name) DO NOTHING
                    """,
                    [user_id, skill, skill_category.category],
                )

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

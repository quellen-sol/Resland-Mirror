from typing import Any

from ..deps import PgConnection


async def _fetch_all(pg_conn: PgConnection, query: str, user_id: str) -> list[Any]:
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(query, [user_id])
        return await res.fetchall()


async def fetch_header(pg_conn: PgConnection, user_id: str):
    """(full_name, email, phone, location, summary), or None without a user row."""
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            SELECT full_name, email, phone, location, summary
            FROM "user" WHERE auth0_id = %s
            """,
            [user_id],
        )
        return await res.fetchone()


async def fetch_social_links(pg_conn: PgConnection, user_id: str):
    return await _fetch_all(
        pg_conn,
        "SELECT type, link FROM user_social_link WHERE user_id = %s ORDER BY id",
        user_id,
    )


async def fetch_experience_bullets(pg_conn: PgConnection, user_id: str):
    """One row per bullet (NULL bullet columns for a bullet-less experience),
    experiences newest first like the export and the tailor agent see them."""
    return await _fetch_all(
        pg_conn,
        """
        SELECT e.id, e.company_name, e.title, e.location, e.start_date,
               e.end_date, e.description, b.id, b.bullet
        FROM user_base_experience e
        LEFT JOIN user_base_experience_bullet b ON b.user_experience_id = e.id
        WHERE e.user_id = %s
        ORDER BY e.created_at DESC, e.id, b.bullet_order
        """,
        user_id,
    )


async def fetch_skills(pg_conn: PgConnection, user_id: str):
    return await _fetch_all(
        pg_conn,
        """
        SELECT name, category FROM user_base_skill
        WHERE user_id = %s ORDER BY sort_order, id
        """,
        user_id,
    )


async def fetch_education(pg_conn: PgConnection, user_id: str):
    return await _fetch_all(
        pg_conn,
        """
        SELECT institution, degree, field_of_study, start_date, end_date, description
        FROM user_base_education WHERE user_id = %s ORDER BY id
        """,
        user_id,
    )


async def fetch_projects(pg_conn: PgConnection, user_id: str):
    return await _fetch_all(
        pg_conn,
        """
        SELECT name, link, description, start_date, end_date
        FROM user_base_project WHERE user_id = %s ORDER BY id
        """,
        user_id,
    )

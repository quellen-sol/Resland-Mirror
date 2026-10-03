from dataclasses import dataclass
from datetime import datetime

from psycopg.rows import class_row

from ..deps import PgConnection


class _Unset:
    """Sentinel for "leave the column alone" in updates — distinct from
    None, which clears the nullable company_name/role columns."""


UNSET = _Unset()


@dataclass
class UserTailoredResumeRow:
    id: str
    user_id: str
    tailor_run_id: str | None
    company_name: str | None
    role: str | None
    job_description: str
    content: str
    s3_key: str | None
    source_hash: str | None
    generated_at: datetime | None
    created_at: datetime
    updated_at: datetime


async def create_tailored_resume(
    conn: PgConnection,
    tailored_id: str,
    user_id: str,
    tailor_run_id: str | None,
    company_name: str | None,
    role: str | None,
    job_description: str,
    content: str,
) -> str:
    """Insert a board entry, or return the existing row's id when the
    (user_id, tailor_run_id) unique constraint fires — saving a run twice
    must stay idempotent."""
    async with conn.cursor() as cursor:
        res = await cursor.execute(
            """
            INSERT INTO user_tailored_resume
                (id, user_id, tailor_run_id, company_name, role,
                 job_description, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, tailor_run_id) DO NOTHING
            """,
            (
                tailored_id,
                user_id,
                tailor_run_id,
                company_name,
                role,
                job_description,
                content,
            ),
        )
        if res.rowcount > 0 or tailor_run_id is None:
            return tailored_id
        res = await cursor.execute(
            """
            SELECT id FROM user_tailored_resume
            WHERE user_id = %s AND tailor_run_id = %s
            """,
            (user_id, tailor_run_id),
        )
        row = await res.fetchone()
        return row[0] if row else tailored_id


async def get_tailored_by_run(
    pg_conn: PgConnection, user_id: str, run_id: str
) -> str | None:
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(
            """
            SELECT id FROM user_tailored_resume
            WHERE user_id = %s AND tailor_run_id = %s
            """,
            (user_id, run_id),
        )
        row = await res.fetchone()
        return row[0] if row else None


async def get_tailored_resume(
    pg_conn: PgConnection, user_id: str, tailored_id: str
) -> UserTailoredResumeRow | None:
    async with pg_conn.cursor(
        row_factory=class_row(UserTailoredResumeRow)
    ) as cursor:
        res = await cursor.execute(
            """
            SELECT * FROM user_tailored_resume
            WHERE id = %s AND user_id = %s
            """,
            (tailored_id, user_id),
        )
        return await res.fetchone()


async def list_tailored_resumes(
    pg_conn: PgConnection, user_id: str
) -> list[UserTailoredResumeRow]:
    async with pg_conn.cursor(
        row_factory=class_row(UserTailoredResumeRow)
    ) as cursor:
        res = await cursor.execute(
            """
            SELECT * FROM user_tailored_resume
            WHERE user_id = %s ORDER BY created_at DESC
            """,
            (user_id,),
        )
        return await res.fetchall()


async def update_tailored_resume(
    conn: PgConnection,
    tailored_id: str,
    user_id: str,
    *,
    company_name: str | None | _Unset = UNSET,
    role: str | None | _Unset = UNSET,
    job_description: str | None = None,
    content: str | None = None,
) -> bool:
    sets: list[str] = []
    params: list = []
    if company_name is not UNSET:
        sets.append("company_name = %s")
        params.append(company_name)
    if role is not UNSET:
        sets.append("role = %s")
        params.append(role)
    if job_description is not None:
        sets.append("job_description = %s")
        params.append(job_description)
    if content is not None:
        sets.append("content = %s")
        params.append(content)
    if not sets:
        return True
    sets.append("updated_at = now()")
    params.extend([tailored_id, user_id])
    async with conn.cursor() as cursor:
        res = await cursor.execute(
            f"""
            UPDATE user_tailored_resume SET {", ".join(sets)}
            WHERE id = %s AND user_id = %s
            """,
            params,
        )
        return res.rowcount > 0


async def set_tailored_generated(
    conn: PgConnection,
    tailored_id: str,
    s3_key: str,
    source_hash: str,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            UPDATE user_tailored_resume
            SET s3_key = %s, source_hash = %s, generated_at = now()
            WHERE id = %s
            """,
            (s3_key, source_hash, tailored_id),
        )


async def delete_tailored_resume(
    conn: PgConnection, tailored_id: str, user_id: str
) -> bool:
    async with conn.cursor() as cursor:
        res = await cursor.execute(
            """
            DELETE FROM user_tailored_resume WHERE id = %s AND user_id = %s
            """,
            (tailored_id, user_id),
        )
        return res.rowcount > 0

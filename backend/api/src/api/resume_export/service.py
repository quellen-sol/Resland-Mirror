import io
from collections.abc import Iterable
from typing import Any

from botocore.exceptions import ClientError
from fastapi import HTTPException
from shared.docgen import (
    FormatProfile,
    ResumeContent,
    ResumeEducation,
    ResumeExperience,
    ResumeHeader,
    ResumeProject,
    ResumeSkillGroup,
    content_source_hash,
    default_format_profile,
    render_docx,
)
from shared.s3 import get_s3_client

from ..deps import PgConnection
from ..env_vars import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    S3_RESUME_BUCKET,
)
from . import model

GENERATED_KEY_TEMPLATE = "resumes/{user_id}/generated.docx"
TEMPLATE_ORIGINAL = "original"
# Short-lived — long enough to start the download, useless after.
PRESIGN_EXPIRY_SECONDS = 300


async def _fetch_one(pg_conn: PgConnection, query: str, params: Iterable[Any]):
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(query, list(params))
        return await res.fetchone()


async def _fetch_all(pg_conn: PgConnection, query: str, params: Iterable[Any] = ()):
    async with pg_conn.cursor() as cursor:
        res = await cursor.execute(query, list(params))
        return await res.fetchall()


async def _fetch_resume_content(pg_conn: PgConnection, user_id: str) -> ResumeContent:
    """Assemble the canonical render input from the user's stored profile —
    the same row set the tailor flow reads."""
    user = await _fetch_one(
        pg_conn,
        """
        SELECT full_name, email, phone, location, summary
        FROM "user" WHERE auth0_id = %s
        """,
        (user_id,),
    )
    links = await _fetch_all(
        pg_conn,
        "SELECT link FROM user_social_link WHERE user_id = %s",
        (user_id,),
    )
    exp_rows = await _fetch_all(
        pg_conn,
        """
        SELECT id, company_name, title, start_date, end_date
        FROM user_base_experience WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,),
    )
    bullet_rows = []
    if exp_rows:
        bullet_rows = await _fetch_all(
            pg_conn,
            """
            SELECT user_experience_id, bullet
            FROM user_base_experience_bullet
            WHERE user_experience_id = ANY(%s)
            ORDER BY bullet_order
            """,
            ([r[0] for r in exp_rows],),
        )
    bullets_by_exp: dict[int, list[str]] = {}
    for exp_id, bullet in bullet_rows:
        bullets_by_exp.setdefault(exp_id, []).append(bullet)

    skill_rows = await _fetch_all(
        pg_conn,
        "SELECT name, category FROM user_base_skill WHERE user_id = %s",
        (user_id,),
    )
    skills_by_cat: dict[str | None, list[str]] = {}
    for name, category in skill_rows:
        skills_by_cat.setdefault(category, []).append(name)

    edu_rows = await _fetch_all(
        pg_conn,
        """
        SELECT institution, degree, field_of_study, start_date, end_date, description
        FROM user_base_education WHERE user_id = %s
        """,
        (user_id,),
    )
    project_rows = await _fetch_all(
        pg_conn,
        """
        SELECT name, link, description, start_date, end_date
        FROM user_base_project WHERE user_id = %s
        """,
        (user_id,),
    )

    return ResumeContent(
        header=ResumeHeader(
            name=user[0] if user else None,
            email=user[1] if user else None,
            phone=user[2] if user else None,
            location=user[3] if user else None,
            links=[row[0] for row in links],
        ),
        summary=user[4] if user else None,
        experiences=[
            ResumeExperience(
                company=r[1],
                title=r[2],
                start_date=r[3],
                end_date=r[4],
                bullets=bullets_by_exp.get(r[0], []),
            )
            for r in exp_rows
        ],
        skill_groups=[
            ResumeSkillGroup(category=cat, skills=names)
            for cat, names in skills_by_cat.items()
        ],
        education=[
            ResumeEducation(
                institution=r[0],
                degree=r[1],
                field_of_study=r[2],
                start_date=r[3],
                end_date=r[4],
                description=r[5],
            )
            for r in edu_rows
        ],
        projects=[
            ResumeProject(
                name=r[0], link=r[1], description=r[2], start_date=r[3], end_date=r[4]
            )
            for r in project_rows
        ],
        source="base",
    )


async def _fetch_format_profile(pg_conn: PgConnection, user_id: str) -> FormatProfile:
    row = await _fetch_one(
        pg_conn,
        "SELECT format FROM user_resume_format WHERE user_id = %s",
        (user_id,),
    )
    if not row:
        return default_format_profile()
    try:
        return FormatProfile.from_json(row[0])
    except Exception:
        # A malformed stored profile shouldn't block export.
        return default_format_profile()


def _object_exists(s3_client, key: str) -> bool:
    try:
        s3_client.head_object(Bucket=S3_RESUME_BUCKET, Key=key)
        return True
    except ClientError:
        return False


async def export_resume(pg_conn: PgConnection, user_id: str):
    content = await _fetch_resume_content(pg_conn, user_id)
    has_content = any(
        [
            content.header.name,
            content.summary,
            content.experiences,
            content.skill_groups,
            content.education,
            content.projects,
        ]
    )
    if not has_content:
        raise HTTPException(
            status_code=409, detail="Upload and parse a resume before exporting"
        )

    s3_key = GENERATED_KEY_TEMPLATE.format(user_id=user_id)
    source_hash = content_source_hash(content, template=TEMPLATE_ORIGINAL)

    existing = await _fetch_one(
        pg_conn,
        """
        SELECT source_hash, generated_at FROM user_generated_resume
        WHERE user_id = %s
        """,
        (user_id,),
    )

    s3_client = get_s3_client(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    regenerated = False
    generated_at = existing[1] if existing else None
    stale = (
        not existing
        or existing[0] != source_hash
        or not _object_exists(s3_client, s3_key)
    )
    if stale:
        fmt = await _fetch_format_profile(pg_conn, user_id)
        docx_bytes = render_docx(content, fmt)
        s3_client.upload_fileobj(
            io.BytesIO(docx_bytes), S3_RESUME_BUCKET, s3_key
        )
        row = await _fetch_one(
            pg_conn,
            """
            INSERT INTO user_generated_resume (user_id, template, s3_key, source_hash)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                template = EXCLUDED.template,
                s3_key = EXCLUDED.s3_key,
                source_hash = EXCLUDED.source_hash,
                generated_at = now()
            RETURNING generated_at
            """,
            (user_id, TEMPLATE_ORIGINAL, s3_key, source_hash),
        )
        generated_at = row[0] if row else None
        regenerated = True

    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_RESUME_BUCKET, "Key": s3_key},
        ExpiresIn=PRESIGN_EXPIRY_SECONDS,
    )
    return model.ExportResumeResponse(
        url=url,
        generated_at=generated_at.isoformat() if generated_at else "",
        regenerated=regenerated,
    )

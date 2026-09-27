import io
import uuid
from contextlib import suppress

from fastapi import HTTPException
from pydantic import ValidationError
from shared.docgen import (
    ResumeContent,
    ResumeExperience,
    ResumeSkillGroup,
    content_source_hash,
    render_docx,
)
from shared.s3 import get_s3_client

from ..deps import PgConnection
from ..env_vars import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_RESUME_BUCKET
from ..resume_export import service as resume_export
from ..tailor import db as tailor_db
from ..tailor.model import MAX_TAILOR_FIELD_CHARS
from . import db, model

GENERATED_TAILORED_KEY_TEMPLATE = "resumes/{user_id}/tailored/{tailored_id}.docx"


def _clean(value: str | None, max_chars: int = MAX_TAILOR_FIELD_CHARS) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()[:max_chars]
    return cleaned or None


async def _experience_meta(
    pg_conn: PgConnection, user_id: str, exp_ids: list[int]
) -> dict[int, tuple]:
    """id → (company_name, title, start_date, end_date) for the run's refs."""
    if not exp_ids:
        return {}
    rows = await resume_export._fetch_all(
        pg_conn,
        """
        SELECT id, company_name, title, start_date, end_date
        FROM user_base_experience WHERE user_id = %s AND id = ANY(%s)
        """,
        (user_id, exp_ids),
    )
    return {r[0]: (r[1], r[2], r[3], r[4]) for r in rows}


async def _skill_categories(pg_conn: PgConnection, user_id: str) -> dict[str, str | None]:
    rows = await resume_export._fetch_all(
        pg_conn,
        "SELECT name, category FROM user_base_skill WHERE user_id = %s",
        (user_id,),
    )
    return {name: category for name, category in rows}


def _group_skills(
    names: list[str], categories: dict[str, str | None]
) -> list[model.TailoredSkillGroupContent]:
    """Fold ordered skill names into groups by first-appearance order — same
    semantics as the frontend's groupSkills."""
    groups: list[model.TailoredSkillGroupContent] = []
    by_category: dict[str | None, model.TailoredSkillGroupContent] = {}
    for raw in names:
        name = raw.strip()
        if not name:
            continue
        category = categories.get(name)
        group = by_category.get(category)
        if group is None:
            group = model.TailoredSkillGroupContent(category=category, skills=[])
            by_category[category] = group
            groups.append(group)
        group.skills.append(name)
    return groups


async def save_from_run(pg_conn: PgConnection, user_id: str, run_id: str) -> str:
    """Snapshot a COMPLETED tailor run into a board entry. The snapshot stores
    display-ready content (experience metadata + skill categories resolved)
    so it survives base-profile re-uploads that rebuild the base tables."""
    run = await tailor_db.get_tailor_run(pg_conn, user_id=user_id, run_id=run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Tailor run not found")
    if run.status != "COMPLETED" or not run.result:
        raise HTTPException(status_code=409, detail="Tailor run is not finished")
    try:
        result = model.TailorRunResult.model_validate_json(run.result)
    except ValidationError:
        raise HTTPException(status_code=409, detail="Tailor result is unreadable")

    exp_meta = await _experience_meta(
        pg_conn, user_id, [e.experience_id for e in result.experiences]
    )
    experiences: list[model.TailoredExperienceContent] = []
    for exp in result.experiences:
        meta = exp_meta.get(exp.experience_id)
        if meta is None:
            # Base row is gone (e.g. profile re-uploaded) — drop the dangling
            # reference rather than saving a resume with blank entries.
            continue
        experiences.append(
            model.TailoredExperienceContent(
                company_name=meta[0],
                title=meta[1],
                start_date=meta[2],
                end_date=meta[3],
                bullets=[b.text for b in exp.bullets],
            )
        )
    if not experiences:
        raise HTTPException(
            status_code=409,
            detail="The tailored result references a profile that no longer exists — tailor again",
        )

    skill_cats = await _skill_categories(pg_conn, user_id)
    content = model.TailoredContent(
        summary=result.summary,
        experiences=experiences,
        skill_groups=_group_skills(result.skills, skill_cats),
    )

    tailored_id = str(uuid.uuid4())
    await db.create_tailored_resume(
        pg_conn,
        tailored_id=tailored_id,
        user_id=user_id,
        tailor_run_id=run_id,
        company_name=_clean(run.company_name),
        role=_clean(run.role),
        job_description=run.job_description,
        content=content.model_dump_json(),
    )
    return tailored_id


def _to_list_item(row: db.UserTailoredResumeRow) -> model.TailoredResumeListItem:
    return model.TailoredResumeListItem(
        id=row.id,
        company_name=row.company_name,
        role=row.role,
        created_at=row.created_at.isoformat(),
        generated_at=row.generated_at.isoformat() if row.generated_at else None,
    )


def _to_response(row: db.UserTailoredResumeRow) -> model.TailoredResumeResponse:
    content = model.TailoredContent.model_validate_json(row.content)
    return model.TailoredResumeResponse(
        id=row.id,
        company_name=row.company_name,
        role=row.role,
        job_description=row.job_description,
        content=content,
        created_at=row.created_at.isoformat(),
        updated_at=row.updated_at.isoformat(),
        generated_at=row.generated_at.isoformat() if row.generated_at else None,
    )


async def list_tailored(
    pg_conn: PgConnection, user_id: str
) -> model.TailoredListResponse:
    rows = await db.list_tailored_resumes(pg_conn, user_id)
    return model.TailoredListResponse(items=[_to_list_item(r) for r in rows])


async def get_tailored(
    pg_conn: PgConnection, user_id: str, tailored_id: str
) -> model.TailoredResumeResponse:
    row = await db.get_tailored_resume(pg_conn, user_id, tailored_id)
    if not row:
        raise HTTPException(status_code=404, detail="Tailored resume not found")
    return _to_response(row)


async def update_tailored(
    pg_conn: PgConnection,
    user_id: str,
    tailored_id: str,
    req: model.UpdateTailoredRequest,
) -> model.TailoredResumeResponse:
    # Explicit null clears the nullable fields; an absent field is untouched.
    provided = req.model_fields_set
    updated = await db.update_tailored_resume(
        pg_conn,
        tailored_id,
        user_id,
        company_name=_clean(req.company_name)
        if "company_name" in provided
        else db.UNSET,
        role=_clean(req.role) if "role" in provided else db.UNSET,
        job_description=req.job_description,
        content=req.content.model_dump_json() if req.content is not None else None,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Tailored resume not found")
    return await get_tailored(pg_conn, user_id, tailored_id)


async def delete_tailored(
    pg_conn: PgConnection, user_id: str, tailored_id: str
) -> dict:
    row = await db.get_tailored_resume(pg_conn, user_id, tailored_id)
    if not row:
        raise HTTPException(status_code=404, detail="Tailored resume not found")
    await db.delete_tailored_resume(pg_conn, tailored_id, user_id)
    if row.s3_key:
        # Generated docx cleanup is best-effort — the row is gone either way.
        with suppress(Exception):
            s3_client = get_s3_client(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            )
            s3_client.delete_object(Bucket=S3_RESUME_BUCKET, Key=row.s3_key)
    return {"ok": True}


def _tailored_render_content(
    row: db.UserTailoredResumeRow, base: ResumeContent
) -> ResumeContent:
    snapshot = model.TailoredContent.model_validate_json(row.content)
    return ResumeContent(
        header=base.header,
        summary=snapshot.summary,
        experiences=[
            ResumeExperience(
                company=e.company_name,
                title=e.title,
                start_date=e.start_date,
                end_date=e.end_date,
                bullets=[b for b in e.bullets if b.strip()],
            )
            for e in snapshot.experiences
        ],
        skill_groups=[
            ResumeSkillGroup(category=g.category, skills=g.skills)
            for g in snapshot.skill_groups
            if g.skills
        ],
        education=base.education,
        projects=base.projects,
        source=f"tailored:{row.id}",
    )


async def export_tailored(
    pg_conn: PgConnection, user_id: str, tailored_id: str
) -> model.ExportTailoredResponse:
    row = await db.get_tailored_resume(pg_conn, user_id, tailored_id)
    if not row:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    # Header/education/projects aren't tailored — read them live from the
    # base profile so fixes there propagate to every saved resume.
    base = await resume_export._fetch_resume_content(pg_conn, user_id)
    content = _tailored_render_content(row, base)

    s3_key = GENERATED_TAILORED_KEY_TEMPLATE.format(
        user_id=user_id, tailored_id=tailored_id
    )
    fmt = await resume_export._fetch_format_profile(pg_conn, user_id)
    source_hash = content_source_hash(
        content, template=resume_export.TEMPLATE_ORIGINAL, fmt=fmt
    )

    s3_client = get_s3_client(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    regenerated = False
    stale = (
        row.source_hash != source_hash
        or not resume_export._object_exists(s3_client, s3_key)
    )
    if stale:
        docx_bytes = render_docx(content, fmt)
        s3_client.upload_fileobj(io.BytesIO(docx_bytes), S3_RESUME_BUCKET, s3_key)
        await db.set_tailored_generated(pg_conn, tailored_id, s3_key, source_hash)
        regenerated = True

    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_RESUME_BUCKET, "Key": s3_key},
        ExpiresIn=resume_export.PRESIGN_EXPIRY_SECONDS,
    )
    fresh = await db.get_tailored_resume(pg_conn, user_id, tailored_id)
    generated_at = fresh.generated_at if fresh else row.generated_at
    return model.ExportTailoredResponse(
        url=url,
        generated_at=generated_at.isoformat() if generated_at else "",
        regenerated=regenerated,
    )

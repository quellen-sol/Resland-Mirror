from fastapi import HTTPException

from ..deps import PgConnection
from . import db, model


async def get_profile(pg_conn: PgConnection, user_id: str) -> model.ProfileResponse:
    header = await db.fetch_header(pg_conn, user_id)
    if header is None:
        raise HTTPException(status_code=404, detail="Account not found")
    links = await db.fetch_social_links(pg_conn, user_id)

    experiences: dict[int, model.ProfileExperience] = {}
    for (
        exp_id,
        company,
        title,
        start,
        end,
        desc,
        bullet_id,
        bullet,
    ) in await db.fetch_experience_bullets(pg_conn, user_id):
        exp = experiences.get(exp_id)
        if exp is None:
            exp = experiences[exp_id] = model.ProfileExperience(
                id=exp_id,
                company_name=company,
                title=title,
                start_date=start,
                end_date=end,
                description=desc,
                bullets=[],
            )
        if bullet_id is not None:
            exp.bullets.append(model.ProfileBullet(id=bullet_id, text=bullet))

    skills = await db.fetch_skills(pg_conn, user_id)
    education = await db.fetch_education(pg_conn, user_id)
    projects = await db.fetch_projects(pg_conn, user_id)
    full_name, email, phone, location, summary = header
    return model.ProfileResponse(
        full_name=full_name,
        email=email,
        phone=phone,
        location=location,
        summary=summary,
        social_links=[model.ProfileSocialLink(type=t, link=link) for t, link in links],
        experiences=list(experiences.values()),
        skills=[model.ProfileSkill(name=n, category=c) for n, c in skills],
        education=[
            model.ProfileEducation(
                institution=r[0],
                degree=r[1],
                field_of_study=r[2],
                start_date=r[3],
                end_date=r[4],
                description=r[5],
            )
            for r in education
        ],
        projects=[
            model.ProfileProject(
                name=r[0], link=r[1], description=r[2], start_date=r[3], end_date=r[4]
            )
            for r in projects
        ],
    )

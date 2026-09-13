from psycopg import Connection

from ..agents.docx_parser import UserDocxProfile


class DbOpError(Exception):
    pass


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

            for bullet in experience.bullets:
                pg_client.execute(
                    """
                    INSERT INTO user_base_experience_bullet (user_experience_id, bullet)
                    VALUES (%s, %s)
                    """,
                    [experience_id, bullet.text],
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

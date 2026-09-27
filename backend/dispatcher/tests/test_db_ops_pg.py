"""db_ops tests beyond record_token_usage — real SQL against a live
Postgres (TEST_PG_URL, default the compose creds). Skips cleanly when no
database is reachable, matching conftest's convention.

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_db_ops_pg -v
     (from the repo root with the workspace venv)
"""

import json
import os
import unittest

import psycopg

from shared.docgen import FormatProfile

from dispatcher.agents.docx_parser import (
    UserDocxProfile,
    UserEducationEntry,
    UserExperienceBullet,
    UserProfileBasicInfo,
    UserProfileExperienceEntry,
    UserProjectEntry,
    UserSkillByCategory,
)
from dispatcher.agents.suggestions import BulletSuggestion, SuggestionsResult
from dispatcher.agents.tailor import (
    TailoredBullet,
    TailoredExperience,
    TailoredResume,
)
from dispatcher.runners import db_ops

TEST_PG_URL = os.getenv(
    "TEST_PG_URL", "postgres://resland:resland@localhost:5432/resland"
)


def _pg_reachable() -> bool:
    try:
        conn = psycopg.connect(TEST_PG_URL, connect_timeout=3, autocommit=True)
    except Exception:
        return False
    conn.close()
    return True


@unittest.skipUnless(_pg_reachable(), f"needs Postgres at {TEST_PG_URL}")
class DbOpsPg(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = psycopg.connect(TEST_PG_URL, autocommit=True)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def setUp(self):
        self.conn.execute(
            'TRUNCATE user_resume_format, user_suggestion, user_tailor_run,'
            ' user_base_experience_bullet, user_base_experience,'
            ' user_base_skill, user_base_education, user_base_project,'
            ' user_social_link, user_upload_job, model_pricing,'
            ' token_usage, balance_purchase, "user" CASCADE'
        )

    # Seeds ------------------------------------------------------------

    def _user(self, uid="u1", **fields):
        cols = {"full_name": None, "email": None, "phone": None, "location": None}
        cols.update(fields)
        self.conn.execute(
            'INSERT INTO "user" (auth0_id, full_name, email, phone, location)'
            " VALUES (%s, %s, %s, %s, %s)",
            (uid, cols["full_name"], cols["email"], cols["phone"], cols["location"]),
        )
        return uid

    def _experience(self, uid="u1", company="Acme", title="Eng", created_at=None):
        row = self.conn.execute(
            "INSERT INTO user_base_experience"
            " (user_id, company_name, title, start_date, created_at)"
            " VALUES (%s, %s, %s, '2020', COALESCE(%s, now())) RETURNING id",
            (uid, company, title, created_at),
        ).fetchone()
        return row[0]

    def _bullet(self, exp_id, text="Did a thing", order=0):
        row = self.conn.execute(
            "INSERT INTO user_base_experience_bullet"
            " (user_experience_id, bullet, bullet_order)"
            " VALUES (%s, %s, %s) RETURNING id",
            (exp_id, text, order),
        ).fetchone()
        return row[0]

    def _suggestion(self, sid, uid, exp_id, bullet_id=None, model=None):
        self.conn.execute(
            "INSERT INTO user_suggestion (id, user_id, experience_id, bullet_id, model)"
            " VALUES (%s, %s, %s, %s, %s)",
            (sid, uid, exp_id, bullet_id, model),
        )

    def _tailor_run(self, rid, uid, model=None):
        self.conn.execute(
            "INSERT INTO user_tailor_run (id, user_id, job_description, model)"
            " VALUES (%s, %s, 'A job', %s)",
            (rid, uid, model),
        )

    def _pricing(self, pid, enabled=True, is_default=False, sort_order=0):
        self.conn.execute(
            "INSERT INTO model_pricing"
            " (id, display_name, cents_per_1k_input, cents_per_1k_output,"
            "  enabled, is_default, sort_order)"
            " VALUES (%s, 'X', 1, 1, %s, %s, %s)",
            (pid, enabled, is_default, sort_order),
        )

    # default_model_spec -----------------------------------------------

    def test_default_model_spec_none_when_table_empty(self):
        self.assertIsNone(db_ops.default_model_spec(self.conn))

    def test_default_model_spec_returns_enabled_default(self):
        self._pricing("openrouter:a", is_default=True)
        self.assertEqual(db_ops.default_model_spec(self.conn), "openrouter:a")

    def test_default_model_spec_ignores_disabled(self):
        self._pricing("openrouter:a", enabled=False, is_default=True)
        self.assertIsNone(db_ops.default_model_spec(self.conn))

    def test_default_model_spec_ignores_non_default(self):
        self._pricing("openrouter:a", enabled=True, is_default=False)
        self.assertIsNone(db_ops.default_model_spec(self.conn))

    def test_default_model_spec_picks_lowest_sort_order(self):
        self._pricing("openrouter:hi", is_default=True, sort_order=5)
        self._pricing("openrouter:lo", is_default=True, sort_order=1)
        self.assertEqual(db_ops.default_model_spec(self.conn), "openrouter:lo")

    # fetch_suggestion_rows --------------------------------------------

    def test_fetch_suggestion_rows_orders_bullets(self):
        self._user()
        exp = self._experience(company="Acme", title="Engineer")
        b1 = self._bullet(exp, "first", order=0)
        b2 = self._bullet(exp, "second", order=1)
        self._suggestion("s1", "u1", exp, model="openrouter:m")

        rows = db_ops.fetch_suggestion_rows(self.conn, "s1")
        self.assertEqual([r.bullet_id for r in rows], [b1, b2])
        row = rows[0]
        self.assertEqual(row.user_id, "u1")
        self.assertEqual(row.company_name, "Acme")
        self.assertEqual(row.title, "Engineer")
        self.assertEqual(row.bullet, "first")
        self.assertEqual(row.model, "openrouter:m")
        self.assertEqual(row.status, "PROCESSING")

    def test_fetch_suggestion_rows_filters_to_chosen_bullet(self):
        self._user()
        exp = self._experience()
        b1 = self._bullet(exp, "first", order=0)
        self._bullet(exp, "second", order=1)
        self._suggestion("s1", "u1", exp, bullet_id=b1)

        rows = db_ops.fetch_suggestion_rows(self.conn, "s1")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].bullet_id, b1)

    def test_fetch_suggestion_rows_empty_for_unknown_session(self):
        self.assertEqual(db_ops.fetch_suggestion_rows(self.conn, "nope"), [])

    # suggestion writes -------------------------------------------------

    def test_set_suggestion_question(self):
        self._user()
        exp = self._experience()
        self._suggestion("s1", "u1", exp)
        db_ops.set_suggestion_question(self.conn, "s1", "Team size?")
        row = self.conn.execute(
            "SELECT pending_question, status FROM user_suggestion WHERE id='s1'"
        ).fetchone()
        self.assertEqual(row, ("Team size?", "WAITING_FOR_INPUT"))

    def test_set_suggestion_result(self):
        self._user()
        exp = self._experience()
        self._suggestion("s1", "u1", exp)
        db_ops.set_suggestion_question(self.conn, "s1", "q")
        db_ops.set_suggestion_result(
            self.conn,
            "s1",
            SuggestionsResult(
                suggestions=[BulletSuggestion(bullet_id=3, suggestion="rewrote it")]
            ),
        )
        row = self.conn.execute(
            "SELECT status, pending_question, result FROM user_suggestion"
            " WHERE id='s1'"
        ).fetchone()
        self.assertEqual(row[0], "COMPLETED")
        self.assertIsNone(row[1])
        self.assertEqual(
            json.loads(row[2]),
            [{"bullet_id": 3, "suggestion": "rewrote it"}],
        )

    def test_set_suggestion_failed_marks_failed(self):
        self._user()
        exp = self._experience()
        self._suggestion("s1", "u1", exp)
        db_ops.set_suggestion_failed(self.conn, "s1")
        status = self.conn.execute(
            "SELECT status FROM user_suggestion WHERE id='s1'"
        ).fetchone()[0]
        self.assertEqual(status, "FAILED")

    def test_set_suggestion_failed_preserves_completed_and_waiting(self):
        self._user()
        exp = self._experience()
        self._suggestion("s1", "u1", exp)
        self._suggestion("s2", "u1", exp)
        self.conn.execute(
            "UPDATE user_suggestion SET status='COMPLETED' WHERE id='s1'"
        )
        self.conn.execute(
            "UPDATE user_suggestion SET status='WAITING_FOR_INPUT' WHERE id='s2'"
        )
        db_ops.set_suggestion_failed(self.conn, "s1")
        db_ops.set_suggestion_failed(self.conn, "s2")
        statuses = self.conn.execute(
            "SELECT id, status FROM user_suggestion ORDER BY id"
        ).fetchall()
        self.assertEqual(
            statuses, [("s1", "COMPLETED"), ("s2", "WAITING_FOR_INPUT")]
        )

    # tailor ------------------------------------------------------------

    def test_fetch_tailor_run(self):
        self._user()
        self._tailor_run("r1", "u1", model="openrouter:m")
        row = db_ops.fetch_tailor_run(self.conn, "r1")
        self.assertEqual(row.id, "r1")
        self.assertEqual(row.user_id, "u1")
        self.assertEqual(row.job_description, "A job")
        self.assertEqual(row.model, "openrouter:m")

    def test_fetch_tailor_run_missing_returns_none(self):
        self.assertIsNone(db_ops.fetch_tailor_run(self.conn, "nope"))

    def test_fetch_tailor_profile_reads_everything(self):
        self._user(
            full_name="Jane", email="j@x.com", phone="555", location="NYC"
        )
        self.conn.execute(
            "INSERT INTO user_social_link (user_id, link, type)"
            " VALUES ('u1', 'https://gh', 'GITHUB')",
        )
        e_new = self._experience(company="NewCo", created_at="2024-01-01")
        e_old = self._experience(company="OldCo", created_at="2020-01-01")
        self._bullet(e_old, "old b", order=0)
        self._bullet(e_new, "new b", order=0)
        self.conn.execute(
            "INSERT INTO user_base_skill (user_id, name, category)"
            " VALUES ('u1', 'Python', 'Langs')",
        )
        self.conn.execute(
            "INSERT INTO user_base_education"
            " (user_id, institution, degree, field_of_study, start_date)"
            " VALUES ('u1', 'MIT', 'BS', 'CS', '2016')",
        )
        self.conn.execute(
            "INSERT INTO user_base_project"
            " (user_id, name, link, description, start_date)"
            " VALUES ('u1', 'Proj', 'https://p', 'desc', '2019')",
        )

        profile = db_ops.fetch_tailor_profile(self.conn, "u1")
        self.assertEqual(profile.header.full_name, "Jane")
        self.assertEqual([l.link for l in profile.social_links], ["https://gh"])
        # Newest experience first.
        self.assertEqual(
            [e.company_name for e in profile.experiences], ["NewCo", "OldCo"]
        )
        self.assertEqual(profile.experiences[0].bullet, "new b")
        self.assertEqual(profile.skills[0].name, "Python")
        self.assertEqual(profile.education[0].institution, "MIT")
        self.assertEqual(profile.projects[0].name, "Proj")

    def test_fetch_tailor_profile_orders_skills_by_sort_order(self):
        self._user()
        for name, category, order in [
            ("AWS", "Cloud", 2),
            ("Go", "Langs", 0),
            ("Git", None, 3),
            ("Rust", "Langs", 1),
        ]:
            self.conn.execute(
                "INSERT INTO user_base_skill (user_id, name, category, sort_order)"
                " VALUES ('u1', %s, %s, %s)",
                (name, category, order),
            )
        profile = db_ops.fetch_tailor_profile(self.conn, "u1")
        self.assertEqual(
            [(s.name, s.category) for s in profile.skills],
            [
                ("Go", "Langs"),
                ("Rust", "Langs"),
                ("AWS", "Cloud"),
                ("Git", None),
            ],
        )

    def test_fetch_tailor_profile_unknown_user_is_empty(self):
        profile = db_ops.fetch_tailor_profile(self.conn, "ghost")
        self.assertIsNone(profile.header)
        self.assertEqual(profile.experiences, [])

    def test_set_tailor_question(self):
        self._user()
        self._tailor_run("r1", "u1")
        db_ops.set_tailor_question(self.conn, "r1", "Want a summary?")
        row = self.conn.execute(
            "SELECT pending_question, status FROM user_tailor_run WHERE id='r1'"
        ).fetchone()
        self.assertEqual(row, ("Want a summary?", "WAITING_FOR_INPUT"))

    def test_set_tailor_result(self):
        self._user()
        self._tailor_run("r1", "u1")
        db_ops.set_tailor_result(
            self.conn,
            "r1",
            TailoredResume(
                summary=None,
                experiences=[
                    TailoredExperience(
                        experience_id=1,
                        bullets=[TailoredBullet(bullet_id=2, text="x")],
                    )
                ],
                skills=["Python"],
            ),
        )
        row = self.conn.execute(
            "SELECT status, result FROM user_tailor_run WHERE id='r1'"
        ).fetchone()
        self.assertEqual(row[0], "COMPLETED")
        self.assertEqual(json.loads(row[1])["skills"], ["Python"])

    def test_set_tailor_question_can_store_result(self):
        self._user()
        self._tailor_run("r1", "u1")
        resume = TailoredResume(
            summary=None,
            experiences=[
                TailoredExperience(
                    experience_id=1,
                    bullets=[TailoredBullet(bullet_id=2, text="x")],
                )
            ],
            skills=["Go"],
        )
        db_ops.set_tailor_question(self.conn, "r1", "Review?", result=resume)
        row = self.conn.execute(
            "SELECT pending_question, status, result"
            " FROM user_tailor_run WHERE id='r1'"
        ).fetchone()
        self.assertEqual(row[0], "Review?")
        self.assertEqual(row[1], "WAITING_FOR_INPUT")
        self.assertEqual(json.loads(row[2])["skills"], ["Go"])

        # A later waiting write without a result keeps the stored one.
        db_ops.set_tailor_question(self.conn, "r1", "Review again?")
        row = self.conn.execute(
            "SELECT result FROM user_tailor_run WHERE id='r1'"
        ).fetchone()
        self.assertEqual(json.loads(row[0])["skills"], ["Go"])

    def test_complete_tailor_run_requires_result(self):
        self._user()
        self._tailor_run("r1", "u1")
        # No result yet — nothing to complete.
        self.assertFalse(db_ops.complete_tailor_run(self.conn, "r1"))
        status = self.conn.execute(
            "SELECT status FROM user_tailor_run WHERE id='r1'"
        ).fetchone()[0]
        self.assertEqual(status, "PROCESSING")

        db_ops.set_tailor_question(
            self.conn,
            "r1",
            "Review?",
            result=TailoredResume(
                summary=None,
                experiences=[
                    TailoredExperience(
                        experience_id=1,
                        bullets=[TailoredBullet(bullet_id=2, text="x")],
                    )
                ],
                skills=[],
            ),
        )
        self.assertTrue(db_ops.complete_tailor_run(self.conn, "r1"))
        row = self.conn.execute(
            "SELECT status, pending_question FROM user_tailor_run WHERE id='r1'"
        ).fetchone()
        self.assertEqual(row, ("COMPLETED", None))

    def test_set_tailor_failed_marks_failed(self):
        self._user()
        self._tailor_run("r1", "u1")
        db_ops.set_tailor_failed(self.conn, "r1")
        status = self.conn.execute(
            "SELECT status FROM user_tailor_run WHERE id='r1'"
        ).fetchone()[0]
        self.assertEqual(status, "FAILED")

    def test_set_tailor_failed_preserves_completed(self):
        self._user()
        self._tailor_run("r1", "u1")
        self.conn.execute(
            "UPDATE user_tailor_run SET status='COMPLETED' WHERE id='r1'"
        )
        db_ops.set_tailor_failed(self.conn, "r1")
        status = self.conn.execute(
            "SELECT status FROM user_tailor_run WHERE id='r1'"
        ).fetchone()[0]
        self.assertEqual(status, "COMPLETED")

    # upserts -------------------------------------------------------------

    def test_upsert_resume_format_insert_then_update(self):
        self._user()
        db_ops.upsert_resume_format(
            self.conn, "u1", FormatProfile(columns=2), "job-1"
        )
        row = self.conn.execute(
            "SELECT format, source_job_id FROM user_resume_format"
            " WHERE user_id='u1'"
        ).fetchone()
        self.assertEqual(json.loads(row[0])["columns"], 2)
        self.assertEqual(row[1], "job-1")

        db_ops.upsert_resume_format(
            self.conn, "u1", FormatProfile(columns=3), "job-2"
        )
        row = self.conn.execute(
            "SELECT format, source_job_id FROM user_resume_format"
            " WHERE user_id='u1'"
        ).fetchone()
        self.assertEqual(json.loads(row[0])["columns"], 3)
        self.assertEqual(row[1], "job-2")
        count = self.conn.execute(
            "SELECT count(*) FROM user_resume_format WHERE user_id='u1'"
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_upsert_user_profile_writes_all_sections(self):
        profile = UserDocxProfile(
            summary="A summary",
            basic_info=UserProfileBasicInfo(
                name="Jane", email="j@x.com", phone="1", location="NYC"
            ),
            experience=[
                UserProfileExperienceEntry(
                    company="Acme",
                    position="Eng",
                    start_date="2020",
                    end_date="2023",
                    bullets=[UserExperienceBullet(text="b1")],
                )
            ],
            skills=[UserSkillByCategory(category="Langs", skills=["Python"])],
            education=[
                UserEducationEntry(
                    institution="MIT",
                    degree="BS",
                    field_of_study="CS",
                    start_date="2016",
                    end_date="2020",
                    description="",
                )
            ],
            projects=[
                UserProjectEntry(
                    name="Proj",
                    link="https://p",
                    description="d",
                    start_date="2019",
                    end_date="2020",
                )
            ],
        )
        db_ops.upsert_user_profile(self.conn, "u1", profile)

        row = self.conn.execute(
            'SELECT full_name, email, summary FROM "user" WHERE auth0_id=%s',
            ("u1",),
        ).fetchone()
        self.assertEqual(row, ("Jane", "j@x.com", "A summary"))
        for table in (
            "user_base_experience",
            "user_base_experience_bullet",
            "user_base_skill",
            "user_base_education",
            "user_base_project",
        ):
            n = self.conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            self.assertEqual(n, 1, table)

    def test_upsert_user_profile_writes_skill_sort_order(self):
        self._user()
        profile = UserDocxProfile(
            summary="",
            basic_info=UserProfileBasicInfo(
                name="Jane", email="", phone="", location=""
            ),
            experience=[],
            skills=[
                UserSkillByCategory(category="Langs", skills=["Go", "Rust"]),
                UserSkillByCategory(category="Cloud", skills=["AWS"]),
            ],
            education=[],
            projects=[],
        )
        db_ops.upsert_user_profile(self.conn, "u1", profile)
        rows = self.conn.execute(
            "SELECT name, category, sort_order FROM user_base_skill"
            " WHERE user_id='u1' ORDER BY sort_order"
        ).fetchall()
        self.assertEqual(
            rows,
            [("Go", "Langs", 0), ("Rust", "Langs", 1), ("AWS", "Cloud", 2)],
        )

    def test_upsert_user_profile_replaces_prior_sections(self):
        self._user()
        old_exp = self._experience(company="OldCo")
        self._bullet(old_exp, "old bullet")
        self.conn.execute(
            "INSERT INTO user_base_skill (user_id, name) VALUES ('u1', 'Old')",
        )
        profile = UserDocxProfile(
            summary="",
            basic_info=UserProfileBasicInfo(
                name="Jane", email="", phone="", location=""
            ),
            experience=[
                UserProfileExperienceEntry(
                    company="NewCo",
                    position="Eng",
                    start_date="2024",
                    end_date="",
                    bullets=[],
                )
            ],
            skills=[UserSkillByCategory(category="", skills=["New"])],
            education=[],
            projects=[],
        )
        db_ops.upsert_user_profile(self.conn, "u1", profile)

        companies = [
            r[0]
            for r in self.conn.execute(
                "SELECT company_name FROM user_base_experience WHERE user_id='u1'"
            ).fetchall()
        ]
        self.assertEqual(companies, ["NewCo"])
        skills = [
            r[0]
            for r in self.conn.execute(
                "SELECT name FROM user_base_skill WHERE user_id='u1'"
            ).fetchall()
        ]
        self.assertEqual(skills, ["New"])
        self.assertEqual(
            self.conn.execute(
                "SELECT count(*) FROM user_base_experience_bullet"
            ).fetchone()[0],
            0,
        )


if __name__ == "__main__":
    unittest.main()

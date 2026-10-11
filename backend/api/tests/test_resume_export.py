"""resume_export service — content assembly from profile tables, stored
format handling, staleness/regeneration logic, presigned URL.

Run: .venv/bin/python -m unittest backend.api.tests.test_resume_export -v
"""

import datetime
import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from fastapi import HTTPException
from shared.docgen import default_format_profile

from api.resume_export import service

from .helpers import _Pg, _Result, one

USER_ROW = one((1,))  # share_user_row's lock found the account


def _content_pg():
    """Row sets for _fetch_resume_content: user, links, experiences,
    bullets, skills, education, projects."""
    return _Pg(
        [
            [("Jane", "j@x.com", "555", "NYC", "My summary")],  # user
            [("https://gh",)],  # links
            [(11, "Acme", "Eng", "2020", None, "Remote")],  # experiences
            [(11, "Built x"), (11, "Shipped y")],  # bullets
            [("Python", "Langs"), ("Go", "Langs")],  # skills
            [("MIT", "BS", "CS", "2016", "2020", "")],  # education
            [("Proj", "https://p", "d", "2019", "2020")],  # projects
        ]
    )


class FetchResumeContent(unittest.IsolatedAsyncioTestCase):
    async def test_assembles_content(self):
        content = await service._fetch_resume_content(_content_pg(), "u1")
        self.assertEqual(content.header.name, "Jane")
        self.assertEqual(content.header.links, ["https://gh"])
        self.assertEqual(content.summary, "My summary")
        self.assertEqual(len(content.experiences), 1)
        self.assertEqual(
            content.experiences[0].bullets, ["Built x", "Shipped y"]
        )
        self.assertEqual(content.experiences[0].location, "Remote")
        self.assertEqual(content.skill_groups[0].skills, ["Python", "Go"])
        self.assertEqual(content.education[0].institution, "MIT")
        self.assertEqual(content.projects[0].name, "Proj")
        self.assertEqual(content.source, "base")

    async def test_skill_groups_follow_row_order(self):
        # Rows arrive in sort_order; a category's group holds every skill
        # that shares its name, uncategorized skills land in a None group.
        pg = _Pg(
            [
                [("Jane", "j@x.com", "555", "NYC", None)],
                [],
                # Empty experiences skip the bullets query entirely.
                [],
                [
                    ("Go", "Langs"),
                    ("Git", None),
                    ("Rust", "Langs"),
                    ("AWS", "Cloud"),
                ],
                [],
                [],
            ]
        )
        content = await service._fetch_resume_content(pg, "u1")
        self.assertEqual(
            [(g.category, g.skills) for g in content.skill_groups],
            [("Langs", ["Go", "Rust"]), (None, ["Git"]), ("Cloud", ["AWS"])],
        )
        # The skills query is the 4th execute (user, links, exps).
        self.assertIn("ORDER BY sort_order", pg.queries[3][0])

    async def test_missing_user_gives_none_header(self):
        pg = _Pg([[], [], [], [], [], [], []])
        content = await service._fetch_resume_content(pg, "ghost")
        self.assertIsNone(content.header.name)
        self.assertEqual(content.experiences, [])


class FetchFormatProfile(unittest.IsolatedAsyncioTestCase):
    async def test_no_row_defaults(self):
        fmt = await service._fetch_format_profile(_Pg([[]]), "u1")
        self.assertEqual(fmt, default_format_profile())

    async def test_valid_row_parsed(self):
        stored = default_format_profile()
        stored.contact_separator = "·"
        stored.columns = 2
        pg = _Pg([[(stored.to_json(),)]])
        fmt = await service._fetch_format_profile(pg, "u1")
        self.assertEqual(fmt.contact_separator, "·")
        self.assertEqual(fmt.columns, 2)

    async def test_malformed_row_defaults(self):
        pg = _Pg([[("not-json{",)]])
        fmt = await service._fetch_format_profile(pg, "u1")
        self.assertEqual(fmt, default_format_profile())


class ObjectExists(unittest.TestCase):
    def test_present(self):
        self.assertTrue(service._object_exists(MagicMock(), "k"))

    def test_client_error_absent(self):
        s3 = MagicMock()
        s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "HeadObject"
        )
        self.assertFalse(service._object_exists(s3, "k"))


class ExportResume(unittest.IsolatedAsyncioTestCase):
    def _s3(self):
        s3 = MagicMock()
        s3.generate_presigned_url.return_value = "https://signed/url"
        return s3

    async def test_no_content_409(self):
        pg = _Pg([[], [], [], [], [], [], []])
        with self.assertRaises(HTTPException) as ctx:
            await service.export_resume(pg, "u1")
        self.assertEqual(ctx.exception.status_code, 409)

    async def test_fresh_upload_renders_and_presigns(self):
        pg = _content_pg()
        pg.results.put(_Result([]))  # no existing generated row
        pg.results.put(_Result([]))  # no stored format → default
        pg.results.put(USER_ROW)
        pg.results.put(_Result([(datetime.datetime(2025, 1, 2),)]))  # RETURNING
        s3 = self._s3()
        with (
            patch.object(service, "get_s3_client", return_value=s3),
            patch.object(service, "render_docx", return_value=b"docx"),
        ):
            resp = await service.export_resume(pg, "u1")
        self.assertTrue(resp.regenerated)
        self.assertEqual(resp.url, "https://signed/url")
        s3.upload_fileobj.assert_called_once()
        _, kwargs = s3.generate_presigned_url.call_args
        self.assertEqual(kwargs["ExpiresIn"], 300)
        self.assertEqual(kwargs["Params"]["Key"], "resumes/u1/generated.docx")
        self.assertEqual(resp.generated_at, "2025-01-02T00:00:00")

    async def test_stale_hash_regenerates(self):
        pg = _content_pg()
        pg.results.put(_Result([("old-hash", datetime.datetime.now())]))
        pg.results.put(_Result([]))
        pg.results.put(USER_ROW)
        pg.results.put(_Result([(datetime.datetime.now(),)]))
        s3 = self._s3()
        with (
            patch.object(service, "get_s3_client", return_value=s3),
            patch.object(service, "render_docx", return_value=b"docx"),
        ):
            resp = await service.export_resume(pg, "u1")
        self.assertTrue(resp.regenerated)
        s3.upload_fileobj.assert_called_once()

    async def test_same_hash_and_object_skips_render(self):
        content = await service._fetch_resume_content(_content_pg(), "u1")
        hash_now = service.content_source_hash(
            content, template="original", fmt=default_format_profile()
        )
        pg = _content_pg()
        pg.results.put(_Result([]))  # no stored format → default profile
        pg.results.put(_Result([(hash_now, datetime.datetime(2025, 1, 1))]))
        s3 = self._s3()  # head_object succeeds → object exists
        with (
            patch.object(service, "get_s3_client", return_value=s3),
            patch.object(service, "render_docx") as render,
        ):
            resp = await service.export_resume(pg, "u1")
        self.assertFalse(resp.regenerated)
        render.assert_not_called()
        s3.upload_fileobj.assert_not_called()
        self.assertEqual(resp.generated_at, "2025-01-01T00:00:00")

    async def test_changed_format_regenerates_despite_content_hash(self):
        # Same resume content, but a re-upload changed the effective
        # format profile — the export must re-render under the new look.
        content = await service._fetch_resume_content(_content_pg(), "u1")
        stored = default_format_profile()
        stored.section_blank_lines = {"skills": 4}
        hash_now = service.content_source_hash(
            content, template="original", fmt=default_format_profile()
        )
        pg = _content_pg()
        pg.results.put(_Result([(stored.to_json(),)]))  # stored fmt differs
        pg.results.put(_Result([(hash_now, datetime.datetime.now(datetime.timezone.utc))]))
        pg.results.put(USER_ROW)
        pg.results.put(_Result([(datetime.datetime.now(datetime.timezone.utc),)]))
        s3 = self._s3()
        with (
            patch.object(service, "get_s3_client", return_value=s3),
            patch.object(service, "render_docx", return_value=b"docx"),
        ):
            resp = await service.export_resume(pg, "u1")
        self.assertTrue(resp.regenerated)
        s3.upload_fileobj.assert_called_once()

    async def test_missing_object_regenerates_despite_hash(self):
        content = await service._fetch_resume_content(_content_pg(), "u1")
        hash_now = service.content_source_hash(
            content, template="original", fmt=default_format_profile()
        )
        pg = _content_pg()
        pg.results.put(_Result([]))  # no stored format → default profile
        pg.results.put(_Result([(hash_now, datetime.datetime.now(datetime.timezone.utc))]))
        pg.results.put(USER_ROW)
        pg.results.put(_Result([(datetime.datetime.now(datetime.timezone.utc),)]))
        s3 = self._s3()
        s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "HeadObject"
        )
        with (
            patch.object(service, "get_s3_client", return_value=s3),
            patch.object(service, "render_docx", return_value=b"docx"),
        ):
            resp = await service.export_resume(pg, "u1")
        self.assertTrue(resp.regenerated)

    async def test_deleted_account_404s_before_writing_a_file(self):
        # An export racing the account's deletion waits on the row lock,
        # then finds the account gone — no file may land after the sweep.
        pg = _content_pg()
        pg.results.put(_Result([]))
        pg.results.put(_Result([]))
        pg.results.put(_Result([]))  # lock: no user row
        s3 = self._s3()
        with (
            patch.object(service, "get_s3_client", return_value=s3),
            patch.object(service, "render_docx", return_value=b"docx"),
            self.assertRaises(HTTPException) as ctx,
        ):
            await service.export_resume(pg, "u1")
        self.assertEqual(ctx.exception.status_code, 404)
        s3.upload_fileobj.assert_not_called()


if __name__ == "__main__":
    unittest.main()

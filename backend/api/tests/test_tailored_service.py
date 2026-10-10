"""tailored service — save-from-run snapshot, update, delete, export.

Run: .venv/bin/python -m unittest backend.api.tests.test_tailored_service -v
"""

import json
import unittest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from api.tailor import db as tailor_db
from api.tailored import db, model, service
from fastapi import HTTPException
from pydantic import ValidationError
from shared.docgen import ResumeContent

from .helpers import _Pg, _Result, one

RESULT = json.dumps(
    {
        "summary": "Tailored summary",
        "experiences": [
            {
                "experience_id": 1,
                "bullets": [{"bullet_id": 10, "text": "Built x"}],
            }
        ],
        "skills": ["Python", "Go"],
    }
)


def _run_row(**over):
    base = {
        "id": "r1",
        "user_id": "u1",
        "job_description": "JD",
        "company_name": "Acme",
        "role": "Senior Engineer",
        "model": None,
        "pending_question": None,
        "result": RESULT,
        "status": "COMPLETED",
        "created_at": datetime(2025, 1, 1, tzinfo=UTC),
    }
    base.update(over)
    return tailor_db.UserTailorRunRow(**base)


def _tailored_row(**over):
    base = {
        "id": "t1",
        "user_id": "u1",
        "tailor_run_id": "r1",
        "company_name": "Acme",
        "role": "Senior Engineer",
        "job_description": "JD",
        "content": json.dumps(
            {
                "summary": "Tailored summary",
                "experiences": [
                    {
                        "company_name": "Acme",
                        "title": "Engineer",
                        "start_date": "2020",
                        "end_date": "2023",
                        "bullets": ["Built x"],
                    }
                ],
                "skill_groups": [
                    {"category": "Languages", "skills": ["Python", "Go"]}
                ],
            }
        ),
        "s3_key": None,
        "source_hash": None,
        "generated_at": None,
        "created_at": datetime(2025, 1, 1, tzinfo=UTC),
        "updated_at": datetime(2025, 1, 1, tzinfo=UTC),
    }
    base.update(over)
    return db.UserTailoredResumeRow(**base)


class SaveFromRun(unittest.IsolatedAsyncioTestCase):
    async def test_repeat_save_returns_existing_entry(self):
        pg = _Pg([one(("t-existing",))])
        tailored_id = await service.save_from_run(pg, "u1", "r1")
        self.assertEqual(tailored_id, "t-existing")
        self.assertEqual(len(pg.queries), 1)

    async def test_missing_run_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.save_from_run(_Pg([_Result(), []]), "u1", "r1")
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_unfinished_run_409(self):
        pg = _Pg([_Result(), one(_run_row(status="PROCESSING", result=None))])
        with self.assertRaises(HTTPException) as ctx:
            await service.save_from_run(pg, "u1", "r1")
        self.assertEqual(ctx.exception.status_code, 409)

    async def test_waiting_feedback_run_is_savable(self):
        # Post-submit review loop — result is stored while the run still
        # waits for the user's reply, and that snapshot is savable.
        pg = _Pg(
            [
                _Result(),  # get_tailored_by_run
                one(_run_row(status="WAITING_FOR_INPUT")),
                _Result([(1, "Acme", "Engineer", "2020", "2023")]),
                _Result([("Python", "Languages"), ("Go", "Languages")]),
                _Result(rowcount=1),
            ]
        )
        tailored_id = await service.save_from_run(pg, "u1", "r1")
        self.assertTrue(tailored_id)

    async def test_unreadable_result_409(self):
        pg = _Pg([_Result(), one(_run_row(result="{not json"))])
        with self.assertRaises(HTTPException) as ctx:
            await service.save_from_run(pg, "u1", "r1")
        self.assertEqual(ctx.exception.status_code, 409)

    async def test_snapshot_resolves_meta_and_groups_skills(self):
        pg = _Pg(
            [
                _Result(),  # get_tailored_by_run → no existing entry
                one(_run_row()),
                # _experience_meta
                _Result([(1, "Acme", "Engineer", "2020", "2023")]),
                # _skill_categories
                _Result([("Python", "Languages"), ("Go", "Languages")]),
                _Result(rowcount=1),  # insert
            ]
        )
        tailored_id = await service.save_from_run(pg, "u1", "r1")
        self.assertTrue(tailored_id)

        insert = next(q for q, _ in pg.queries if "INSERT" in q)
        params = next(p for q, p in pg.queries if "INSERT" in q)
        self.assertIn("user_tailored_resume", insert)
        # (id, user_id, tailor_run_id, company_name, role, job_description, content)
        self.assertEqual(params[1:6], ("u1", "r1", "Acme", "Senior Engineer", "JD"))
        content = json.loads(params[6])
        self.assertEqual(content["summary"], "Tailored summary")
        self.assertEqual(content["experiences"][0]["company_name"], "Acme")
        self.assertEqual(content["experiences"][0]["bullets"], ["Built x"])
        self.assertEqual(
            content["skill_groups"],
            [{"category": "Languages", "skills": ["Python", "Go"]}],
        )

    async def test_dangling_experience_refs_dropped(self):
        pg = _Pg(
            [
                _Result(),
                one(_run_row()),
                _Result([]),  # no matching base experience
                _Result([]),
            ]
        )
        with self.assertRaises(HTTPException) as ctx:
            await service.save_from_run(pg, "u1", "r1")
        self.assertEqual(ctx.exception.status_code, 409)


def _create_req(**over):
    base = {
        "company_name": "  Acme ",
        "role": "Senior Engineer",
        "job_description": "JD",
        "summary": "Tailored summary",
        "experiences": [
            {"experience_id": 2, "bullets": ["Led x", "  ", "Built y"]},
            {"experience_id": 1, "bullets": ["Ran z"]},
        ],
        "skills": ["Go", "Python", "Terraform"],
    }
    base.update(over)
    return model.CreateTailoredRequest(**base)


class Create(unittest.IsolatedAsyncioTestCase):
    async def test_resolves_profile_fields_and_groups_skills(self):
        pg = _Pg(
            [
                # _experience_meta — in id order, not the request's order
                _Result(
                    [
                        (1, "Initech", "Engineer", "2019", "2022"),
                        (2, "Acme", "Senior Engineer", "2022", None),
                    ]
                ),
                _Result([("Python", "Languages"), ("Go", "Languages")]),
                _Result(rowcount=1),
            ]
        )
        resp = await service.create_tailored(pg, "u1", _create_req())
        self.assertTrue(resp.id)

        params = next(p for q, p in pg.queries if "INSERT" in q)
        # No run behind it, and company/role cleaned like a run's.
        self.assertEqual(params[0], resp.id)
        self.assertEqual(params[1:6], ("u1", None, "Acme", "Senior Engineer", "JD"))
        content = json.loads(params[6])
        self.assertEqual(content["summary"], "Tailored summary")
        # The request's experience order wins; blank bullets are dropped.
        self.assertEqual(
            [(e["company_name"], e["title"], e["end_date"], e["bullets"]) for e in content["experiences"]],
            [
                ("Acme", "Senior Engineer", None, ["Led x", "Built y"]),
                ("Initech", "Engineer", "2022", ["Ran z"]),
            ],
        )
        # Skills not in the base profile land in an uncategorized group.
        self.assertEqual(
            content["skill_groups"],
            [
                {"category": "Languages", "skills": ["Go", "Python"]},
                {"category": None, "skills": ["Terraform"]},
            ],
        )

    async def test_unknown_experience_id_422(self):
        pg = _Pg([_Result([(1, "Initech", "Engineer", "2019", "2022")])])
        with self.assertRaises(HTTPException) as ctx:
            await service.create_tailored(pg, "u1", _create_req())
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("2", ctx.exception.detail)
        self.assertFalse(any("INSERT" in q for q, _ in pg.queries))

    async def test_duplicate_experience_id_422(self):
        req = _create_req(
            experiences=[
                {"experience_id": 1, "bullets": ["a"]},
                {"experience_id": 1, "bullets": ["b"]},
            ]
        )
        pg = _Pg()
        with self.assertRaises(HTTPException) as ctx:
            await service.create_tailored(pg, "u1", req)
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(pg.queries, [])

    def test_request_needs_an_experience_and_a_job_description(self):
        with self.assertRaises(ValidationError):
            _create_req(experiences=[])
        with self.assertRaises(ValidationError):
            _create_req(job_description="")
        with self.assertRaises(ValidationError):
            _create_req(
                experiences=[
                    {"experience_id": 1, "bullets": ["x" * (model.MAX_TAILORED_BULLET_CHARS + 1)]}
                ]
            )


class GetAndList(unittest.IsolatedAsyncioTestCase):
    async def test_get_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.get_tailored(_Pg([[]]), "u1", "t1")
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_get_maps_content(self):
        resp = await service.get_tailored(_Pg([one(_tailored_row())]), "u1", "t1")
        self.assertEqual(resp.id, "t1")
        self.assertEqual(resp.content.experiences[0].bullets, ["Built x"])

    async def test_list(self):
        resp = await service.list_tailored(_Pg([_Result()]), "u1")
        self.assertEqual(resp.items, [])
        resp = await service.list_tailored(
            _Pg([_Result([_tailored_row()])]), "u1"
        )
        self.assertEqual(len(resp.items), 1)
        self.assertEqual(resp.items[0].role, "Senior Engineer")


class Update(unittest.IsolatedAsyncioTestCase):
    async def test_update_404(self):
        pg = _Pg([_Result()])  # existence check → missing
        with self.assertRaises(HTTPException) as ctx:
            await service.update_tailored(
                pg, "u1", "t1", model.UpdateTailoredRequest(role="X")
            )
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_empty_patch_404s_for_missing_row(self):
        pg = _Pg([_Result()])
        with self.assertRaises(HTTPException) as ctx:
            await service.update_tailored(
                pg, "u1", "t1", model.UpdateTailoredRequest()
            )
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_update_writes_fields_and_refreshes(self):
        new_content = model.TailoredContent(
            summary=None,
            experiences=[
                model.TailoredExperienceContent(
                    company_name="Acme", title="Eng", bullets=["y"]
                )
            ],
            skill_groups=[],
        )
        pg = _Pg(
            [one(_tailored_row()), _Result(rowcount=1), one(_tailored_row(role="X"))]
        )
        resp = await service.update_tailored(
            pg,
            "u1",
            "t1",
            model.UpdateTailoredRequest(role="X", content=new_content),
        )
        self.assertEqual(resp.role, "X")
        update = next(q for q, _ in pg.queries if "UPDATE" in q)
        self.assertIn("role = %s", update)
        self.assertIn("content = %s", update)


class Delete(unittest.IsolatedAsyncioTestCase):
    async def test_delete_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.delete_tailored(_Pg([[]]), "u1", "t1")
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_delete_without_s3(self):
        pg = _Pg([one(_tailored_row()), _Result(rowcount=1)])
        out = await service.delete_tailored(pg, "u1", "t1")
        self.assertEqual(out, {"ok": True})

    async def test_delete_removes_s3_object(self):
        s3 = MagicMock()
        pg = _Pg([one(_tailored_row(s3_key="k")), _Result(rowcount=1)])
        with patch.object(service, "get_s3_client", return_value=s3):
            await service.delete_tailored(pg, "u1", "t1")
        s3.delete_object.assert_called_once()


class Export(unittest.IsolatedAsyncioTestCase):
    def _patches(self, s3, exists=False):
        return [
            patch.object(service, "get_s3_client", return_value=s3),
            patch.object(service, "render_docx", return_value=b"docx"),
            patch.object(
                service.resume_export,
                "_fetch_resume_content",
                new=AsyncMock(return_value=ResumeContent()),
            ),
            patch.object(
                service.resume_export,
                "_fetch_format_profile",
                new=AsyncMock(return_value=None),
            ),
            patch.object(
                service.resume_export, "_object_exists", return_value=exists
            ),
            patch.object(
                service, "content_source_hash", return_value="h"
            ),
        ]

    async def test_export_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.export_tailored(_Pg([[]]), "u1", "t1")
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_export_regenerates_when_stale(self):
        s3 = MagicMock()
        s3.generate_presigned_url.return_value = "https://x/docx"
        pg = _Pg([one(_tailored_row()), one((1,)), _Result(), one(_tailored_row(generated_at=datetime(2025, 1, 2, tzinfo=UTC)))])
        for p in self._patches(s3):
            p.start()
            self.addCleanup(p.stop)
        resp = await service.export_tailored(pg, "u1", "t1")
        self.assertTrue(resp.regenerated)
        self.assertEqual(resp.url, "https://x/docx")
        s3.upload_fileobj.assert_called_once()

    async def test_export_reuses_fresh_object(self):
        s3 = MagicMock()
        s3.generate_presigned_url.return_value = "https://x/docx"
        row = _tailored_row(s3_key="k", source_hash="h", generated_at=datetime(2025, 1, 2, tzinfo=UTC))
        pg = _Pg([one(row), one(row)])
        for p in self._patches(s3, exists=True):
            p.start()
            self.addCleanup(p.stop)
        resp = await service.export_tailored(pg, "u1", "t1")
        self.assertFalse(resp.regenerated)
        s3.upload_fileobj.assert_not_called()

    async def test_deleted_account_404s_before_writing_a_file(self):
        s3 = MagicMock()
        pg = _Pg([one(_tailored_row()), _Result()])  # lock: no user row
        for p in self._patches(s3):
            p.start()
            self.addCleanup(p.stop)
        with self.assertRaises(HTTPException) as ctx:
            await service.export_tailored(pg, "u1", "t1")
        self.assertEqual(ctx.exception.status_code, 404)
        s3.upload_fileobj.assert_not_called()


class RenderContent(unittest.TestCase):
    def test_snapshot_sections_override_base(self):
        base = ResumeContent(
            summary="base summary",
            experiences=[],
            skill_groups=[],
        )
        content = service._tailored_render_content(_tailored_row(), base)
        self.assertEqual(content.summary, "Tailored summary")
        self.assertEqual(content.experiences[0].company, "Acme")
        self.assertEqual(content.experiences[0].bullets, ["Built x"])
        self.assertEqual(content.skill_groups[0].skills, ["Python", "Go"])
        self.assertEqual(content.source, "tailored:t1")

    def test_empty_bullets_dropped_from_render(self):
        row = _tailored_row(
            content=json.dumps(
                {
                    "summary": None,
                    "experiences": [
                        {
                            "company_name": "A",
                            "title": "T",
                            "start_date": "2020",
                            "end_date": None,
                            "bullets": ["", "  ", "keep"],
                        }
                    ],
                    "skill_groups": [
                        {"category": None, "skills": []},
                        {"category": "C", "skills": ["s"]},
                    ],
                }
            )
        )
        content = service._tailored_render_content(row, ResumeContent())
        self.assertEqual(content.experiences[0].bullets, ["keep"])
        self.assertEqual(len(content.skill_groups), 1)


if __name__ == "__main__":
    unittest.main()

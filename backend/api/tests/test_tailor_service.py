"""tailor service — run dedup, commit-before-publish, answer/dismiss
lifecycle. Mirrors the suggestion service tests.

Run: .venv/bin/python -m unittest backend.api.tests.test_tailor_service -v
"""

import json
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from shared.amqp import TAILOR_EXCHANGE_NAME
from shared.checkpoints import CHECKPOINT_TABLES

from api.tailor import db, model, service

from .helpers import _Amqp, _Pg, _Result, one


def _row(**over):
    base = dict(
        id="r1",
        user_id="u1",
        job_description="JD",
        company_name=None,
        role=None,
        model=None,
        pending_question=None,
        result=None,
        status="PROCESSING",
        created_at=datetime(2025, 1, 1),
    )
    base.update(over)
    return db.UserTailorRunRow(**base)


class StartTailor(unittest.IsolatedAsyncioTestCase):
    async def test_active_run_resumes_without_publish(self):
        pg = _Pg([one(_row(status="PROCESSING"))])
        amqp = _Amqp()
        with (
            patch.object(service, "require_balance", new=AsyncMock()) as bal,
            patch.object(service, "validate_model_choice", new=AsyncMock()),
        ):
            resp = await service.start_tailor(
                pg, amqp, model.StartTailorRequest(job_description="JD"), "u1"
            )
        self.assertEqual(resp.run_id, "r1")
        self.assertTrue(resp.resumed)
        bal.assert_not_called()
        self.assertEqual(amqp.publisher.published, [])

    async def test_result_bearing_wait_resumes(self):
        # A run parked on the review interrupt still counts as outstanding —
        # it blocks a fresh tailor instead of being overwritten.
        pg = _Pg([one(_row(status="WAITING_FOR_INPUT", result='{"x":1}'))])
        amqp = _Amqp()
        with patch.object(service, "require_balance", new=AsyncMock()):
            resp = await service.start_tailor(
                pg, amqp, model.StartTailorRequest(job_description="JD"), "u1"
            )
        self.assertEqual(resp.run_id, "r1")
        self.assertTrue(resp.resumed)
        self.assertEqual(amqp.publisher.published, [])

    async def test_completed_runs_clear_on_new_start(self):
        pg = _Pg(
            [
                _Result(),                # outstanding select → none
                _Result([("r-done",)]),   # clear: DELETE ... RETURNING
                _Result(),                # checkpoints
                _Result(),                # checkpoint_blobs
                _Result(),                # checkpoint_writes
                _Result(),                # insert new run
            ]
        )
        amqp = _Amqp()
        with (
            patch.object(service, "require_balance", new=AsyncMock()),
            patch.object(
                service,
                "validate_model_choice",
                new=AsyncMock(return_value=None),
            ),
        ):
            resp = await service.start_tailor(
                pg, amqp, model.StartTailorRequest(job_description="JD"), "u1"
            )
        self.assertNotEqual(resp.run_id, "r-done")
        self.assertFalse(resp.resumed)
        self.assertTrue(amqp.publisher.published)
        deletes = [(q, p) for q, p in pg.queries if "DELETE" in q]
        self.assertIn("status = 'COMPLETED'", deletes[0][0])
        self.assertEqual([p for _, p in deletes[1:]], [("r-done",)] * 3)

    async def test_happy_path_commits_then_publishes(self):
        order = []
        pg = _Pg([_Result(), _Result()])  # no outstanding; clear + insert
        real_commit = pg.commit

        async def commit():
            order.append("commit")
            await real_commit()

        pg.commit = commit
        amqp = _Amqp(order)
        with (
            patch.object(service, "require_balance", new=AsyncMock()),
            patch.object(
                service,
                "validate_model_choice",
                new=AsyncMock(return_value=None),
            ),
        ):
            resp = await service.start_tailor(
                pg, amqp, model.StartTailorRequest(job_description="JD"), "u1"
            )
        self.assertTrue(resp.run_id)
        self.assertEqual(order, ["commit", "publish"])
        self.assertEqual(amqp.calls, [(TAILOR_EXCHANGE_NAME, "#")])
        body = json.loads(amqp.publisher.published[0].body)
        self.assertEqual(body["run_id"], resp.run_id)


class GetTailorStatus(unittest.IsolatedAsyncioTestCase):
    async def test_missing_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.get_tailor_status(_Pg([[]]), "u1", "r1")
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_fields_mapped(self):
        resp = await service.get_tailor_status(
            _Pg([_Result(fetchone=_row(status="WAITING_FOR_INPUT", pending_question="Q",
                                       company_name="Acme", role="Engineer"))]),
            "u1",
            "r1",
        )
        self.assertEqual(resp.run_id, "r1")
        self.assertEqual(resp.status, "WAITING_FOR_INPUT")
        self.assertEqual(resp.pending_question, "Q")
        self.assertEqual(resp.job_description, "JD")
        self.assertEqual(resp.company_name, "Acme")
        self.assertEqual(resp.role, "Engineer")


class GetActiveTailor(unittest.IsolatedAsyncioTestCase):
    async def test_none_outstanding_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.get_active_tailor(_Pg([_Result()]), "u1")
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_returns_outstanding_run(self):
        resp = await service.get_active_tailor(
            _Pg([_Result(fetchone=_row(status="FAILED"))]), "u1"
        )
        self.assertEqual(resp.run_id, "r1")
        self.assertEqual(resp.status, "FAILED")

    async def test_failed_run_carries_its_inputs_for_a_retry(self):
        # The form refills from these, model included, so a failed run
        # doesn't cost the user their pasted posting.
        resp = await service.get_active_tailor(
            _Pg([_Result(fetchone=_row(status="FAILED", company_name="Acme",
                                       role="Engineer", model="openrouter:x/y"))]),
            "u1",
        )
        self.assertEqual(resp.job_description, "JD")
        self.assertEqual(resp.company_name, "Acme")
        self.assertEqual(resp.role, "Engineer")
        self.assertEqual(resp.model, "openrouter:x/y")


class AnswerTailor(unittest.IsolatedAsyncioTestCase):
    async def test_missing_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.answer_tailor(
                "u1", "r1", model.AnswerRequest(text="hi"), _Pg([[]]), _Amqp()
            )
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_not_waiting_409(self):
        pg = _Pg([_Result(fetchone=_row(status="COMPLETED"))])
        with self.assertRaises(HTTPException) as ctx:
            await service.answer_tailor(
                "u1", "r1", model.AnswerRequest(text="hi"), pg, _Amqp()
            )
        self.assertEqual(ctx.exception.status_code, 409)

    async def test_answer_requeues_with_text(self):
        pg = _Pg(
            [_Result(fetchone=_row(status="WAITING_FOR_INPUT")), one((1,)), _Result()]
        )
        amqp = _Amqp()
        out = await service.answer_tailor(
            "u1", "r1", model.AnswerRequest(text="yes please"), pg, amqp
        )
        self.assertEqual(out, {"ok": True})
        self.assertEqual(pg.commits, 1)
        body = json.loads(amqp.publisher.published[0].body)
        self.assertEqual(body["answer"], "yes please")
        self.assertEqual(body["run_id"], "r1")

    async def test_answer_keeps_stored_result(self):
        # Feedback on a submitted resume resumes the run — the stored result
        # must survive the PROCESSING transition so it stays on screen.
        pg = _Pg(
            [
                _Result(
                    fetchone=_row(status="WAITING_FOR_INPUT", result='{"x":1}')
                ),
                one((1,)),
                _Result(),
            ]
        )
        out = await service.answer_tailor(
            "u1", "r1", model.AnswerRequest(text="tweak"), pg, _Amqp()
        )
        self.assertEqual(out, {"ok": True})
        update = next(q for q, _ in pg.queries if "UPDATE user_tailor_run" in q)
        self.assertNotIn("result", update)
        params = next(p for q, p in pg.queries if "UPDATE user_tailor_run" in q)
        self.assertEqual(params, ("PROCESSING", None, "r1"))

    async def test_deleted_account_404s_without_queueing(self):
        pg = _Pg([_Result(fetchone=_row(status="WAITING_FOR_INPUT")), _Result()])
        amqp = _Amqp()
        with self.assertRaises(HTTPException) as ctx:
            await service.answer_tailor(
                "u1", "r1", model.AnswerRequest(text="hi"), pg, amqp
            )
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(amqp.publisher.published, [])
        self.assertFalse(any("UPDATE user_tailor_run" in q for q, _ in pg.queries))


class DismissTailor(unittest.IsolatedAsyncioTestCase):
    async def test_someone_elses_run_leaves_its_thread_alone(self):
        pg = _Pg([[]])  # DELETE ... RETURNING found no row of theirs
        out = await service.dismiss_tailor("u1", "r-other", pg)
        self.assertEqual(out, {"ok": True})
        deletes = [q for q, _ in pg.queries if "DELETE FROM" in q]
        self.assertEqual(len(deletes), 1)
        self.assertIn("user_tailor_run", deletes[0])

    async def test_deletes_run_and_checkpoints(self):
        pg = _Pg([[("r1",)]])
        out = await service.dismiss_tailor("u1", "r1", pg)
        self.assertEqual(out, {"ok": True})
        deletes = [(q, p) for q, p in pg.queries if "DELETE FROM" in q]
        self.assertEqual(len(deletes), 4)
        self.assertEqual(deletes[0][1], ("r1", "u1"))  # run row
        self.assertEqual(
            [q.split()[2] for q, _ in deletes[1:]], list(CHECKPOINT_TABLES)
        )
        for _, params in deletes[1:]:
            self.assertEqual(params, ("r1",))  # checkpoint tables


if __name__ == "__main__":
    unittest.main()

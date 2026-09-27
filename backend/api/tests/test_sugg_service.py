"""bullet_point_sugg service — session dedup, balance+model gates, the
commit-before-publish ordering, answer flow, accept/dismiss lifecycle.

Run: .venv/bin/python -m unittest backend.api.tests.test_sugg_service -v
"""

import json
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from shared.amqp import BULLET_SUGG_EXCHANGE_NAME

from api.bullet_point_sugg import db, model, service

from .helpers import _Amqp, _Pg, _Result


def _row(**over):
    base = dict(
        id="s1",
        user_id="u1",
        experience_id=5,
        bullet_id=None,
        model=None,
        pending_question=None,
        result=None,
        status="PROCESSING",
        created_at=datetime(2025, 1, 1),
    )
    base.update(over)
    return db.UserSuggestionRow(**base)


class StartSuggestion(unittest.IsolatedAsyncioTestCase):
    def _pg(self):
        return _Pg()

    async def test_active_session_resumes_without_publish(self):
        pg = _Pg([[( "s-existing", )]])
        amqp = _Amqp()
        with (
            patch.object(service, "require_balance", new=AsyncMock()) as bal,
            patch.object(
                service, "validate_model_choice", new=AsyncMock()
            ) as vm,
        ):
            resp = await service.start_suggestion(
                pg, amqp, model.StartSuggestionRequest(experience_id=5), "u1"
            )
        self.assertEqual(resp.session_id, "s-existing")
        bal.assert_not_called()
        vm.assert_not_called()
        self.assertEqual(amqp.publisher.published, [])

    async def test_missing_experience_404(self):
        pg = _Pg([[], [], []])  # no active; exp lookup empty
        with (
            patch.object(service, "require_balance", new=AsyncMock()),
            patch.object(
                service,
                "validate_model_choice",
                new=AsyncMock(return_value=None),
            ),
            self.assertRaises(HTTPException) as ctx,
        ):
            await service.start_suggestion(
                pg, _Amqp(), model.StartSuggestionRequest(experience_id=9), "u1"
            )
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_missing_bullet_404(self):
        pg = _Pg([[], [(1,)], []])  # no active; exp found; bullet missing
        with (
            patch.object(service, "require_balance", new=AsyncMock()),
            patch.object(
                service,
                "validate_model_choice",
                new=AsyncMock(return_value=None),
            ),
            self.assertRaises(HTTPException) as ctx,
        ):
            await service.start_suggestion(
                pg,
                _Amqp(),
                model.StartSuggestionRequest(experience_id=5, bullet_id=99),
                "u1",
            )
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_happy_path_commits_then_publishes(self):
        order = []
        pg = _Pg([[], [(1,)], _Result()])  # no active; exp ok; insert
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
                new=AsyncMock(return_value="openrouter:m"),
            ),
        ):
            resp = await service.start_suggestion(
                pg, amqp, model.StartSuggestionRequest(experience_id=5), "u1"
            )
        self.assertTrue(resp.session_id)
        self.assertEqual(order, ["commit", "publish"])
        insert = [q for q, _ in pg.queries if "INSERT INTO user_suggestion" in q]
        self.assertEqual(len(insert), 1)
        self.assertEqual(amqp.calls, [(BULLET_SUGG_EXCHANGE_NAME, "#")])
        body = json.loads(amqp.publisher.published[0].body)
        self.assertEqual(body["session_id"], resp.session_id)
        self.assertIsNone(body["prompt"])

    async def test_prompt_is_sent_with_job(self):
        pg = _Pg([[], [(1,)], _Result()])  # no active; exp ok; insert
        amqp = _Amqp()
        with (
            patch.object(service, "require_balance", new=AsyncMock()),
            patch.object(
                service,
                "validate_model_choice",
                new=AsyncMock(return_value=None),
            ),
        ):
            await service.start_suggestion(
                pg,
                amqp,
                model.StartSuggestionRequest(
                    experience_id=5, prompt="keep it punchy"
                ),
                "u1",
            )
        body = json.loads(amqp.publisher.published[0].body)
        self.assertEqual(body["prompt"], "keep it punchy")

    async def test_failed_session_is_swept_before_insert(self):
        # A leftover FAILED row shares the (user, experience, bullet) unique
        # slot — the sweep must delete it (and its checkpoints) before insert.
        pg = _Pg([[], [(1,)], _Result(rows=[("s-dead",)]), _Result()])
        with (
            patch.object(service, "require_balance", new=AsyncMock()),
            patch.object(
                service,
                "validate_model_choice",
                new=AsyncMock(return_value=None),
            ),
        ):
            resp = await service.start_suggestion(
                pg, _Amqp(), model.StartSuggestionRequest(experience_id=5), "u1"
            )
        self.assertTrue(resp.session_id)
        texts = [q for q, _ in pg.queries]
        sweep = next(
            i for i, q in enumerate(texts) if "DELETE FROM user_suggestion" in q
        )
        insert = next(
            i for i, q in enumerate(texts) if "INSERT INTO user_suggestion" in q
        )
        self.assertLess(sweep, insert)
        ckpt_deletes = [
            q
            for q in texts
            if "DELETE FROM checkpoint" in q
        ]
        self.assertEqual(len(ckpt_deletes), 3)


class GetSuggestionStatus(unittest.IsolatedAsyncioTestCase):
    async def test_missing_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.get_suggestion_status(_Pg([[]]), "u1", "s1")
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_fields_mapped(self):
        row = _row(status="WAITING_FOR_INPUT", pending_question="Q?")
        resp = await service.get_suggestion_status(
            _Pg([_Result(fetchone=row)]), "u1", "s1"
        )
        self.assertEqual(resp.status, "WAITING_FOR_INPUT")
        self.assertEqual(resp.pending_question, "Q?")


class AnswerSuggestion(unittest.IsolatedAsyncioTestCase):
    async def test_missing_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.answer_suggestion(
                "u1", "s1", model.AnswerRequest(text="hi"), _Pg([[]]), _Amqp()
            )
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_not_waiting_409(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.answer_suggestion(
                "u1",
                "s1",
                model.AnswerRequest(text="hi"),
                _Pg([_Result(fetchone=_row(status="PROCESSING"))]),
                _Amqp(),
            )
        self.assertEqual(ctx.exception.status_code, 409)

    async def test_answer_requeues_with_text(self):
        order = []
        pg = _Pg(
            [_Result(fetchone=_row(status="WAITING_FOR_INPUT")), _Result()]
        )
        real_commit = pg.commit

        async def commit():
            order.append("commit")
            await real_commit()

        pg.commit = commit
        amqp = _Amqp(order)
        out = await service.answer_suggestion(
            "u1", "s1", model.AnswerRequest(text="5 engineers"), pg, amqp
        )
        self.assertEqual(out, {"ok": True})
        self.assertEqual(order, ["commit", "publish"])
        update = [q for q, _ in pg.queries if "UPDATE user_suggestion" in q][0]
        self.assertIn("status = %s", update)
        body = json.loads(amqp.publisher.published[0].body)
        self.assertEqual(body["answer"], "5 engineers")
        self.assertEqual(body["session_id"], "s1")


class RetrySuggestion(unittest.IsolatedAsyncioTestCase):
    async def test_missing_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.retry_suggestion("u1", "s1", _Pg([[]]), _Amqp())
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_non_failed_409(self):
        for status in ("PROCESSING", "WAITING_FOR_INPUT", "COMPLETED"):
            with self.subTest(status=status):
                pg = _Pg([_Result(fetchone=_row(status=status))])
                with self.assertRaises(HTTPException) as ctx:
                    await service.retry_suggestion("u1", "s1", pg, _Amqp())
                self.assertEqual(ctx.exception.status_code, 409)

    async def test_retry_commits_then_publishes_without_answer(self):
        order = []
        pg = _Pg(
            [_Result(fetchone=_row(status="FAILED")), _Result()]
        )
        real_commit = pg.commit

        async def commit():
            order.append("commit")
            await real_commit()

        pg.commit = commit
        amqp = _Amqp(order)
        with patch.object(service, "require_balance", new=AsyncMock()) as bal:
            out = await service.retry_suggestion("u1", "s1", pg, amqp)
        self.assertEqual(out, {"ok": True})
        bal.assert_called_once()
        self.assertEqual(order, ["commit", "publish"])
        update = [q for q, _ in pg.queries if "UPDATE user_suggestion" in q][0]
        self.assertIn("status = %s", update)
        body = json.loads(amqp.publisher.published[0].body)
        self.assertEqual(body["session_id"], "s1")
        # Retry is a checkpoint resume — no answer, no prompt.
        self.assertIsNone(body["answer"])
        self.assertIsNone(body["prompt"])

    async def test_retry_gates_on_balance(self):
        pg = _Pg([_Result(fetchone=_row(status="FAILED")), _Result()])
        amqp = _Amqp()
        with (
            patch.object(
                service,
                "require_balance",
                new=AsyncMock(
                    side_effect=HTTPException(402, "insufficient_balance")
                ),
            ),
            self.assertRaises(HTTPException) as ctx,
        ):
            await service.retry_suggestion("u1", "s1", pg, amqp)
        self.assertEqual(ctx.exception.status_code, 402)
        self.assertEqual(amqp.publisher.published, [])


class AcceptSuggestion(unittest.IsolatedAsyncioTestCase):
    async def test_missing_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await service.accept_suggestion("u1", "s1", _Pg([[]]))
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_no_result_500(self):
        pg = _Pg([_Result(fetchone=_row(result=None))])
        with self.assertRaises(HTTPException) as ctx:
            await service.accept_suggestion("u1", "s1", pg)
        self.assertEqual(ctx.exception.status_code, 500)

    async def test_applies_suggestions_and_cleans_up(self):
        result = json.dumps(
            [
                {"bullet_id": 1, "suggestion": "new one"},
                {"bullet_id": 2, "suggestion": "new two"},
            ]
        )
        row = _row(status="COMPLETED", result=result, experience_id=5)
        pg = _Pg([_Result(fetchone=row)])
        out = await service.accept_suggestion("u1", "s1", pg)
        self.assertEqual(out, {"ok": True})
        updates = [
            (q, p)
            for q, p in pg.queries
            if "UPDATE user_base_experience_bullet" in q
        ]
        self.assertEqual(len(updates), 2)
        self.assertEqual(updates[0][1], ("new one", 1, 5))
        # Session row + langgraph checkpoint tables are all deleted.
        deletes = [q for q, _ in pg.queries if "DELETE FROM" in q]
        self.assertTrue(any("user_suggestion" in q for q in deletes))
        for table in ("checkpoints", "checkpoint_blobs", "checkpoint_writes"):
            self.assertTrue(any(table in q for q in deletes), table)


class DismissSuggestion(unittest.IsolatedAsyncioTestCase):
    async def test_deletes_session_and_checkpoints(self):
        pg = _Pg()
        out = await service.dismiss_suggestion("u1", "s1", pg)
        self.assertEqual(out, {"ok": True})
        deletes = [(q, p) for q, p in pg.queries if "DELETE FROM" in q]
        self.assertEqual(len(deletes), 4)
        self.assertEqual(deletes[0][1], ("s1", "u1"))  # session row
        for _, params in deletes[1:]:
            self.assertEqual(params, ("s1",))  # checkpoint tables


if __name__ == "__main__":
    unittest.main()

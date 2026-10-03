"""Handler tests — parse_event guards, dispatch bookkeeping, the cleanup
task's ack/nack, and each handler's id extraction + status writes.

The cleanup loop is an asyncio task polling ~1/s, so ack/nack assertions
poll briefly instead of sleeping.

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_handlers -v
     (from the repo root with the workspace venv)
"""

import asyncio
import json
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from dispatcher.handlers.generic import (
    DispatchJobParams,
    GenericHandlerWithCleanup,
    HandlerError,
)
from dispatcher.handlers.resume_handler import ResumeHandler
from dispatcher.handlers.suggestion_handler import SuggestionHandler
from dispatcher.handlers.system_design_handler import SystemDesignHandler
from dispatcher.handlers.tailor_handler import TailorHandler
from dispatcher.runners.generic import JobHandle


def _message(body: dict | None) -> MagicMock:
    msg = MagicMock()
    msg.body = json.dumps(body).encode() if body is not None else b""
    msg.ack = AsyncMock()
    msg.nack = AsyncMock()
    return msg


async def _wait_for(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.05)
    return False


class _Handle(JobHandle):
    def __init__(self, result):
        super().__init__({})
        self._result = result

    def poll(self):
        return self._result


class _Runner:
    """JobRunner stand-in — returns a preset handle from run()."""

    def __init__(self, handle):
        self.handle = handle

    def run(self):
        return self.handle


class _Handler(GenericHandlerWithCleanup):
    """Adds a spy to the no-op base update_db_status."""

    def __init__(self):
        super().__init__()
        self.status_updates = []

    def update_db_status(self, job_id: str, status: str):
        self.status_updates.append((job_id, status))


class ParseEvent(unittest.TestCase):
    def setUp(self):
        self.handler = _Handler()

    def test_parses_body_json(self):
        msg = _message({"job_id": "j1", "extra": [1, 2]})
        data = self.handler.parse_event(msg)
        self.assertEqual(data["job_id"], "j1")
        self.assertEqual(data["extra"], [1, 2])

    def test_missing_body_raises(self):
        with self.assertRaises(HandlerError):
            self.handler.parse_event(_message(None))


class DispatchJob(unittest.IsolatedAsyncioTestCase):
    async def test_registers_handle_under_job_id(self):
        handler = _Handler()
        handle = _Handle("PROCESSING")
        msg = _message({})
        await handler.dispatch_job(
            DispatchJobParams(
                job_id="j1", runner=_Runner(handle), message=msg
            )
        )
        self.assertIs(handler.running_jobs["j1"][0], handle)
        self.assertIs(handler.running_jobs["j1"][1], msg)

    async def test_redelivery_of_in_flight_job_is_acked_not_redispatched(self):
        handler = _Handler()
        msg = _message({})
        handler.running_jobs["j1"] = (_Handle("PROCESSING"), msg)

        runner = _Runner(_Handle("PROCESSING"))
        dup = _message({})
        await handler.dispatch_job(
            DispatchJobParams(job_id="j1", runner=runner, message=dup)
        )

        dup.ack.assert_awaited_once()
        self.assertIs(handler.running_jobs["j1"][1], msg)

    async def test_failed_settle_retries_then_gives_up(self):
        handler = _Handler()
        msg = _message({})
        msg.ack = AsyncMock(side_effect=RuntimeError("channel closed"))
        handle = _Handle("COMPLETED")
        handler.running_jobs["j1"] = (handle, msg)
        handler.last_statuses["j1"] = "COMPLETED"

        # 9 failures keep the job tracked; the 10th drops it — the broker
        # already requeued the delivery when its channel died.
        for _ in range(9):
            with self.assertRaises(RuntimeError):
                await handler._reap_job("j1", handle, msg)
            self.assertIn("j1", handler.running_jobs)
        await handler._reap_job("j1", handle, msg)
        self.assertNotIn("j1", handler.running_jobs)
        self.assertEqual(msg.ack.await_count, 10)

    async def test_db_update_failure_retries_write_next_tick(self):
        handler = _Handler()
        handler.update_db_status = MagicMock(
            side_effect=[RuntimeError("db down"), None]
        )
        handle = _Handle("PROCESSING")
        handler.running_jobs["j1"] = (handle, _message({}))

        with self.assertRaises(RuntimeError):
            await handler._reap_job("j1", handle, handler.running_jobs["j1"][1])
        self.assertNotIn("j1", handler.last_statuses)

        await handler._reap_job("j1", handle, handler.running_jobs["j1"][1])
        self.assertEqual(handler.last_statuses["j1"], "PROCESSING")
        self.assertEqual(handler.update_db_status.call_count, 2)


class CleanupLoop(unittest.IsolatedAsyncioTestCase):
    async def test_completed_job_is_acked_and_dropped(self):
        handler = _Handler()
        handler._ensure_cleanup_task()
        msg = _message({})
        handler.running_jobs["j1"] = (_Handle("COMPLETED"), msg)
        self.assertTrue(
            await _wait_for(lambda: "j1" not in handler.running_jobs)
        )
        msg.ack.assert_awaited_once()
        self.assertIn(("j1", "COMPLETED"), handler.status_updates)

    async def test_failed_job_is_nacked_and_dropped(self):
        handler = _Handler()
        handler._ensure_cleanup_task()
        msg = _message({})
        handler.running_jobs["j2"] = (_Handle("FAILED"), msg)
        self.assertTrue(
            await _wait_for(lambda: "j2" not in handler.running_jobs)
        )
        msg.nack.assert_awaited_once_with(requeue=False)

    async def test_processing_job_is_polled_not_dropped(self):
        handler = _Handler()
        handler._ensure_cleanup_task()
        msg = _message({})
        handler.running_jobs["j3"] = (_Handle("PROCESSING"), msg)
        await asyncio.sleep(1.3)
        self.assertIn("j3", handler.running_jobs)
        msg.ack.assert_not_awaited()
        msg.nack.assert_not_awaited()

    async def test_repeated_status_writes_db_once(self):
        handler = _Handler()
        handler._ensure_cleanup_task()
        handler.running_jobs["j4"] = (_Handle("PROCESSING"), _message({}))
        await asyncio.sleep(2.2)
        self.assertIn("j4", handler.running_jobs)
        self.assertEqual(
            handler.status_updates.count(("j4", "PROCESSING")), 1
        )

    async def test_status_change_writes_db_again(self):
        handler = _Handler()
        handler._ensure_cleanup_task()
        handle = _Handle("PROCESSING")
        handler.running_jobs["j5"] = (handle, _message({}))
        self.assertTrue(
            await _wait_for(
                lambda: ("j5", "PROCESSING") in handler.status_updates
            )
        )
        handle._result = "COMPLETED"
        self.assertTrue(
            await _wait_for(lambda: "j5" not in handler.running_jobs)
        )
        self.assertEqual(
            handler.status_updates,
            [("j5", "PROCESSING"), ("j5", "COMPLETED")],
        )


class ResumeHandlerMessages(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = ResumeHandler()

    async def test_missing_job_id_nacks(self):
        msg = _message({"s3_key": "k"})
        await self.handler.on_message(msg)
        msg.nack.assert_awaited_once_with(requeue=False)
        self.assertEqual(self.handler.running_jobs, {})

    async def test_valid_message_dispatches_runner(self):
        msg = _message({"job_id": "j1", "s3_key": "k", "user_id": "u"})
        with patch(
            "dispatcher.handlers.resume_handler.ResumeRunner"
        ) as runner_cls:
            runner_cls.return_value = _Runner(_Handle("PROCESSING"))
            await self.handler.on_message(msg)
        self.assertIn("j1", self.handler.running_jobs)
        runner_cls.assert_called_once()
        msg.nack.assert_not_awaited()

    def test_update_db_status_writes_row(self):
        conn = MagicMock()
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=conn)
        cm.__exit__ = MagicMock(return_value=False)
        with patch(
            "dispatcher.handlers.resume_handler.get_pg_client",
            return_value=cm,
        ):
            self.handler.update_db_status("j1", "COMPLETED")
        conn.execute.assert_called_once_with(
            "UPDATE user_upload_job SET status = %s WHERE id = %s",
            ("COMPLETED", "j1"),
        )


class SuggestionHandlerMessages(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = SuggestionHandler()

    async def test_missing_session_id_nacks(self):
        msg = _message({"answer": "hi"})
        await self.handler.on_message(msg)
        msg.nack.assert_awaited_once_with(requeue=False)

    async def test_valid_message_dispatches_runner(self):
        msg = _message({"session_id": "s1"})
        with patch(
            "dispatcher.handlers.suggestion_handler.SuggestionsRunner"
        ) as runner_cls:
            runner_cls.return_value = _Runner(_Handle("PROCESSING"))
            await self.handler.on_message(msg)
        self.assertIn("s1", self.handler.running_jobs)

    def test_update_db_status_only_acts_on_failed(self):
        with patch(
            "dispatcher.handlers.suggestion_handler.set_suggestion_failed"
        ) as failed, patch(
            "dispatcher.handlers.suggestion_handler.get_pg_client"
        ) as get_pg:
            self.handler.update_db_status("s1", "COMPLETED")
            failed.assert_not_called()
            get_pg.assert_not_called()

            self.handler.update_db_status("s1", "FAILED")
            failed.assert_called_once()


class TailorHandlerMessages(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = TailorHandler()

    async def test_missing_run_id_nacks(self):
        msg = _message({"nope": 1})
        await self.handler.on_message(msg)
        msg.nack.assert_awaited_once_with(requeue=False)

    async def test_valid_message_dispatches_runner(self):
        msg = _message({"run_id": "r1"})
        with patch(
            "dispatcher.handlers.tailor_handler.TailorRunner"
        ) as runner_cls:
            runner_cls.return_value = _Runner(_Handle("PROCESSING"))
            await self.handler.on_message(msg)
        self.assertIn("r1", self.handler.running_jobs)

    def test_update_db_status_only_acts_on_failed(self):
        with patch(
            "dispatcher.handlers.tailor_handler.set_tailor_failed"
        ) as failed, patch(
            "dispatcher.handlers.tailor_handler.get_pg_client"
        ) as get_pg:
            self.handler.update_db_status("r1", "COMPLETED")
            failed.assert_not_called()
            get_pg.assert_not_called()

            self.handler.update_db_status("r1", "FAILED")
            failed.assert_called_once()



class SystemDesignHandlerMessages(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.handler = SystemDesignHandler()

    async def test_missing_session_id_nacks(self):
        msg = _message({"nope": 1})
        await self.handler.on_message(msg)
        msg.nack.assert_awaited_once_with(requeue=False)

    async def test_valid_message_dispatches_runner(self):
        msg = _message({"session_id": "s1", "action": "start"})
        with patch(
            "dispatcher.handlers.system_design_handler.SystemDesignRunner"
        ) as runner_cls:
            runner_cls.return_value = _Runner(_Handle("PROCESSING"))
            await self.handler.on_message(msg)
        self.assertIn("s1", self.handler.running_jobs)
        runner_cls.assert_called_once_with({"session_id": "s1", "action": "start"})

    def test_update_db_status_only_acts_on_failed(self):
        with patch(
            "dispatcher.handlers.system_design_handler.set_system_design_failed"
        ) as failed, patch(
            "dispatcher.handlers.system_design_handler.get_pg_client"
        ) as get_pg:
            self.handler.update_db_status("s1", "COMPLETED")
            failed.assert_not_called()
            get_pg.assert_not_called()

            self.handler.update_db_status("s1", "FAILED")
            failed.assert_called_once()


if __name__ == "__main__":
    unittest.main()

"""Handler tests — parse_event guards, dispatch bookkeeping, the cleanup
loop's accept/discard, and each handler's id extraction + status writes.

The cleanup thread is a daemon polling ~1/s, so accept/discard assertions
poll briefly instead of sleeping.

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_handlers -v
     (from the repo root with the workspace venv)
"""

import json
import time
import unittest
from unittest.mock import MagicMock, patch

from dispatcher.handlers.generic import (
    DispatchJobParams,
    GenericHandlerWithCleanup,
    HandlerError,
)
from dispatcher.handlers.resume_handler import ResumeHandler
from dispatcher.handlers.suggestion_handler import SuggestionHandler
from dispatcher.handlers.tailor_handler import TailorHandler
from dispatcher.runners.generic import JobHandle


def _event(body: dict | None) -> MagicMock:
    event = MagicMock()
    if body is None:
        event.message.body = None
    else:
        event.message.body = json.dumps(body).encode()
    return event


def _wait_for(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
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
        event = _event({"job_id": "j1", "extra": [1, 2]})
        data = self.handler.parse_event(event)
        self.assertEqual(data["job_id"], "j1")
        self.assertEqual(data["extra"], [1, 2])

    def test_missing_message_raises(self):
        event = MagicMock()
        event.message = None
        with self.assertRaises(HandlerError):
            self.handler.parse_event(event)

    def test_missing_body_raises(self):
        with self.assertRaises(HandlerError):
            self.handler.parse_event(_event(None))


class DispatchJob(unittest.TestCase):
    def test_registers_handle_under_job_id(self):
        handler = _Handler()
        handle = _Handle("PROCESSING")
        event = _event({})
        handler.dispatch_job(
            DispatchJobParams(
                job_id="j1", runner=_Runner(handle), event=event
            )
        )
        self.assertIs(handler.running_jobs["j1"][0], handle)
        self.assertIs(handler.running_jobs["j1"][1], event)


class CleanupLoop(unittest.TestCase):
    def test_completed_job_is_accepted_and_dropped(self):
        handler = _Handler()
        handler.delivery_context = MagicMock()
        event = _event({})
        handler.running_jobs["j1"] = (_Handle("COMPLETED"), event)
        self.assertTrue(
            _wait_for(lambda: "j1" not in handler.running_jobs)
        )
        handler.delivery_context.accept.assert_called_with(event)
        self.assertIn(("j1", "COMPLETED"), handler.status_updates)

    def test_failed_job_is_discarded_and_dropped(self):
        handler = _Handler()
        handler.delivery_context = MagicMock()
        event = _event({})
        handler.running_jobs["j2"] = (_Handle("FAILED"), event)
        self.assertTrue(
            _wait_for(lambda: "j2" not in handler.running_jobs)
        )
        handler.delivery_context.discard.assert_called_with(event)

    def test_processing_job_is_polled_not_dropped(self):
        handler = _Handler()
        handler.delivery_context = MagicMock()
        event = _event({})
        handler.running_jobs["j3"] = (_Handle("PROCESSING"), event)
        time.sleep(1.3)
        self.assertIn("j3", handler.running_jobs)
        handler.delivery_context.accept.assert_not_called()
        handler.delivery_context.discard.assert_not_called()


class ResumeHandlerMessages(unittest.TestCase):
    def setUp(self):
        self.handler = ResumeHandler()
        self.handler.delivery_context = MagicMock()

    def test_missing_job_id_discards(self):
        self.handler.on_amqp_message(_event({"s3_key": "k"}))
        self.handler.delivery_context.discard.assert_called_once()
        self.assertEqual(self.handler.running_jobs, {})

    def test_valid_message_dispatches_runner(self):
        with patch(
            "dispatcher.handlers.resume_handler.ResumeRunner"
        ) as runner_cls:
            runner_cls.return_value = _Runner(_Handle("PROCESSING"))
            self.handler.on_amqp_message(
                _event({"job_id": "j1", "s3_key": "k", "user_id": "u"})
            )
        self.assertIn("j1", self.handler.running_jobs)
        runner_cls.assert_called_once()
        self.handler.delivery_context.discard.assert_not_called()

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


class SuggestionHandlerMessages(unittest.TestCase):
    def setUp(self):
        self.handler = SuggestionHandler()
        self.handler.delivery_context = MagicMock()

    def test_missing_session_id_discards(self):
        self.handler.on_amqp_message(_event({"answer": "hi"}))
        self.handler.delivery_context.discard.assert_called_once()

    def test_valid_message_dispatches_runner(self):
        with patch(
            "dispatcher.handlers.suggestion_handler.SuggestionsRunner"
        ) as runner_cls:
            runner_cls.return_value = _Runner(_Handle("PROCESSING"))
            self.handler.on_amqp_message(_event({"session_id": "s1"}))
        self.assertIn("s1", self.handler.running_jobs)


class TailorHandlerMessages(unittest.TestCase):
    def setUp(self):
        self.handler = TailorHandler()
        self.handler.delivery_context = MagicMock()

    def test_missing_run_id_discards(self):
        self.handler.on_amqp_message(_event({"nope": 1}))
        self.handler.delivery_context.discard.assert_called_once()

    def test_valid_message_dispatches_runner(self):
        with patch(
            "dispatcher.handlers.tailor_handler.TailorRunner"
        ) as runner_cls:
            runner_cls.return_value = _Runner(_Handle("PROCESSING"))
            self.handler.on_amqp_message(_event({"run_id": "r1"}))
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


if __name__ == "__main__":
    unittest.main()

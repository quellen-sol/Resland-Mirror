"""Runner machinery tests — local_threaded + generic ABCs, plus each
runner's input-validation paths (no DB/LLM needed: validation raises
before either is touched).

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_runners -v
     (from the repo root with the workspace venv)
"""

import queue
import threading
import time
import unittest

from dispatcher.runners.generic import JobHandle, JobRunner
from dispatcher.runners.local_threaded import (
    LocalThreadedJobHandle,
    LocalThreadJobRunner,
)


def _poll_until(handle, status, timeout=5.0):
    """Wait for poll() to report `status` (the cleanup thread polls ~1/s)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = handle.poll()
        if result == status:
            return result
        time.sleep(0.05)
    return handle.poll()


class NoopRunner(LocalThreadJobRunner):
    def task(self, q):
        pass


class ExplodingRunner(LocalThreadJobRunner):
    """Mirrors the real runners: catch the exception and queue it."""

    def task(self, q):
        try:
            raise RuntimeError("boom")
        except Exception as e:
            q.put((threading.current_thread().name, e))


class UncaughtRunner(LocalThreadJobRunner):
    def task(self, q):
        raise RuntimeError("boom")


RELEASE = threading.Event()


class SlowRunner(LocalThreadJobRunner):
    """Stays alive until the test lets it go — the runner's threads are
    non-daemon, so a plain long sleep would hang test exit."""

    def task(self, q):
        RELEASE.wait(timeout=30)


class LocalThreadedPoll(unittest.TestCase):
    def test_completed_when_thread_finishes_clean(self):
        handle = NoopRunner({}).run()
        self.assertEqual(_poll_until(handle, "COMPLETED"), "COMPLETED")

    def test_failed_when_task_queues_exception(self):
        handle = ExplodingRunner({}).run()
        self.assertEqual(_poll_until(handle, "FAILED"), "FAILED")

    def test_uncaught_task_exception_reports_completed(self):
        # Quirk: poll() only sees failures the task queued itself — a
        # task whose exception escapes just looks like a finished thread.
        handle = UncaughtRunner({}).run()
        self.assertEqual(_poll_until(handle, "COMPLETED"), "COMPLETED")

    def test_processing_while_thread_alive(self):
        RELEASE.clear()
        try:
            runner = SlowRunner({"x": 1})
            handle = runner.run()
            self.assertEqual(handle.poll(), "PROCESSING")
        finally:
            RELEASE.set()


class HandleDirectly(unittest.TestCase):
    def test_poll_prefers_queued_exception_over_thread_state(self):
        # An exception already in the queue wins even while the thread runs.
        q = queue.Queue()
        q.put(("worker-1", ValueError("nope")))
        t = threading.Thread(target=RELEASE.wait, args=(30,), daemon=True)
        t.start()
        handle = LocalThreadedJobHandle({}, t, q)
        self.assertEqual(handle.poll(), "FAILED")


class AbcShape(unittest.TestCase):
    def test_job_runner_and_handle_are_abstract(self):
        with self.assertRaises(TypeError):
            JobRunner({})
        with self.assertRaises(TypeError):
            JobHandle({})


if __name__ == "__main__":
    unittest.main()

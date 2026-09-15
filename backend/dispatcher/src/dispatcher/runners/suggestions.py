import queue
import threading
from typing import Any

from ..agents.suggestions import build_and_invoke_agent
from ..pg import pg_pool
from .db_ops import (
    fetch_suggestion_rows,
    set_suggestion_question,
    set_suggestion_result,
)
from .generic import RunnerError
from .local_threaded import LocalThreadJobRunner


class SuggestionsRunner(LocalThreadJobRunner):
    def __init__(self, job_data: Any):
        super().__init__(job_data)

    def task(self, queue: queue.Queue):
        try:
            if not self.job_data:
                raise RunnerError("Job data is required")

            if not isinstance(self.job_data, dict):
                raise TypeError("Job data must be a dictionary")

            session_id = self.job_data.get("session_id")
            if not session_id:
                raise RunnerError("Got job with no session_id")

            if not isinstance(session_id, str):
                raise TypeError("Session ID must be a string")

            answer = self.job_data.get("answer")

            with pg_pool.connection() as conn:
                rows = fetch_suggestion_rows(conn, session_id)
            if not rows:
                raise RunnerError("Session not found")

            outcome = build_and_invoke_agent(session_id, answer, rows)

            with pg_pool.connection() as conn:
                if outcome.status == "waiting":
                    set_suggestion_question(conn, session_id, outcome.question)
                else:
                    if not outcome.result:
                        raise RunnerError(
                            "Agent finished without submitting suggestions"
                        )
                    set_suggestion_result(conn, session_id, outcome.result)

        except Exception as e:
            print(f"Error in job runner: {e}")
            queue.put((threading.current_thread().name, e))
            return

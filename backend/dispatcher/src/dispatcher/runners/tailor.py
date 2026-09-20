import queue
import threading
from typing import Any

from ..agents.tailor import build_and_invoke_agent
from ..pg import pg_pool
from .db_ops import (
    fetch_tailor_profile,
    fetch_tailor_run,
    set_tailor_question,
    set_tailor_result,
)
from .generic import RunnerError
from .local_threaded import LocalThreadJobRunner


class TailorRunner(LocalThreadJobRunner):
    def __init__(self, job_data: Any):
        super().__init__(job_data)

    def task(self, queue: queue.Queue):
        try:
            if not self.job_data:
                raise RunnerError("Job data is required")

            if not isinstance(self.job_data, dict):
                raise TypeError("Job data must be a dictionary")

            run_id = self.job_data.get("run_id")
            if not run_id:
                raise RunnerError("Got job with no run_id")

            if not isinstance(run_id, str):
                raise TypeError("Run ID must be a string")

            answer = self.job_data.get("answer")

            with pg_pool.connection() as conn:
                run = fetch_tailor_run(conn, run_id)
            if not run:
                raise RunnerError("Tailor run not found")

            with pg_pool.connection() as conn:
                profile = fetch_tailor_profile(conn, run.user_id)
            if not profile.experiences:
                raise RunnerError("No experience to tailor")

            outcome = build_and_invoke_agent(run_id, answer, run, profile)

            with pg_pool.connection() as conn:
                if outcome.status == "waiting":
                    set_tailor_question(conn, run_id, outcome.question)
                else:
                    if not outcome.result:
                        raise RunnerError(
                            "Agent finished without submitting a tailored resume"
                        )
                    set_tailor_result(conn, run_id, outcome.result)

        except Exception as e:
            print(f"Error in job runner: {e}")
            queue.put((threading.current_thread().name, e))
            return

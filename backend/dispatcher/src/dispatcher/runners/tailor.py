import queue
import threading
from typing import Any

from shared.pg import get_pg_client

from ..agents.tailor import build_and_invoke_agent
from ..env_vars import PG_URL, TAILOR_MODEL
from .db_ops import (
    complete_tailor_run,
    default_model_spec,
    discard_orphaned_thread,
    fetch_tailor_profile,
    fetch_tailor_run,
    record_token_usage,
    set_tailor_question,
    set_tailor_result,
    usage_job_id,
)
from .generic import RunnerError
from .local_threaded import LocalThreadJobRunner

# Shown as the pending question when the agent crashes mid-run (provider
# outage, transient error) — the answer flow then resumes the checkpointed
# graph instead of losing the session.
RESUME_AFTER_ERROR_MESSAGE = (
    "Something went wrong on our end — send any message to continue."
)


class TailorRunner(LocalThreadJobRunner):
    def __init__(self, job_data: Any):
        super().__init__(job_data)

    def task(self, queue: queue.Queue):
        usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "generation_ids": [],
            "cost_usd": 0.0,
            "all_costed": True,
        }
        user_id: str | None = None
        model_spec = TAILOR_MODEL
        run_id: str | None = None
        try:
            with get_pg_client(PG_URL) as pg_conn:
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

                    run = fetch_tailor_run(pg_conn, run_id)
                    if not run:
                        # Dismissed, or the account deleted, before the job
                        # ran: ack it instead of dead-lettering a message
                        # that carries the user's answer.
                        print(f"Tailor run {run_id} no longer exists, dropped")
                        return

                    user_id = run.user_id
                    model_spec = run.model
                    if not model_spec:
                        model_spec = default_model_spec(pg_conn)
                    if not model_spec:
                        model_spec = TAILOR_MODEL

                    profile = fetch_tailor_profile(pg_conn, run.user_id)
                    if not profile.experiences:
                        raise RunnerError("No experience to tailor")

                    try:
                        outcome = build_and_invoke_agent(
                            run_id, answer, run, profile, model_spec, usage
                        )
                    except Exception as e:
                        # Leave the run resumable — the checkpointed graph can be
                        # continued by the answer flow once the failure clears. The
                        # job ends cleanly so the message isn't dead-lettered.
                        print(f"Agent failed for tailor run {run_id}: {e}")
                        set_tailor_question(pg_conn, run_id, RESUME_AFTER_ERROR_MESSAGE)
                        return

                    if outcome.status == "waiting":
                        set_tailor_question(
                            pg_conn, run_id, outcome.question, outcome.result
                        )
                    else:
                        if outcome.result:
                            set_tailor_result(pg_conn, run_id, outcome.result)
                        elif not complete_tailor_run(pg_conn, run_id):
                            raise RunnerError(
                                "Agent finished without submitting a tailored resume"
                            )
                finally:
                    if user_id and run_id:
                        # Dismissed (or the account deleted) while the agent
                        # ran: its checkpoints outlived the row's cleanup.
                        try:
                            if discard_orphaned_thread(
                                pg_conn, "user_tailor_run", run_id
                            ):
                                print(f"Tailor run {run_id} deleted mid-run")
                        except Exception as e:
                            print(f"Orphaned-thread check failed: {e}")
                    if (
                        user_id
                        and run_id
                        and (usage["input_tokens"] or usage["output_tokens"])
                    ):
                        try:
                            charged = record_token_usage(
                                pg_conn,
                                user_id=user_id,
                                job_kind="TAILOR",
                                job_id=usage_job_id(run_id, self.job_data),
                                model=model_spec,
                                input_tokens=usage["input_tokens"],
                                output_tokens=usage["output_tokens"],
                                generation_ids=usage["generation_ids"],
                                cost_usd=usage["cost_usd"]
                                if usage["all_costed"]
                                else None,
                            )
                            print(f"Charged {charged}¢ for {run_id}")
                        except Exception as e:
                            print(f"Failed to record token usage: {e}")
        except Exception as e:
            print(f"Error in job runner: {e}")
            queue.put((threading.current_thread().name, e))
            return

import queue
import threading
from typing import Any

from shared.pg import get_pg_client

from ..agents.suggestions import build_and_invoke_agent
from ..env_vars import PG_URL, SUGGESTIONS_MODEL
from .db_ops import (
    complete_suggestion,
    default_model_spec,
    discard_orphaned_thread,
    fetch_suggestion_rows,
    load_memory_bank,
    record_token_usage,
    set_suggestion_failed,
    set_suggestion_question,
    set_suggestion_result,
    suggestion_exists,
    usage_job_id,
)
from .generic import RunnerError
from .local_threaded import LocalThreadJobRunner


class SuggestionsRunner(LocalThreadJobRunner):
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
        model_spec = SUGGESTIONS_MODEL
        session_id: str | None = None
        try:
            with get_pg_client(PG_URL) as pg_conn:
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
                    prompt = self.job_data.get("prompt")

                    rows = fetch_suggestion_rows(pg_conn, session_id)
                    if not rows:
                        if not suggestion_exists(pg_conn, session_id):
                            # Dismissed, or the account deleted, before the
                            # job ran: ack it instead of dead-lettering a
                            # message that carries the user's text.
                            print(f"Suggestion {session_id} no longer exists, dropped")
                            return
                        # The row is there but its bullet join is empty.
                        raise RunnerError("Session not found")

                    user_id = rows[0].user_id
                    model_spec = rows[0].model
                    if not model_spec:
                        model_spec = default_model_spec(pg_conn)
                    if not model_spec:
                        model_spec = SUGGESTIONS_MODEL

                    memory = load_memory_bank(pg_conn, user_id, "SUGGESTION")
                    try:
                        outcome = build_and_invoke_agent(
                            session_id,
                            answer,
                            rows,
                            model_spec,
                            usage,
                            prompt,
                            memory=memory,
                        )
                    except Exception as e:
                        # Leave the session resumable — the checkpointed graph is
                        # continued by the retry endpoint once the failure
                        # clears. The job ends cleanly so the message isn't
                        # dead-lettered.
                        print(f"Agent failed for suggestion {session_id}: {e}")

                        set_suggestion_failed(pg_conn, session_id)
                        return

                    if outcome.status == "waiting":
                        set_suggestion_question(
                            pg_conn, session_id, outcome.question, outcome.result
                        )
                    elif outcome.result:
                        set_suggestion_result(pg_conn, session_id, outcome.result)
                    elif not complete_suggestion(pg_conn, session_id):
                        raise RunnerError(
                            "Agent finished without submitting suggestions"
                        )
                finally:
                    if user_id and session_id:
                        # Dismissed (or the account deleted) while the agent
                        # ran: its checkpoints outlived the row's cleanup.
                        try:
                            if discard_orphaned_thread(
                                pg_conn, "user_suggestion", session_id
                            ):
                                print(f"Suggestion {session_id} deleted mid-run")
                        except Exception as e:
                            print(f"Orphaned-thread check failed: {e}")
                    if (
                        user_id
                        and session_id
                        and (usage["input_tokens"] or usage["output_tokens"])
                    ):
                        try:
                            charged = record_token_usage(
                                pg_conn,
                                user_id=user_id,
                                job_kind="SUGGESTION",
                                job_id=usage_job_id(session_id, self.job_data),
                                model=model_spec,
                                input_tokens=usage["input_tokens"],
                                output_tokens=usage["output_tokens"],
                                generation_ids=usage["generation_ids"],
                                cost_usd=usage["cost_usd"]
                                if usage["all_costed"]
                                else None,
                            )
                            print(f"Charged {charged}¢ for {session_id}")
                        except Exception as e:
                            print(f"Failed to record token usage: {e}")
        except Exception as e:
            print(f"Error in job runner: {e}")
            queue.put((threading.current_thread().name, e))
            return

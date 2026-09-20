import queue
import threading
from typing import Any

from ..agents.suggestions import build_and_invoke_agent
from ..env_vars import SUGGESTIONS_MODEL
from ..pg import pg_pool
from .db_ops import (
    default_model_spec,
    fetch_suggestion_rows,
    record_token_usage,
    set_suggestion_question,
    set_suggestion_result,
)
from .generic import RunnerError
from .local_threaded import LocalThreadJobRunner

# Shown as the pending question when the agent crashes mid-run (provider
# outage, transient error) — the answer flow then resumes the checkpointed
# graph instead of losing the session.
RESUME_AFTER_ERROR_MESSAGE = (
    "Something went wrong on our end — send any message to continue."
)


class SuggestionsRunner(LocalThreadJobRunner):
    def __init__(self, job_data: Any):
        super().__init__(job_data)

    def task(self, queue: queue.Queue):
        usage = {"input_tokens": 0, "output_tokens": 0, "generation_ids": []}
        user_id: str | None = None
        model_spec = SUGGESTIONS_MODEL
        session_id: str | None = None
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

            user_id = rows[0].user_id
            model_spec = rows[0].model
            if not model_spec:
                with pg_pool.connection() as conn:
                    model_spec = default_model_spec(conn)
            if not model_spec:
                model_spec = SUGGESTIONS_MODEL

            try:
                outcome = build_and_invoke_agent(
                    session_id, answer, rows, model_spec, usage
                )
            except Exception as e:
                # Leave the session resumable — the checkpointed graph can be
                # continued by the answer flow once the failure clears. The
                # job ends cleanly so the message isn't dead-lettered.
                print(f"Agent failed for suggestion {session_id}: {e}")
                with pg_pool.connection() as conn:
                    set_suggestion_question(
                        conn, session_id, RESUME_AFTER_ERROR_MESSAGE
                    )
                return

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
        finally:
            if (
                user_id
                and session_id
                and (usage["input_tokens"] or usage["output_tokens"])
            ):
                try:
                    with pg_pool.connection() as conn:
                        charged = record_token_usage(
                            conn,
                            user_id=user_id,
                            job_kind="SUGGESTION",
                            job_id=session_id,
                            model=model_spec,
                            input_tokens=usage["input_tokens"],
                            output_tokens=usage["output_tokens"],
                            generation_ids=usage["generation_ids"],
                        )
                        print(f"Charged {charged}¢ for {session_id}")
                except Exception as e:
                    print(f"Failed to record token usage: {e}")

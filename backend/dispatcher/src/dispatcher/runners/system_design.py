import json
import queue
import threading
from datetime import UTC, datetime
from typing import Any

from langchain.messages import AIMessage, HumanMessage
from shared.pg import get_pg_client
from shared.system_design.bank import InterviewBrief, get_problem
from shared.system_design.diagram import normalize_scene, parse_scene

from ..agents.system_design import (
    INTERVIEW_KICKOFF,
    AgentContext,
    build_turn_message,
    generate_brief,
    grade_interview,
    interviewer_prompt,
    new_usage,
    opening_message,
    run_interview_turn,
)
from ..env_vars import (
    PG_URL,
    SYSTEM_DESIGN_GRADER_MODEL,
    SYSTEM_DESIGN_MODEL,
    TAILOR_MODEL,
)
from .db_ops import (
    complete_system_design_session,
    default_model_spec,
    discard_orphaned_thread,
    fetch_system_design_session,
    fetch_system_design_transcript,
    record_token_usage,
    save_system_design_turn,
    set_system_design_notice,
    start_system_design_session,
    usage_job_id,
)
from .generic import RunnerError
from .local_threaded import LocalThreadJobRunner

# Shown when a turn crashes (provider outage, transient error); the candidate
# retries and the checkpointed thread picks up where it stopped.
RESUME_AFTER_ERROR_MESSAGE = (
    "Something went wrong on our end. Retry to continue the interview."
)


class ModelNotConfiguredError(Exception):
    pass


def require_model(spec: str) -> str:
    """An empty spec makes init_chat_model build a configurable model that
    only fails at invoke time with a cryptic error — fail early instead."""
    if not spec:
        raise ModelNotConfiguredError(
            "No model configured for system design interviews: set "
            "SYSTEM_DESIGN_MODEL (or TAILOR_MODEL) on the dispatcher, or mark "
            "an enabled model_pricing row as the default."
        )
    return spec


class SystemDesignRunner(LocalThreadJobRunner):
    def __init__(self, job_data: Any):
        super().__init__(job_data)

    def task(self, queue: queue.Queue):
        usage = new_usage()
        grader_usage = new_usage()
        user_id: str | None = None
        session_id: str | None = None
        model_spec = SYSTEM_DESIGN_MODEL
        grader_spec = SYSTEM_DESIGN_MODEL
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

                    action = self.job_data.get("action") or "start"
                    text = self.job_data.get("text")
                    turn_id = self.job_data.get("turn_id")

                    session = fetch_system_design_session(pg_conn, session_id)
                    if not session:
                        raise RunnerError("System design session not found")

                    if turn_id and session.last_turn_id == turn_id:
                        # Redelivery of a turn that already finished.
                        print(f"Skipping finished turn {turn_id} for {session_id}")
                        return

                    user_id = session.user_id
                    # Deployments already set TAILOR_MODEL for agent work, so
                    # it stands in when SYSTEM_DESIGN_MODEL isn't configured.
                    model_spec = (
                        session.model
                        or default_model_spec(pg_conn)
                        or SYSTEM_DESIGN_MODEL
                        or TAILOR_MODEL
                    )
                    grader_spec = SYSTEM_DESIGN_GRADER_MODEL or model_spec

                    try:
                        if session.brief is None:
                            brief = self._load_brief(session, model_spec, usage)
                            start_system_design_session(
                                pg_conn,
                                session_id,
                                title=brief.title,
                                prompt=brief.prompt,
                                brief_json=brief.to_json(),
                                opening=opening_message(brief),
                                turn_id=turn_id,
                            )
                            return

                        brief = InterviewBrief.from_json(session.brief)
                        if session.phase != "FEEDBACK":
                            over = self._interview_turn(
                                pg_conn,
                                session,
                                brief,
                                action,
                                text,
                                turn_id,
                                model_spec,
                                usage,
                            )
                            if not over:
                                return
                            session = fetch_system_design_session(pg_conn, session_id)
                            if not session:
                                raise RunnerError("System design session vanished")
                        self._grade(
                            pg_conn,
                            session,
                            brief,
                            turn_id,
                            grader_spec,
                            grader_usage if grader_spec != model_spec else usage,
                        )
                    except RunnerError:
                        raise
                    except Exception as e:
                        # Leave the session resumable — a retry turn picks the
                        # checkpointed thread (or the grading) back up. The job
                        # ends cleanly so the message isn't dead-lettered.
                        print(
                            f"Agent failed for system design session {session_id}: {e}"
                        )
                        set_system_design_notice(
                            pg_conn, session_id, RESUME_AFTER_ERROR_MESSAGE
                        )
                finally:
                    if user_id and session_id:
                        self._bill(pg_conn, user_id, session_id, model_spec, usage, "")
                        if grader_spec != model_spec:
                            self._bill(
                                pg_conn,
                                user_id,
                                session_id,
                                grader_spec,
                                grader_usage,
                                ":grade",
                            )
        except Exception as e:
            print(f"Error in job runner: {e}")
            queue.put((threading.current_thread().name, e))
            return

    def _load_brief(self, session, model_spec: str, usage: dict) -> InterviewBrief:
        if session.source == "BANK":
            problem = get_problem(session.problem_id or "")
            if not problem:
                raise RunnerError(f"Unknown bank problem {session.problem_id!r}")
            return problem.brief
        if not session.job_description:
            raise RunnerError("Job-based session has no job description")
        return generate_brief(
            require_model(model_spec),
            usage,
            company_name=session.company_name,
            role=session.role,
            job_description=session.job_description,
            level=session.level,
        )

    def _interview_turn(
        self, pg_conn, session, brief, action, text, turn_id, model_spec, usage
    ) -> bool:
        context = AgentContext.from_json(session.agent_context)
        if action == "retry":
            new_messages = None
        else:
            message, context = build_turn_message(
                session, action, text, context, datetime.now(UTC)
            )
            new_messages = [HumanMessage(content=message)]
        outcome = run_interview_turn(
            session.id,
            require_model(model_spec),
            usage,
            interviewer_prompt(brief, session.level),
            new_messages,
            [
                HumanMessage(content=INTERVIEW_KICKOFF),
                AIMessage(content=opening_message(brief)),
            ],
        )
        save_system_design_turn(
            pg_conn,
            session.id,
            reply=outcome.reply,
            phase=session.phase,
            agent_context=context.to_json(),
            interview_over=outcome.interview_over,
            # Grading still has to run — a redelivery must not skip it.
            turn_id=None if outcome.interview_over else turn_id,
        )
        return outcome.interview_over

    def _grade(self, pg_conn, session, brief, turn_id, grader_spec, usage) -> None:
        try:
            durations = {
                k: int(v) for k, v in json.loads(session.phase_durations).items()
            }
        except (ValueError, TypeError, AttributeError):
            durations = {}
        report = grade_interview(
            require_model(grader_spec),
            usage,
            brief=brief,
            level=session.level,
            transcript=fetch_system_design_transcript(pg_conn, session.id),
            requirements=session.requirements,
            estimates=session.estimates,
            graph=normalize_scene(parse_scene(session.diagram)),
            phase_durations=durations,
        )
        complete_system_design_session(pg_conn, session.id, report, turn_id)

    def _bill(self, pg_conn, user_id, session_id, model, usage, suffix: str) -> None:
        if not (usage["input_tokens"] or usage["output_tokens"]):
            return
        try:
            charged = record_token_usage(
                pg_conn,
                user_id=user_id,
                job_kind="SYSTEM_DESIGN",
                job_id=usage_job_id(session_id, self.job_data) + suffix,
                model=model,
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
                generation_ids=usage["generation_ids"],
                cost_usd=usage["cost_usd"] if usage["all_costed"] else None,
            )
            print(f"Charged {charged}¢ for {session_id}{suffix}")
        except Exception as e:
            print(f"Failed to record token usage: {e}")

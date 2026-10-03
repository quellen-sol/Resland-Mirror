"""SystemDesignRunner task tests — input guards, the start / interview /
grading paths, redelivery and crash handling, and per-turn billing. The
agents and db_ops are patched in the runner module; the task thread is real.

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_system_design_runner -v
     (from the repo root with the workspace venv)
"""

import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from dispatcher.agents import system_design as sd
from dispatcher.runners import system_design as runner_mod
from shared.system_design.bank import get_problem, list_problems

from .test_runner_tasks import _pg_cm, _poll_until
from .test_system_design_agent import brief

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def row(**over):
    base = {
        "id": "s1",
        "user_id": "u1",
        "source": "BANK",
        "problem_id": list_problems()[0].id,
        "level": "SENIOR",
        "model": "openrouter:test/model",
        "status": "PROCESSING",
        "phase": "REQUIREMENTS",
        "title": None,
        "prompt": None,
        "brief": None,
        "phase_started_at": NOW,
        "created_at": NOW,
    }
    base.update(over)
    return sd.FetchSystemDesignSessionRow(**base)


def started(**over):
    b = brief()
    return row(title=b.title, prompt=b.prompt, brief=b.to_json(), **over)


def report():
    return sd.GradeReport(
        letter_grade="B",
        hire_signal="HIRE",
        weighted_score=3.0,
        level="SENIOR",
        dimensions=[],
        summary="ok",
        strengths=[],
        improvements=[],
        study_topics=[],
    )


class SystemDesignRunnerTask(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.db = MagicMock()
        self.db.default_model_spec.return_value = None
        self.db.fetch_system_design_transcript.return_value = []
        self.db.record_token_usage.return_value = 0.5
        names = [
            "complete_system_design_session",
            "default_model_spec",
            "fetch_system_design_session",
            "fetch_system_design_transcript",
            "record_token_usage",
            "save_system_design_turn",
            "set_system_design_notice",
            "start_system_design_session",
        ]
        patches = [patch.object(runner_mod, n, getattr(self.db, n)) for n in names]
        patches.append(
            patch.object(runner_mod, "get_pg_client", return_value=_pg_cm(self.conn))
        )
        self.agent = MagicMock()
        self.agent.run_interview_turn.return_value = sd.InterviewTurnOutcome(
            reply="Good question.", interview_over=False
        )
        self.agent.grade_interview.return_value = report()
        self.agent.generate_brief.return_value = brief(title="Payout Ledger")
        for n in ("run_interview_turn", "grade_interview", "generate_brief"):
            patches.append(patch.object(runner_mod, n, getattr(self.agent, n)))
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def run_job(self, job_data):
        handle = runner_mod.SystemDesignRunner(job_data).run()
        return _poll_until(handle, "COMPLETED")

    # Guards -----------------------------------------------------------

    def test_non_dict_job_data_fails(self):
        self.assertEqual(self.run_job(["nope"]), "FAILED")

    def test_missing_session_id_fails(self):
        self.assertEqual(self.run_job({"action": "start"}), "FAILED")

    def test_session_not_found_fails(self):
        self.db.fetch_system_design_session.return_value = None
        self.assertEqual(self.run_job({"session_id": "s1"}), "FAILED")

    def test_redelivered_turn_is_a_no_op(self):
        self.db.fetch_system_design_session.return_value = started(last_turn_id="t1")
        self.assertEqual(
            self.run_job(
                {"session_id": "s1", "action": "message", "text": "hi", "turn_id": "t1"}
            ),
            "COMPLETED",
        )
        self.agent.run_interview_turn.assert_not_called()
        self.db.save_system_design_turn.assert_not_called()

    # Start ------------------------------------------------------------

    def test_bank_start_posts_opening_without_an_llm_call(self):
        problem = list_problems()[0]
        self.db.fetch_system_design_session.return_value = row(problem_id=problem.id)
        self.assertEqual(
            self.run_job({"session_id": "s1", "turn_id": "t0"}), "COMPLETED"
        )
        kwargs = self.db.start_system_design_session.call_args.kwargs
        self.assertEqual(kwargs["title"], problem.title)
        self.assertEqual(kwargs["prompt"], problem.brief.prompt)
        self.assertIn(problem.title, kwargs["opening"])
        self.assertEqual(kwargs["turn_id"], "t0")
        self.assertEqual(get_problem(problem.id).brief.to_json(), kwargs["brief_json"])
        self.agent.generate_brief.assert_not_called()
        self.db.record_token_usage.assert_not_called()

    def test_unknown_bank_problem_fails(self):
        self.db.fetch_system_design_session.return_value = row(problem_id="nope")
        self.assertEqual(self.run_job({"session_id": "s1"}), "FAILED")

    def test_job_start_generates_a_brief_and_bills_it(self):
        self.db.fetch_system_design_session.return_value = row(
            source="JOB",
            problem_id=None,
            company_name="Stripe",
            role="Backend",
            job_description="Payouts in Go",
        )

        def gen(model_spec, usage, **kw):
            usage["input_tokens"] += 100
            usage["output_tokens"] += 50
            return brief(title="Payout Ledger")

        self.agent.generate_brief.side_effect = gen
        self.assertEqual(
            self.run_job({"session_id": "s1", "turn_id": "t0"}), "COMPLETED"
        )
        kw = self.agent.generate_brief.call_args.kwargs
        self.assertEqual(kw["company_name"], "Stripe")
        self.assertEqual(kw["job_description"], "Payouts in Go")
        self.assertEqual(kw["level"], "SENIOR")
        self.assertEqual(
            self.db.start_system_design_session.call_args.kwargs["title"],
            "Payout Ledger",
        )
        usage_kw = self.db.record_token_usage.call_args.kwargs
        self.assertEqual(usage_kw["job_kind"], "SYSTEM_DESIGN")
        self.assertEqual(usage_kw["job_id"], "s1:t0")
        self.assertEqual(usage_kw["input_tokens"], 100)

    def test_job_start_without_posting_fails(self):
        self.db.fetch_system_design_session.return_value = row(
            source="JOB", problem_id=None, job_description=None
        )
        self.assertEqual(self.run_job({"session_id": "s1"}), "FAILED")

    # Interview turns -----------------------------------------------------

    def test_message_turn_posts_the_reply(self):
        self.db.fetch_system_design_session.return_value = started(
            requirements="Shorten links"
        )
        self.assertEqual(
            self.run_job(
                {
                    "session_id": "s1",
                    "action": "message",
                    "text": "How many users?",
                    "turn_id": "t2",
                }
            ),
            "COMPLETED",
        )
        args, _kwargs = self.agent.run_interview_turn.call_args
        session_id, model_spec, _usage, system_prompt, new_messages, prefix = args
        self.assertEqual(session_id, "s1")
        self.assertEqual(model_spec, "openrouter:test/model")
        self.assertIn("URL Shortener", system_prompt)
        self.assertIn("How many users?", new_messages[0].content)
        self.assertIn("Shorten links", new_messages[0].content)
        self.assertEqual(prefix[0].content, sd.INTERVIEW_KICKOFF)
        self.assertIn("URL Shortener", prefix[1].content)
        save = self.db.save_system_design_turn.call_args.kwargs
        self.assertEqual(save["reply"], "Good question.")
        self.assertEqual(save["phase"], "REQUIREMENTS")
        self.assertFalse(save["interview_over"])
        self.assertEqual(save["turn_id"], "t2")
        self.assertIn("requirements_hash", save["agent_context"])
        self.agent.grade_interview.assert_not_called()

    def test_retry_resumes_without_a_new_message(self):
        self.db.fetch_system_design_session.return_value = started(phase="DEEP_DIVE")
        self.run_job({"session_id": "s1", "action": "retry", "turn_id": "t3"})
        self.assertIsNone(self.agent.run_interview_turn.call_args.args[4])

    def test_interview_over_saves_then_grades(self):
        self.agent.run_interview_turn.return_value = sd.InterviewTurnOutcome(
            reply="Thanks, that's time.", interview_over=True
        )
        self.db.fetch_system_design_session.side_effect = [
            started(phase="DEEP_DIVE"),
            started(phase="FEEDBACK", phase_durations='{"REQUIREMENTS": 300}'),
        ]
        self.db.fetch_system_design_transcript.return_value = [
            sd.TranscriptRow(role="CANDIDATE", phase="DEEP_DIVE", content="hi")
        ]
        self.assertEqual(
            self.run_job(
                {
                    "session_id": "s1",
                    "action": "message",
                    "text": "done",
                    "turn_id": "t9",
                }
            ),
            "COMPLETED",
        )
        save = self.db.save_system_design_turn.call_args.kwargs
        self.assertTrue(save["interview_over"])
        self.assertIsNone(save["turn_id"])
        grade_kw = self.agent.grade_interview.call_args.kwargs
        self.assertEqual(grade_kw["phase_durations"], {"REQUIREMENTS": 300})
        self.assertEqual(len(grade_kw["transcript"]), 1)
        args = self.db.complete_system_design_session.call_args.args
        self.assertEqual(args[1], "s1")
        self.assertEqual(args[2].letter_grade, "B")
        self.assertEqual(args[3], "t9")

    def test_feedback_phase_only_grades(self):
        self.db.fetch_system_design_session.return_value = started(phase="FEEDBACK")
        self.assertEqual(
            self.run_job({"session_id": "s1", "action": "finish", "turn_id": "t5"}),
            "COMPLETED",
        )
        self.agent.run_interview_turn.assert_not_called()
        self.agent.grade_interview.assert_called_once()
        self.db.complete_system_design_session.assert_called_once()

    def test_agent_crash_leaves_a_retry_notice(self):
        self.db.fetch_system_design_session.return_value = started()
        self.agent.run_interview_turn.side_effect = RuntimeError("provider down")
        self.assertEqual(
            self.run_job({"session_id": "s1", "action": "message", "text": "hi"}),
            "COMPLETED",
        )
        self.db.set_system_design_notice.assert_called_once_with(
            self.conn, "s1", runner_mod.RESUME_AFTER_ERROR_MESSAGE
        )
        self.db.save_system_design_turn.assert_not_called()

    def test_grading_crash_leaves_a_retry_notice(self):
        self.db.fetch_system_design_session.return_value = started(phase="FEEDBACK")
        self.agent.grade_interview.side_effect = RuntimeError("bad json")
        self.assertEqual(
            self.run_job({"session_id": "s1", "action": "finish"}), "COMPLETED"
        )
        self.db.set_system_design_notice.assert_called_once()
        self.db.complete_system_design_session.assert_not_called()

    # Billing ------------------------------------------------------------

    def test_turn_usage_is_billed_per_turn(self):
        self.db.fetch_system_design_session.return_value = started()

        def turn(session_id, model_spec, usage, *rest):
            usage["input_tokens"] += 12
            usage["output_tokens"] += 4
            usage["cost_usd"] += 0.01
            usage["generation_ids"].append("g1")
            return sd.InterviewTurnOutcome(reply="ok", interview_over=False)

        self.agent.run_interview_turn.side_effect = turn
        self.run_job(
            {"session_id": "s1", "action": "message", "text": "q", "turn_id": "t7"}
        )
        kw = self.db.record_token_usage.call_args.kwargs
        self.assertEqual(kw["user_id"], "u1")
        self.assertEqual(kw["job_kind"], "SYSTEM_DESIGN")
        self.assertEqual(kw["job_id"], "s1:t7")
        self.assertEqual(kw["model"], "openrouter:test/model")
        self.assertEqual(kw["generation_ids"], ["g1"])
        self.assertAlmostEqual(kw["cost_usd"], 0.01)

    def test_crashed_turn_still_bills_what_it_burned(self):
        self.db.fetch_system_design_session.return_value = started()

        def turn(session_id, model_spec, usage, *rest):
            usage["input_tokens"] += 5
            raise RuntimeError("mid-turn")

        self.agent.run_interview_turn.side_effect = turn
        self.run_job(
            {"session_id": "s1", "action": "message", "text": "q", "turn_id": "t8"}
        )
        self.assertEqual(self.db.record_token_usage.call_args.kwargs["input_tokens"], 5)

    def test_default_model_falls_back_to_admin_default(self):
        self.db.fetch_system_design_session.return_value = started(model=None)
        self.db.default_model_spec.return_value = "openrouter:admin/default"
        self.run_job({"session_id": "s1", "action": "message", "text": "q"})
        self.assertEqual(
            self.agent.run_interview_turn.call_args.args[1], "openrouter:admin/default"
        )

    def test_unset_system_design_model_falls_back_to_tailor_model(self):
        # Deployments already configure TAILOR_MODEL; a missing
        # SYSTEM_DESIGN_MODEL must not leave the interviewer without a model.
        self.db.fetch_system_design_session.return_value = started(model=None)
        with (
            patch.object(runner_mod, "SYSTEM_DESIGN_MODEL", ""),
            patch.object(runner_mod, "TAILOR_MODEL", "openrouter:tailor/model"),
        ):
            self.run_job({"session_id": "s1", "action": "advance"})
        self.assertEqual(
            self.agent.run_interview_turn.call_args.args[1], "openrouter:tailor/model"
        )

    def test_no_model_configured_leaves_a_retry_notice(self):
        self.db.fetch_system_design_session.return_value = started(model=None)
        with (
            patch.object(runner_mod, "SYSTEM_DESIGN_MODEL", ""),
            patch.object(runner_mod, "TAILOR_MODEL", ""),
        ):
            status = self.run_job({"session_id": "s1", "action": "advance"})
        self.assertEqual(status, "COMPLETED")
        self.agent.run_interview_turn.assert_not_called()
        self.db.set_system_design_notice.assert_called_once()

    def test_no_model_configured_still_starts_a_bank_problem(self):
        # Bank starts never call a model, so they don't need one.
        self.db.fetch_system_design_session.return_value = row(model=None)
        with (
            patch.object(runner_mod, "SYSTEM_DESIGN_MODEL", ""),
            patch.object(runner_mod, "TAILOR_MODEL", ""),
        ):
            self.run_job({"session_id": "s1"})
        self.db.start_system_design_session.assert_called_once()
        self.db.set_system_design_notice.assert_not_called()

    def test_job_start_crash_leaves_a_retry_notice(self):
        self.db.fetch_system_design_session.return_value = row(
            source="JOB", problem_id=None, job_description="Payouts in Go"
        )
        self.agent.generate_brief.side_effect = RuntimeError("provider down")
        self.assertEqual(self.run_job({"session_id": "s1"}), "COMPLETED")
        self.db.set_system_design_notice.assert_called_once()
        self.db.start_system_design_session.assert_not_called()

    def test_separate_grader_model_bills_its_own_row(self):
        self.db.fetch_system_design_session.return_value = started(phase="FEEDBACK")

        def grade(model_spec, usage, **kw):
            usage["input_tokens"] += 300
            return report()

        self.agent.grade_interview.side_effect = grade
        with patch.object(
            runner_mod, "SYSTEM_DESIGN_GRADER_MODEL", "openrouter:big/grader"
        ):
            self.run_job({"session_id": "s1", "action": "finish", "turn_id": "t4"})
        self.assertEqual(
            self.agent.grade_interview.call_args.args[0], "openrouter:big/grader"
        )
        rows = [c.kwargs for c in self.db.record_token_usage.call_args_list]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["job_id"], "s1:t4:grade")
        self.assertEqual(rows[0]["model"], "openrouter:big/grader")
        self.assertEqual(rows[0]["input_tokens"], 300)


if __name__ == "__main__":
    unittest.main()

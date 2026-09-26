"""Runner task tests — LocalThreadJobRunner subclasses' task() paths:
input guards, fetched-row guards, happy-path side effects, and the
crash-recovery write. All externals (S3, PG, agents) are patched in each
runner module's namespace; the task thread is real.

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_runner_tasks -v
     (from the repo root with the workspace venv)
"""

import io
import queue
import time
import unittest
from unittest.mock import MagicMock, patch

from dispatcher.agents import suggestions as sugg_agents
from dispatcher.agents import tailor as tailor_agents
from dispatcher.runners import resume, suggestions, tailor


def _poll_until(handle, status, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = handle.poll()
        if result == status:
            return result
        if result == "FAILED":
            return result
        time.sleep(0.05)
    return handle.poll()


def _pg_cm(conn=None):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=conn or MagicMock())
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _sugg_row(**over):
    base = dict(
        pending_question=None,
        status="PROCESSING",
        result=None,
        model="openrouter:test/model",
        user_id="u1",
        company_name="Acme",
        description=None,
        start_date="Jan 2020",
        end_date=None,
        title="Engineer",
        bullet_id=7,
        bullet="Built the thing",
    )
    base.update(over)
    return sugg_agents.FetchSuggestionRow(**base)


def _tailor_profile(**over):
    base = dict(
        header=None,
        social_links=[],
        experiences=[
            tailor_agents.TailorExperienceRow(
                experience_id=1,
                company_name="Acme",
                title="Engineer",
                start_date="2020",
                end_date=None,
                description=None,
                bullet_id=10,
                bullet="Built the thing",
                bullet_order=0,
            )
        ],
        skills=[],
        education=[],
        projects=[],
    )
    base.update(over)
    return tailor_agents.TailorProfile(**base)


def _tailor_run(**over):
    base = dict(
        id="run-1",
        user_id="u1",
        job_description="JD",
        status="PROCESSING",
        model="openrouter:test/model",
    )
    base.update(over)
    return tailor_agents.FetchTailorRunRow(**base)


class ResumeRunnerTask(unittest.TestCase):
    def _patches(self, **kw):
        return [
            patch.object(resume, "get_s3_client", return_value=kw.get("s3") or MagicMock()),
            patch.object(resume, "get_pg_client", return_value=kw.get("pg") or _pg_cm()),
            patch.object(resume, "agent_parse_docx", return_value=kw.get("agent_q") or queue.Queue()),
            patch.object(resume, "agent_parse_pdf", return_value=kw.get("agent_q") or queue.Queue()),
            patch.object(resume, "parse_docx", return_value=kw.get("src") or MagicMock(name="src")),
            patch.object(resume, "parse_pdf", return_value=kw.get("src") or MagicMock(name="src")),
            patch.object(resume, "capture_format_profile", return_value=kw.get("fmt") or "FMT"),
            patch.object(resume, "capture_format_profile_pdf", return_value=kw.get("fmt") or "FMT"),
            patch.object(resume, "upsert_user_profile"),
            patch.object(resume, "upsert_resume_format"),
            patch.object(resume, "puremagic", kw.get("puremagic") or MagicMock(**{"from_string.return_value": ".docx"})),
        ]

    def _run(self, job_data, **kw):
        patches = self._patches(**kw)
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        handle = resume.ResumeRunner(job_data).run()
        status = _poll_until(handle, "COMPLETED")
        return status, patches

    def test_empty_job_data_fails(self):
        status, _ = self._run({})
        self.assertEqual(status, "FAILED")

    def test_non_dict_job_data_fails(self):
        status, _ = self._run("oops")
        self.assertEqual(status, "FAILED")

    def test_user_not_found_fails(self):
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = None
        status, _ = self._run(
            {"job_id": "j1", "user_id": "u1", "s3_key": "k"},
            pg=_pg_cm(conn),
        )
        self.assertEqual(status, "FAILED")

    def test_missing_s3_key_fails(self):
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = ("auth0|u1",)
        status, _ = self._run(
            {"job_id": "j1", "user_id": "u1"}, pg=_pg_cm(conn)
        )
        self.assertEqual(status, "FAILED")

    def test_unsupported_file_type_fails(self):
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = ("auth0|u1",)
        s3 = MagicMock()
        s3.get_object.return_value = {"Body": io.BytesIO(b"bytes")}
        status, _ = self._run(
            {"job_id": "j1", "user_id": "u1", "s3_key": "k"},
            pg=_pg_cm(conn),
            s3=s3,
            puremagic=MagicMock(**{"from_string.return_value": ".png"}),
        )
        self.assertEqual(status, "FAILED")

    def test_empty_profile_queue_fails(self):
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = ("auth0|u1",)
        s3 = MagicMock()
        s3.get_object.return_value = {"Body": io.BytesIO(b"bytes")}
        status, _ = self._run(
            {"job_id": "j1", "user_id": "u1", "s3_key": "k"},
            pg=_pg_cm(conn),
            s3=s3,
            agent_q=queue.Queue(),
        )
        self.assertEqual(status, "FAILED")

    def test_happy_path_writes_profile_and_format(self):
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = ("auth0|u1",)
        s3 = MagicMock()
        s3.get_object.return_value = {"Body": io.BytesIO(b"docx-bytes")}
        q = queue.Queue()
        profile = MagicMock(name="profile")
        q.put(profile)
        src = MagicMock(name="src")
        status, patches = self._run(
            {"job_id": "j1", "user_id": "u1", "s3_key": "k"},
            pg=_pg_cm(conn),
            s3=s3,
            agent_q=q,
            src=src,
            fmt="FMT",
        )
        self.assertEqual(status, "COMPLETED")
        resume.upsert_user_profile.assert_called_once_with(conn, "u1", profile)
        resume.capture_format_profile.assert_called_once_with(src, profile)
        resume.upsert_resume_format.assert_called_once_with(conn, "u1", "FMT", "j1")

    def test_pdf_happy_path_uses_pdf_pipeline(self):
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = ("auth0|u1",)
        s3 = MagicMock()
        s3.get_object.return_value = {"Body": io.BytesIO(b"%PDF-1.4 fake")}
        q = queue.Queue()
        profile = MagicMock(name="profile")
        q.put(profile)
        src = MagicMock(name="pdf-src")
        status, _ = self._run(
            {"job_id": "j1", "user_id": "u1", "s3_key": "k"},
            pg=_pg_cm(conn),
            s3=s3,
            agent_q=q,
            src=src,
            fmt="PDF-FMT",
            puremagic=MagicMock(**{"from_string.return_value": ".pdf"}),
        )
        self.assertEqual(status, "COMPLETED")
        resume.parse_pdf.assert_called_once()
        resume.agent_parse_pdf.assert_called_once_with(src)
        resume.agent_parse_docx.assert_not_called()
        resume.upsert_user_profile.assert_called_once_with(conn, "u1", profile)
        resume.capture_format_profile_pdf.assert_called_once_with(src, profile)
        resume.capture_format_profile.assert_not_called()
        resume.upsert_resume_format.assert_called_once_with(
            conn, "u1", "PDF-FMT", "j1"
        )

    def test_pdf_with_no_extractable_text_fails(self):
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = ("auth0|u1",)
        s3 = MagicMock()
        s3.get_object.return_value = {"Body": io.BytesIO(b"%PDF-1.4 fake")}
        status, _ = self._run(
            {"job_id": "j1", "user_id": "u1", "s3_key": "k"},
            pg=_pg_cm(conn),
            s3=s3,
            src=MagicMock(name="pdf-src", lines=[]),
            puremagic=MagicMock(**{"from_string.return_value": ".pdf"}),
        )
        self.assertEqual(status, "FAILED")
        resume.agent_parse_pdf.assert_not_called()
        resume.upsert_user_profile.assert_not_called()


class SuggestionsRunnerTask(unittest.TestCase):
    def _run(self, job_data, rows=None, outcome=None, agent_exc=None, agent_fn=None):
        conn = MagicMock()
        agent = MagicMock()
        if agent_exc is not None:
            agent.side_effect = agent_exc
        elif agent_fn is not None:
            agent.side_effect = agent_fn
        else:
            agent.return_value = outcome
        with (
            patch.object(suggestions, "get_pg_client", return_value=_pg_cm(conn)),
            patch.object(suggestions, "fetch_suggestion_rows", return_value=rows or []),
            patch.object(suggestions, "default_model_spec", return_value=None),
            patch.object(suggestions, "build_and_invoke_agent", agent),
            patch.object(suggestions, "set_suggestion_question") as set_q,
            patch.object(suggestions, "set_suggestion_result") as set_r,
            patch.object(suggestions, "set_suggestion_failed") as set_f,
            patch.object(suggestions, "record_token_usage") as record,
        ):
            handle = suggestions.SuggestionsRunner(job_data).run()
            status = _poll_until(handle, "COMPLETED")
        return status, agent, set_q, set_r, record, set_f

    def test_empty_job_data_fails(self):
        status, *_ = self._run({})
        self.assertEqual(status, "FAILED")

    def test_non_dict_job_data_fails(self):
        status, *_ = self._run("oops")
        self.assertEqual(status, "FAILED")

    def test_missing_session_id_fails(self):
        status, *_ = self._run({"answer": "hi"})
        self.assertEqual(status, "FAILED")

    def test_non_string_session_id_fails(self):
        status, *_ = self._run({"session_id": 42})
        self.assertEqual(status, "FAILED")

    def test_session_not_found_fails(self):
        status, *_ = self._run({"session_id": "s1"}, rows=[])
        self.assertEqual(status, "FAILED")

    def test_waiting_outcome_sets_question(self):
        outcome = sugg_agents.SuggestionRunOutcome(status="waiting", question="Team size?")
        status, _, set_q, set_r, _, _ = self._run(
            {"session_id": "s1"}, rows=[_sugg_row()], outcome=outcome
        )
        self.assertEqual(status, "COMPLETED")
        set_q.assert_called_once()
        self.assertEqual(set_q.call_args.args[2], "Team size?")
        set_r.assert_not_called()

    def test_completed_outcome_sets_result(self):
        result = sugg_agents.SuggestionsResult(
            suggestions=[sugg_agents.BulletSuggestion(bullet_id=7, suggestion="x")]
        )
        outcome = sugg_agents.SuggestionRunOutcome(status="completed", result=result)
        status, _, _, set_r, _, _ = self._run(
            {"session_id": "s1"}, rows=[_sugg_row()], outcome=outcome
        )
        self.assertEqual(status, "COMPLETED")
        set_r.assert_called_once()

    def test_completed_without_result_fails(self):
        outcome = sugg_agents.SuggestionRunOutcome(status="completed", result=None)
        status, *_ = self._run({"session_id": "s1"}, rows=[_sugg_row()], outcome=outcome)
        self.assertEqual(status, "FAILED")

    def test_agent_crash_marks_session_failed_for_retry(self):
        status, _, set_q, set_r, _, set_f = self._run(
            {"session_id": "s1"},
            rows=[_sugg_row()],
            agent_exc=RuntimeError("provider down"),
        )
        self.assertEqual(status, "COMPLETED")
        set_f.assert_called_once()
        self.assertEqual(set_f.call_args.args[1], "s1")
        set_q.assert_not_called()
        set_r.assert_not_called()

    def test_prompt_is_forwarded_to_agent(self):
        outcome = sugg_agents.SuggestionRunOutcome(status="waiting", question="Q")
        status, agent, *_ = self._run(
            {"session_id": "s1", "prompt": "emphasize metrics"},
            rows=[_sugg_row()],
            outcome=outcome,
        )
        self.assertEqual(status, "COMPLETED")
        self.assertEqual(agent.call_args.args[5], "emphasize metrics")

    def test_missing_prompt_passes_none_to_agent(self):
        outcome = sugg_agents.SuggestionRunOutcome(status="waiting", question="Q")
        status, agent, *_ = self._run(
            {"session_id": "s1"}, rows=[_sugg_row()], outcome=outcome
        )
        self.assertEqual(status, "COMPLETED")
        self.assertIsNone(agent.call_args.args[5])

    def test_usage_is_recorded_with_suggestion_kind(self):
        def fake_agent(session_id, answer, rows, model_spec, usage, prompt):
            usage["input_tokens"] = 100
            usage["output_tokens"] = 20
            usage["cost_usd"] = 0.01
            usage["generation_ids"] = ["g1"]
            return sugg_agents.SuggestionRunOutcome(status="waiting", question="Q")

        status, _, _, _, record, _ = self._run(
            {"session_id": "s1"}, rows=[_sugg_row()], agent_fn=fake_agent
        )
        self.assertEqual(status, "COMPLETED")
        record.assert_called_once()
        kwargs = record.call_args.kwargs
        self.assertEqual(kwargs["job_kind"], "SUGGESTION")
        self.assertEqual(kwargs["job_id"], "s1")
        self.assertEqual(kwargs["input_tokens"], 100)
        self.assertEqual(kwargs["cost_usd"], 0.01)

    def test_no_usage_no_record(self):
        outcome = sugg_agents.SuggestionRunOutcome(status="waiting", question="Q")
        status, _, _, _, record, _ = self._run(
            {"session_id": "s1"}, rows=[_sugg_row()], outcome=outcome
        )
        self.assertEqual(status, "COMPLETED")
        record.assert_not_called()


class TailorRunnerTask(unittest.TestCase):
    def _run(self, job_data, run=None, profile=None, outcome=None, agent_exc=None, agent_fn=None):
        conn = MagicMock()
        agent = MagicMock()
        if agent_exc is not None:
            agent.side_effect = agent_exc
        elif agent_fn is not None:
            agent.side_effect = agent_fn
        else:
            agent.return_value = outcome
        with (
            patch.object(tailor, "get_pg_client", return_value=_pg_cm(conn)),
            patch.object(tailor, "fetch_tailor_run", return_value=run),
            patch.object(tailor, "fetch_tailor_profile", return_value=profile),
            patch.object(tailor, "default_model_spec", return_value=None),
            patch.object(tailor, "build_and_invoke_agent", agent),
            patch.object(tailor, "set_tailor_question") as set_q,
            patch.object(tailor, "set_tailor_result") as set_r,
            patch.object(tailor, "record_token_usage") as record,
        ):
            handle = tailor.TailorRunner(job_data).run()
            status = _poll_until(handle, "COMPLETED")
        return status, set_q, set_r, record

    def test_missing_run_id_fails(self):
        status, *_ = self._run({})
        self.assertEqual(status, "FAILED")

    def test_non_dict_job_data_fails(self):
        status, *_ = self._run("oops")
        self.assertEqual(status, "FAILED")

    def test_non_string_run_id_fails(self):
        status, *_ = self._run({"run_id": 7})
        self.assertEqual(status, "FAILED")

    def test_run_not_found_fails(self):
        status, *_ = self._run({"run_id": "r1"}, run=None)
        self.assertEqual(status, "FAILED")

    def test_no_experiences_fails(self):
        status, *_ = self._run(
            {"run_id": "r1"},
            run=_tailor_run(),
            profile=_tailor_profile(experiences=[]),
        )
        self.assertEqual(status, "FAILED")

    def test_waiting_outcome_sets_question(self):
        outcome = tailor_agents.TailorRunOutcome(status="waiting", question="Summary?")
        status, set_q, set_r, _ = self._run(
            {"run_id": "r1"}, run=_tailor_run(), profile=_tailor_profile(), outcome=outcome
        )
        self.assertEqual(status, "COMPLETED")
        self.assertEqual(set_q.call_args.args[2], "Summary?")
        set_r.assert_not_called()

    def test_completed_outcome_sets_result(self):
        result = tailor_agents.TailoredResume(
            summary=None,
            experiences=[
                tailor_agents.TailoredExperience(
                    experience_id=1,
                    bullets=[tailor_agents.TailoredBullet(bullet_id=10, text="x")],
                )
            ],
            skills=[],
        )
        outcome = tailor_agents.TailorRunOutcome(status="completed", result=result)
        status, _, set_r, _ = self._run(
            {"run_id": "r1"}, run=_tailor_run(), profile=_tailor_profile(), outcome=outcome
        )
        self.assertEqual(status, "COMPLETED")
        set_r.assert_called_once()

    def test_agent_crash_sets_resume_question(self):
        status, set_q, _, _ = self._run(
            {"run_id": "r1"},
            run=_tailor_run(),
            profile=_tailor_profile(),
            agent_exc=RuntimeError("boom"),
        )
        self.assertEqual(status, "COMPLETED")
        self.assertEqual(set_q.call_args.args[2], tailor.RESUME_AFTER_ERROR_MESSAGE)

    def test_agent_usage_is_recorded(self):
        def _agent(run_id, answer, run, profile, model_spec, usage):
            usage["input_tokens"] = 1
            usage["output_tokens"] = 1
            usage["cost_usd"] = 0.5
            usage["generation_ids"] = ["gen-1"]
            usage["all_costed"] = True
            return tailor_agents.TailorRunOutcome(status="waiting", question="Q")

        status, _, _, record = self._run(
            {"run_id": "r1"},
            run=_tailor_run(),
            profile=_tailor_profile(),
            agent_fn=_agent,
        )
        self.assertEqual(status, "COMPLETED")
        _, kw = record.call_args
        self.assertEqual(kw["job_kind"], "TAILOR")
        self.assertEqual(kw["job_id"], "r1")
        self.assertEqual(kw["cost_usd"], 0.5)
        self.assertEqual(kw["generation_ids"], ["gen-1"])

    def test_zero_usage_skips_billing_record(self):
        status, _, _, record = self._run(
            {"run_id": "r1"},
            run=_tailor_run(),
            profile=_tailor_profile(),
            outcome=tailor_agents.TailorRunOutcome(status="waiting", question="Q"),
        )
        self.assertEqual(status, "COMPLETED")
        record.assert_not_called()


if __name__ == "__main__":
    unittest.main()

"""Agent tests — the real compiled LangGraph, driven by a scripted fake
chat model and an in-memory checkpointer (no LLM calls, no Postgres).

`init_chat_model`, `PostgresSaver`, and `get_pg_client` are patched in each
agent module; everything between — the graph, tools, interrupt/resume
plumbing, and usage accounting — is the production code.

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_agents -v
     (from the repo root with the workspace venv)
"""

import io
import unittest
from unittest.mock import MagicMock, patch

import docx
from langchain.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from dispatcher.agents import docx_parser, suggestions, tailor


class FakeChatModel:
    """bind_tools() returns self; invoke() pops the next scripted message
    and records every message list it's shown (so tests can read the
    ToolMessages the graph fed back)."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []
        self.bound_tools = []

    def bind_tools(self, tools):
        self.bound_tools = list(tools)
        return self

    def invoke(self, messages):
        self.calls.append(list(messages))
        nxt = self.script.pop(0)
        return nxt() if callable(nxt) else nxt


def ai(content="", tool_calls=None, in_tok=10, out_tok=5, cost=0.001, gen="gen-1"):
    return AIMessage(
        content=content,
        tool_calls=tool_calls or [],
        usage_metadata={
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "total_tokens": in_tok + out_tok,
        },
        response_metadata={"cost": cost, "id": gen},
    )


def tc(name, args, tc_id="tc-1", **kw):
    return ai(
        tool_calls=[{"name": name, "args": args, "id": tc_id, "type": "tool_call"}],
        **kw,
    )


def _patch_model(module, script):
    return patch.object(module, "init_chat_model", return_value=FakeChatModel(script))


def _patch_infra(module, saver):
    """PostgresSaver → a real (in-memory) checkpointer; get_pg_client → a
    dummy context manager whose conn is never used."""
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock())
    cm.__exit__ = MagicMock(return_value=False)
    return (
        patch.object(module, "PostgresSaver", return_value=saver),
        patch.object(module, "get_pg_client", return_value=cm),
    )


def sugg_row(**over):
    base = dict(
        pending_question=None,
        status="PROCESSING",
        result=None,
        model=None,
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
    return suggestions.FetchSuggestionRow(**base)


def tailor_profile(**over):
    base = dict(
        header=tailor.TailorHeaderRow(
            full_name="Jane", email=None, phone=None, location=None
        ),
        social_links=[],
        experiences=[
            tailor.TailorExperienceRow(
                experience_id=1,
                company_name="Acme",
                title="Engineer",
                start_date="2020",
                end_date=None,
                description=None,
                bullet_id=10,
                bullet="Built the thing",
                bullet_order=0,
            ),
            tailor.TailorExperienceRow(
                experience_id=2,
                company_name="Beta",
                title="Senior",
                start_date="2022",
                end_date=None,
                description=None,
                bullet_id=20,
                bullet="Shipped the other thing",
                bullet_order=0,
            ),
        ],
        skills=[tailor.TailorSkillRow(name="Python", category=None)],
        education=[],
        projects=[],
    )
    base.update(over)
    return tailor.TailorProfile(**base)


def tailor_run(**over):
    base = dict(
        id="run-1",
        user_id="u1",
        job_description="We need a Python engineer.",
        status="PROCESSING",
        model=None,
    )
    base.update(over)
    return tailor.FetchTailorRunRow(**base)


def _usage():
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "generation_ids": [],
        "cost_usd": 0.0,
        "all_costed": True,
    }


def _last_tool_msg(model):
    """The most recent ToolMessage the model was shown."""
    for msg in reversed(model.calls[-1]):
        if getattr(msg, "type", None) == "tool":
            return msg
    return None


class SuggestionAgent(unittest.TestCase):
    def setUp(self):
        self.saver = InMemorySaver()
        self.pg_patch, self.saver_patch = _patch_infra(suggestions, self.saver)
        self.pg_patch.start()
        self.saver_patch.start()
        self.addCleanup(self.pg_patch.stop)
        self.addCleanup(self.saver_patch.stop)

    def _run(
        self,
        script,
        session_id="sess-1",
        answer=None,
        rows=None,
        usage=None,
        prompt=None,
    ):
        with _patch_model(suggestions, script) as model_cls:
            outcome = suggestions.build_and_invoke_agent(
                session_id,
                answer,
                rows if rows is not None else [sugg_row()],
                "openrouter:test/model",
                usage if usage is not None else _usage(),
                prompt,
            )
        return outcome, model_cls.return_value

    def test_completed_flow_submits_and_counts_usage(self):
        outcome, model = self._run(
            [
                tc("get_user_bullet_points", {}),
                tc(
                    "verify_final_suggestions",
                    {"suggestions": {"suggestions": [{"bullet_id": 7, "suggestion": "Did x"}]}},
                    tc_id="tc-2",
                ),
                tc(
                    "submit_suggestions",
                    {"suggestions": {"suggestions": [{"bullet_id": 7, "suggestion": "Did x"}]}},
                    tc_id="tc-3",
                ),
            ]
        )
        self.assertEqual(outcome.status, "completed")
        self.assertEqual(outcome.result.suggestions[0].suggestion, "Did x")

    def test_bullet_points_tool_returns_experience_rows(self):
        _, model = self._run(
            [
                tc("get_user_bullet_points", {}),
                tc(
                    "submit_suggestions",
                    {"suggestions": {"suggestions": [{"bullet_id": 7, "suggestion": "x"}]}},
                    tc_id="tc-2",
                ),
            ]
        )
        tool_msg = model.calls[1][-1]
        self.assertIn('"Acme"', tool_msg.content)
        self.assertIn('"Built the thing"', tool_msg.content)
        # Session-internal fields are stripped from what the model sees.
        self.assertNotIn("user_id", tool_msg.content)
        self.assertNotIn("pending_question", tool_msg.content)

    def test_clarifying_question_waits_with_question(self):
        outcome, _ = self._run(
            [tc("ask_clarifying_question", {"question": "How many engineers?"})]
        )
        self.assertEqual(outcome.status, "waiting")
        self.assertEqual(outcome.question, "How many engineers?")

    def test_answer_resumes_interrupt(self):
        # First run ends waiting on a question; the answer resumes the
        # same checkpoint (shared saver) and the tool returns it.
        self._run([tc("ask_clarifying_question", {"question": "Team size?"})])
        outcome, model = self._run(
            [
                tc(
                    "submit_suggestions",
                    {"suggestions": {"suggestions": [{"bullet_id": 7, "suggestion": "x"}]}},
                )
            ],
            answer="5 engineers",
        )
        self.assertEqual(outcome.status, "completed")
        resumed_msg = model.calls[0][-1]
        self.assertEqual(resumed_msg.content, "5 engineers")

    def test_custom_prompt_seeds_kickoff_message(self):
        outcome, model = self._run(
            [ai("done")],
            prompt="Keep them under 10 words",
        )
        self.assertEqual(outcome.status, "completed")
        kickoff = model.calls[0][-1]
        self.assertEqual(kickoff.type, "human")
        self.assertIn("Keep them under 10 words", kickoff.content)

    def test_retry_resumes_checkpoint_without_new_kickoff(self):
        # First run crashes mid-node — the checkpoint keeps llm_call pending.
        def boom():
            raise RuntimeError("provider down")

        with self.assertRaises(RuntimeError):
            self._run([boom])

        # Retry with no answer: the pending node resumes in place instead of
        # a duplicate kickoff message being injected.
        outcome, model = self._run(
            [
                tc(
                    "submit_suggestions",
                    {"suggestions": {"suggestions": [{"bullet_id": 7, "suggestion": "x"}]}},
                )
            ]
        )
        self.assertEqual(outcome.status, "completed")
        humans = [
            m
            for m in model.calls[0]
            if getattr(m, "type", None) == "human"
        ]
        self.assertEqual(len(humans), 1)
        self.assertIn("get_user_bullet_points", humans[0].content)

    def test_answer_on_finished_run_hits_empty_input_fallback(self):
        # Command(resume) on a checkpoint with no pending interrupt raises
        # EmptyInputError — the code falls back to invoke(None).
        self._run(
            [
                tc(
                    "submit_suggestions",
                    {"suggestions": {"suggestions": [{"bullet_id": 7, "suggestion": "x"}]}},
                )
            ]
        )
        outcome, _ = self._run([], answer="late answer")
        self.assertEqual(outcome.status, "completed")

    def test_usage_accumulates_tokens_cost_and_generation_ids(self):
        usage = _usage()
        self._run(
            [
                tc("get_user_bullet_points", {}, in_tok=10, out_tok=5, cost=0.001),
                tc(
                    "submit_suggestions",
                    {"suggestions": {"suggestions": [{"bullet_id": 7, "suggestion": "x"}]}},
                    in_tok=20,
                    out_tok=8,
                    cost=0.002,
                    gen="gen-2",
                    tc_id="tc-2",
                ),
            ],
            usage=usage,
        )
        self.assertEqual(usage["input_tokens"], 30)
        self.assertEqual(usage["output_tokens"], 13)
        self.assertAlmostEqual(usage["cost_usd"], 0.003)
        self.assertEqual(usage["generation_ids"], ["gen-1", "gen-2"])
        self.assertTrue(usage["all_costed"])

    def test_missing_inline_cost_marks_not_all_costed(self):
        usage = _usage()
        msg = tc("get_user_bullet_points", {})
        msg.response_metadata = {"id": "gen-9"}  # no cost field
        self._run(
            [
                msg,
                tc(
                    "submit_suggestions",
                    {"suggestions": {"suggestions": [{"bullet_id": 7, "suggestion": "x"}]}},
                    tc_id="tc-2",
                    gen="gen-2",
                ),
            ],
            usage=usage,
        )
        self.assertFalse(usage["all_costed"])
        self.assertEqual(usage["generation_ids"], ["gen-9", "gen-2"])

    def test_verify_rejects_unknown_bullet_id(self):
        _, model = self._run(
            [
                tc(
                    "verify_final_suggestions",
                    {"suggestions": {"suggestions": [{"bullet_id": 999, "suggestion": "x"}]}},
                ),
                tc(
                    "submit_suggestions",
                    {"suggestions": {"suggestions": [{"bullet_id": 7, "suggestion": "x"}]}},
                    tc_id="tc-2",
                ),
            ]
        )
        self.assertIn("Invalid bullet id (999)", _last_tool_msg(model).content)

    def test_verify_accepts_valid_ids(self):
        _, model = self._run(
            [
                tc(
                    "verify_final_suggestions",
                    {"suggestions": {"suggestions": [{"bullet_id": 7, "suggestion": "x"}]}},
                ),
                ai("done"),
            ]
        )
        self.assertIn("bullet ids are valid", _last_tool_msg(model).content)


class TailorAgent(unittest.TestCase):
    def setUp(self):
        self.saver = InMemorySaver()
        self.pg_patch, self.saver_patch = _patch_infra(tailor, self.saver)
        self.pg_patch.start()
        self.saver_patch.start()
        self.addCleanup(self.pg_patch.stop)
        self.addCleanup(self.saver_patch.stop)

    def _run(self, script, run_id="run-1", answer=None, run=None, profile=None, usage=None):
        with _patch_model(tailor, script) as model_cls:
            outcome = tailor.build_and_invoke_agent(
                run_id,
                answer,
                run if run is not None else tailor_run(),
                profile if profile is not None else tailor_profile(),
                "openrouter:test/model",
                usage if usage is not None else _usage(),
            )
        return outcome, model_cls.return_value

    def _verify_call(self, resume):
        return tc("verify_tailored_resume", {"resume": resume})

    def test_completed_flow_submits_resume(self):
        resume = {
            "summary": None,
            "experiences": [
                {"experience_id": 1, "bullets": [{"bullet_id": 10, "text": "Built x"}]}
            ],
            "skills": ["Python"],
        }
        outcome, _ = self._run(
            [
                tc("get_job_description", {}),
                tc("get_user_profile", {}),
                self._verify_call(resume),
                tc("submit_tailored_resume", {"resume": resume}, tc_id="tc-4"),
            ]
        )
        self.assertEqual(outcome.status, "completed")
        self.assertEqual(outcome.result.skills, ["Python"])
        self.assertEqual(outcome.result.experiences[0].experience_id, 1)

    def test_tools_hand_back_job_description_and_profile(self):
        _, model = self._run(
            [
                tc("get_job_description", {}),
                tc("get_user_profile", {}),
                ai("done"),
            ]
        )
        self.assertIn("Python engineer", model.calls[1][-1].content)
        self.assertIn('"Acme"', model.calls[2][-1].content)

    def test_clarifying_question_waits_then_resumes(self):
        self._run([tc("ask_clarifying_question", {"question": "Want a summary?"})])
        run = tailor_run()
        profile = tailor_profile()
        resume = {
            "summary": "Yes please",
            "experiences": [
                {"experience_id": 1, "bullets": [{"bullet_id": 10, "text": "x"}]}
            ],
            "skills": [],
        }
        outcome, model = self._run(
            [tc("submit_tailored_resume", {"resume": resume})],
            answer="yes, write one",
            run=run,
            profile=profile,
        )
        self.assertEqual(outcome.status, "completed")
        self.assertEqual(model.calls[0][-1].content, "yes, write one")

    def test_usage_accumulates(self):
        usage = _usage()
        resume = {
            "summary": None,
            "experiences": [
                {"experience_id": 1, "bullets": [{"bullet_id": 10, "text": "x"}]}
            ],
            "skills": [],
        }
        self._run(
            [
                tc("get_job_description", {}, in_tok=3, out_tok=2, cost=0.0005),
                tc("submit_tailored_resume", {"resume": resume}, in_tok=7, out_tok=4, cost=0.0005, gen="gen-2", tc_id="tc-2"),
            ],
            usage=usage,
        )
        self.assertEqual(usage["input_tokens"], 10)
        self.assertEqual(usage["output_tokens"], 6)
        self.assertAlmostEqual(usage["cost_usd"], 0.001)
        self.assertEqual(usage["generation_ids"], ["gen-1", "gen-2"])

    def _verify_feedback(self, resume):
        _, model = self._run([self._verify_call(resume), ai("done")])
        return _last_tool_msg(model).content

    def test_verify_requires_an_experience(self):
        msg = self._verify_feedback({"summary": None, "experiences": [], "skills": []})
        self.assertIn("at least one experience", msg)

    def test_verify_rejects_unknown_experience(self):
        msg = self._verify_feedback(
            {
                "summary": None,
                "experiences": [{"experience_id": 99, "bullets": []}],
                "skills": [],
            }
        )
        self.assertIn("Invalid experience id (99)", msg)

    def test_verify_rejects_bullet_under_wrong_experience(self):
        msg = self._verify_feedback(
            {
                "summary": None,
                "experiences": [
                    {"experience_id": 1, "bullets": [{"bullet_id": 20, "text": "x"}]}
                ],
                "skills": [],
            }
        )
        self.assertIn("does not belong", msg)

    def test_verify_rejects_duplicate_bullets(self):
        msg = self._verify_feedback(
            {
                "summary": None,
                "experiences": [
                    {
                        "experience_id": 1,
                        "bullets": [
                            {"bullet_id": 10, "text": "x"},
                            {"bullet_id": 10, "text": "y"},
                        ],
                    }
                ],
                "skills": [],
            }
        )
        self.assertIn("Duplicate bullet id (10)", msg)

    def test_verify_rejects_unknown_skills(self):
        msg = self._verify_feedback(
            {
                "summary": None,
                "experiences": [
                    {"experience_id": 1, "bullets": [{"bullet_id": 10, "text": "x"}]}
                ],
                "skills": ["Kubernetes"],
            }
        )
        self.assertIn("Skills not present", msg)

    def test_verify_accepts_valid_resume(self):
        msg = self._verify_feedback(
            {
                "summary": None,
                "experiences": [
                    {"experience_id": 1, "bullets": [{"bullet_id": 10, "text": "x"}]}
                ],
                "skills": ["Python"],
            }
        )
        self.assertIn("All ids are valid", msg)

    def test_missing_inline_cost_marks_not_all_costed(self):
        usage = _usage()
        msg = tc("get_user_profile", {})
        msg.response_metadata = {"id": "gen-9"}  # no cost field
        _, _ = self._run(
            [
                msg,
                self._verify_call({"summary": None, "experiences": [], "skills": []}),
                tc("submit_tailored_resume", {"resume": {"summary": None, "experiences": [], "skills": []}}, tc_id="tc-3"),
            ],
            usage=usage,
        )
        self.assertFalse(usage["all_costed"])
        self.assertIn("gen-9", usage["generation_ids"])


def _doc():
    buf = io.BytesIO()
    d = docx.Document()
    d.add_paragraph("Jane Doe")
    d.add_paragraph("Engineer at Acme")
    d.save(buf)
    buf.seek(0)
    return docx.Document(buf)


class DocxParserAgent(unittest.TestCase):
    def _build(self):
        """build_resume_agent with create_agent stubbed — returns the
        captured tools/model plus the profile queue."""
        agent = MagicMock()
        with patch.object(
            docx_parser, "create_agent", return_value=agent
        ) as create:
            out = docx_parser.build_resume_agent(_doc())
        _, kwargs = create.call_args
        tools = {t.name: t for t in kwargs["tools"]}
        return out, agent, kwargs, tools

    def test_create_agent_wired_with_model_tools_prompt(self):
        _, _, kwargs, tools = self._build()
        self.assertEqual(kwargs["model"], docx_parser.RESUME_PARSER_MODEL)
        self.assertEqual(kwargs["system_prompt"], docx_parser.DOCX_AGENT_PARSER_SYSTEM_PROMPT)
        self.assertEqual(
            set(tools),
            {
                "get_raw_doc_text",
                "get_block_sequence",
                "get_whitespace_map",
                "get_columns",
                "submit_user_profile",
            },
        )

    def test_tools_return_precomputed_doc_views(self):
        _, _, _, tools = self._build()
        self.assertIn("Jane Doe", tools["get_raw_doc_text"].invoke({}))
        blocks = tools["get_block_sequence"].invoke({})
        self.assertTrue(any("Jane Doe" in str(b) for b in blocks))
        self.assertIsInstance(tools["get_whitespace_map"].invoke({}), list)
        self.assertEqual(tools["get_columns"].invoke({}), [1])

    def test_submit_tool_fills_profile_queue(self):
        out, _, _, tools = self._build()
        profile = docx_parser.UserDocxProfile(
            summary="s",
            basic_info=docx_parser.UserProfileBasicInfo(
                name="Jane", email="", phone="", location=""
            ),
            experience=[],
            skills=[],
            education=[],
            projects=[],
        )
        tools["submit_user_profile"].invoke({"profile": profile})
        self.assertIs(out.profile_queue.get_nowait(), profile)

    def test_agent_parse_docx_invokes_and_returns_queue(self):
        out, agent, _, _ = self._build()
        with patch.object(
            docx_parser, "build_resume_agent", return_value=out
        ):
            q = docx_parser.agent_parse_docx(MagicMock())
        self.assertIs(q, out.profile_queue)
        agent.invoke.assert_called_once_with(
            {"messages": [{"role": "user", "content": "Parse this document"}]}
        )


if __name__ == "__main__":
    unittest.main()

"""System design agent tests — the real interviewer graph driven by the
scripted FakeChatModel with an in-memory checkpointer, plus the brief writer,
the grader, and the pure helpers (calculator, turn message, report).

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_system_design_agent -v
     (from the repo root with the workspace venv)
"""

import json
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from dispatcher.agents import system_design as sd
from langchain.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from shared.system_design.bank import (
    Clarification,
    InterviewBrief,
    RefComponent,
    RefConnection,
)
from shared.system_design.diagram import DiagramGraph, normalize_scene
from shared.system_design.rubric import DIMENSION_KEYS

from .test_agents import FakeChatModel, _patch_infra, ai, tc

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def brief(**over):
    base = {
        "title": "URL Shortener",
        "prompt": "Design a service that turns long links into short ones.",
        "clarifications": (Clarification("Scale", "100M new links a month"),),
        "functional_requirements": ("Create short links",),
        "non_functional_requirements": ("Redirects under 50 ms p99",),
        "estimation_notes": ("~40 writes/s average",),
        "reference_components": (
            RefComponent("client", "client", "Client", "Browsers"),
            RefComponent("api", "service", "Link Service", "Creates links"),
            RefComponent("kv", "database", "KV Store", "code -> url"),
        ),
        "reference_connections": (
            RefConnection("client", "api", "HTTPS"),
            RefConnection("api", "kv", "read/write"),
        ),
        "deep_dive_topics": ("Short code generation",),
        "pitfalls": ("Ignoring redirect caching",),
    }
    base.update(over)
    return InterviewBrief(**base)


def session(**over):
    base = {
        "id": "s1",
        "user_id": "u1",
        "source": "BANK",
        "problem_id": "url-shortener",
        "level": "SENIOR",
        "status": "PROCESSING",
        "phase": "REQUIREMENTS",
        "title": "URL Shortener",
        "prompt": "Design it.",
        "brief": brief().to_json(),
        "requirements": "",
        "estimates": "",
        "diagram": "[]",
        "phase_started_at": NOW - timedelta(minutes=3, seconds=20),
        "created_at": NOW - timedelta(minutes=14, seconds=5),
    }
    base.update(over)
    return sd.FetchSystemDesignSessionRow(**base)


def labelled(el_id, label):
    return [
        {"id": el_id, "type": "rectangle", "isDeleted": False},
        {"id": f"{el_id}-t", "type": "text", "text": label, "containerId": el_id},
    ]


def edge(el_id, start, end):
    return {
        "id": el_id,
        "type": "arrow",
        "startBinding": {"elementId": start},
        "endBinding": {"elementId": end},
        "endArrowhead": "arrow",
    }


SCENE = [
    *labelled("c", "Browser"),
    *labelled("s", "Link Service"),
    *labelled("d", "Postgres"),
    edge("e1", "c", "s"),
    edge("e2", "s", "d"),
]


def grade_args(**over):
    scores = [
        {"dimension": key, "score": 3, "evidence": f"e-{key}", "feedback": f"f-{key}"}
        for key in DIMENSION_KEYS
    ]
    base = {
        "scores": scores,
        "summary": "Solid.",
        "strengths": ["Clear API"],
        "improvements": ["Size the cache"],
        "study_topics": ["Consistent hashing"],
        "diagram_comments": [{"ref": "n2", "comment": "Single instance"}],
    }
    base.update(over)
    return {"grade": base}


def brief_args(**over):
    base = {
        "title": "Payout Ledger",
        "prompt": "Design the ledger behind merchant payouts.",
        "clarifications": [{"topic": "Scale", "answer": "5M payouts a day"}],
        "functional_requirements": ["Record payouts"],
        "non_functional_requirements": ["No lost writes"],
        "estimation_notes": ["~60 writes/s"],
        "reference_components": [
            {"id": "api", "kind": "service", "label": "Payout API", "purpose": "x"},
            {"id": "db", "kind": "database", "label": "Ledger DB", "purpose": "y"},
        ],
        "reference_connections": [{"source": "api", "target": "db", "label": "SQL"}],
        "deep_dive_topics": ["Idempotency"],
        "pitfalls": ["Floating point money"],
    }
    base.update(over)
    return {"brief": base}


class SafeEval(unittest.TestCase):
    def test_arithmetic(self):
        self.assertEqual(
            sd.safe_eval("100_000_000 / (30 * 86400)"), 100_000_000 / (30 * 86400)
        )
        self.assertEqual(sd.safe_eval("2 ** 10 + 3 % 2 - -1"), 1026)
        self.assertEqual(sd.safe_eval("1e6 * 500"), 5e8)
        self.assertEqual(sd.safe_eval("7 // 2"), 3)

    def test_rejects_anything_but_arithmetic(self):
        for expr in (
            "__import__('os')",
            "x + 1",
            "abs(-1)",
            "(1).real",
            "[1, 2]",
            "1 if 1 else 2",
            "",
            "1" * 300,
        ):
            with self.subTest(expr=expr), self.assertRaises(ValueError):
                sd.safe_eval(expr)

    def test_math_errors_are_value_errors(self):
        for expr in ("1 / 0", "10 ** 10 ** 10", "2 ** 5000.5"):
            with self.subTest(expr=expr), self.assertRaises(ValueError):
                sd.safe_eval(expr)


class Helpers(unittest.TestCase):
    def test_fmt_duration(self):
        self.assertEqual(sd.fmt_duration(45), "45s")
        self.assertEqual(sd.fmt_duration(365), "6m 05s")
        self.assertEqual(sd.fmt_duration(3720), "1h 02m")
        self.assertEqual(sd.fmt_duration(-5), "0s")

    def test_agent_context_round_trip_and_garbage(self):
        ctx = sd.AgentContext(
            requirements_hash="a", estimates_hash=None, graph={"nodes": []}
        )
        self.assertEqual(sd.AgentContext.from_json(ctx.to_json()), ctx)
        self.assertEqual(sd.AgentContext.from_json(None), sd.AgentContext())
        self.assertEqual(sd.AgentContext.from_json("{nope"), sd.AgentContext())
        self.assertEqual(sd.AgentContext.from_json('{"other": 1}'), sd.AgentContext())

    def test_opening_message_presents_the_problem(self):
        msg = sd.opening_message(brief())
        self.assertIn("URL Shortener", msg)
        self.assertIn("long links", msg)
        self.assertIn("requirements", msg.lower())

    def test_render_brief_includes_private_notes(self):
        text = sd.render_brief(brief())
        for needle in (
            "Scale: 100M new links a month",
            "Create short links",
            "Redirects under 50 ms p99",
            "~40 writes/s average",
            "Link Service",
            "Client -> Link Service (HTTPS)",
            "Short code generation",
            "Ignoring redirect caching",
        ):
            self.assertIn(needle, text)

    def test_interviewer_prompt_carries_level_and_brief(self):
        prompt = sd.interviewer_prompt(brief(), "STAFF")
        self.assertIn("Staff", prompt)
        self.assertIn("second-order", prompt)
        self.assertIn("Short code generation", prompt)


class BuildTurnMessage(unittest.TestCase):
    def test_header_has_phase_and_clock(self):
        msg, _ = sd.build_turn_message(
            session(), "message", "hi", sd.AgentContext(), NOW
        )
        self.assertIn("Phase: Requirements", msg)
        self.assertIn("3m 20s in this phase", msg)
        self.assertIn("target 6m 00s", msg)
        self.assertIn("14m 05s since the start", msg)

    def test_first_look_sends_notes_and_records_hashes(self):
        s = session(requirements="Shorten links\nRedirect fast")
        msg, ctx = sd.build_turn_message(
            s, "message", "How many users?", sd.AgentContext(), NOW
        )
        self.assertIn("Shorten links\nRedirect fast", msg)
        self.assertIn("How many users?", msg)
        self.assertEqual(
            ctx.requirements_hash, sd.text_hash("Shorten links\nRedirect fast")
        )

    def test_unchanged_notes_are_not_repeated(self):
        s = session(requirements="Shorten links")
        _, ctx = sd.build_turn_message(s, "message", "q1", sd.AgentContext(), NOW)
        msg, _ = sd.build_turn_message(s, "message", "q2", ctx, NOW)
        self.assertNotIn("Shorten links", msg)
        self.assertIn("unchanged", msg)

    def test_empty_diagram_is_left_out_before_the_design_phase(self):
        msg, _ = sd.build_turn_message(
            session(), "message", "hi", sd.AgentContext(), NOW
        )
        self.assertNotIn("Diagram", msg)

    def test_diagram_then_diff_then_unchanged(self):
        s = session(phase="HIGH_LEVEL_DESIGN", diagram=json.dumps(SCENE))
        first, ctx = sd.build_turn_message(s, "message", "ok", sd.AgentContext(), NOW)
        self.assertIn('"Link Service"', first)
        self.assertIn("->", first)
        self.assertIsNotNone(ctx.graph)

        again, ctx2 = sd.build_turn_message(s, "message", "ok", ctx, NOW)
        self.assertIn("Diagram: unchanged", again)

        changed = session(
            phase="HIGH_LEVEL_DESIGN",
            diagram=json.dumps([*SCENE, *labelled("r", "Redis"), edge("e3", "s", "r")]),
        )
        diff, _ = sd.build_turn_message(changed, "message", "ok", ctx2, NOW)
        self.assertIn('Added component "Redis"', diff)
        self.assertIn('Added connection "Link Service" -> "Redis"', diff)

    def test_advance_into_deep_dive_starts_it_with_observations(self):
        s = session(phase="DEEP_DIVE", diagram=json.dumps(SCENE))
        msg, _ = sd.build_turn_message(s, "advance", None, sd.AgentContext(), NOW)
        self.assertIn("submitted their high-level design", msg)
        self.assertIn("first question", msg)
        self.assertIn("No cache anywhere", msg)
        self.assertIn("(no message)", msg)

    def test_advance_mentions_the_phase_they_left(self):
        msg, _ = sd.build_turn_message(
            session(phase="ESTIMATION"),
            "advance",
            "Done with reqs",
            sd.AgentContext(),
            NOW,
        )
        self.assertIn("moved on from Requirements to Estimation", msg)
        self.assertIn("Done with reqs", msg)


class _GraphTest(unittest.TestCase):
    def setUp(self):
        self.saver = InMemorySaver()
        self.pg_patch, self.saver_patch = _patch_infra(sd, self.saver)
        self.pg_patch.start()
        self.saver_patch.start()
        self.addCleanup(self.pg_patch.stop)
        self.addCleanup(self.saver_patch.stop)

    def turn(self, script, text="How many users?", usage=None, new_messages="default"):
        model = FakeChatModel(script)
        if new_messages == "default":
            new_messages = [HumanMessage(content=text)]
        with patch.object(sd, "init_chat_model", return_value=model):
            outcome = sd.run_interview_turn(
                "s1",
                "openrouter:test/model",
                usage if usage is not None else sd.new_usage(),
                "SYSTEM PROMPT",
                new_messages,
                [
                    HumanMessage(content=sd.INTERVIEW_KICKOFF),
                    AIMessage(content="Opening"),
                ],
            )
        return outcome, model


class InterviewTurn(_GraphTest):
    def test_first_turn_seeds_the_opening_exchange(self):
        outcome, model = self.turn([ai("About 100M a month.")])
        self.assertEqual(outcome.reply, "About 100M a month.")
        self.assertFalse(outcome.interview_over)
        shown = model.calls[0]
        self.assertEqual(shown[0].content, "SYSTEM PROMPT")
        self.assertEqual(
            [m.content for m in shown[1:]],
            [sd.INTERVIEW_KICKOFF, "Opening", "How many users?"],
        )

    def test_later_turns_keep_history_without_reseeding(self):
        self.turn([ai("100M a month.")])
        _, model = self.turn([ai("Yes, custom aliases.")], text="Custom aliases?")
        contents = [m.content for m in model.calls[0][1:]]
        self.assertEqual(contents.count("Opening"), 1)
        self.assertEqual(contents[-1], "Custom aliases?")

    def test_calculate_tool_feeds_the_result_back(self):
        outcome, model = self.turn(
            [
                tc("calculate", {"expression": "100_000_000 / 2_592_000"}),
                ai("Looks right."),
            ]
        )
        self.assertEqual(outcome.reply, "Looks right.")
        tool_msg = model.calls[1][-1]
        self.assertEqual(tool_msg.type, "tool")
        self.assertIn("38.58", tool_msg.content)

    def test_calculate_reports_bad_expressions(self):
        _, model = self.turn([tc("calculate", {"expression": "import os"}), ai("ok")])
        self.assertIn("Could not evaluate", model.calls[1][-1].content)

    def test_end_interview_marks_the_interview_over(self):
        outcome, _ = self.turn(
            [tc("end_interview", {}), ai("Thanks, that's time.")],
            text="I think that's it.",
        )
        self.assertTrue(outcome.interview_over)
        self.assertEqual(outcome.reply, "Thanks, that's time.")

    def test_end_interview_only_counts_for_the_current_turn(self):
        self.turn([tc("end_interview", {}), ai("Thanks.")])
        outcome, _ = self.turn([ai("Sure.")], text="One more thing")
        self.assertFalse(outcome.interview_over)

    def test_empty_final_reply_gets_a_fallback(self):
        outcome, _ = self.turn([tc("end_interview", {}), ai("")])
        self.assertTrue(outcome.reply)

    def test_block_content_is_flattened(self):
        outcome, _ = self.turn(
            [
                AIMessage(
                    content=[
                        {"type": "text", "text": "Part one."},
                        {"type": "text", "text": "Part two."},
                    ]
                )
            ]
        )
        self.assertEqual(outcome.reply, "Part one.\nPart two.")

    def test_usage_accumulates_across_calls(self):
        usage = sd.new_usage()
        self.turn(
            [
                tc(
                    "calculate",
                    {"expression": "1+1"},
                    in_tok=7,
                    out_tok=3,
                    cost=0.002,
                    gen="g1",
                ),
                ai("ok", in_tok=11, out_tok=2, cost=0.001, gen="g2"),
            ],
            usage=usage,
        )
        self.assertEqual(usage["input_tokens"], 18)
        self.assertEqual(usage["output_tokens"], 5)
        self.assertAlmostEqual(usage["cost_usd"], 0.003)
        self.assertEqual(usage["generation_ids"], ["g1", "g2"])
        self.assertTrue(usage["all_costed"])

    def test_retry_resumes_a_crashed_turn(self):
        def boom():
            raise RuntimeError("provider down")

        with self.assertRaises(RuntimeError):
            self.turn([boom])
        outcome, model = self.turn([ai("Recovered answer.")], new_messages=None)
        self.assertEqual(outcome.reply, "Recovered answer.")
        # The retried call still sees the candidate's original message.
        self.assertEqual(model.calls[0][-1].content, "How many users?")

    def test_retry_with_nothing_pending_returns_the_last_reply(self):
        self.turn([ai("Already answered.")])
        outcome, model = self.turn([], new_messages=None)
        self.assertEqual(outcome.reply, "Already answered.")
        self.assertEqual(model.calls, [])


class GenerateBrief(unittest.TestCase):
    def run_brief(self, script):
        model = FakeChatModel(script)
        usage = sd.new_usage()
        with patch.object(sd, "init_chat_model", return_value=model):
            result = sd.generate_brief(
                "openrouter:test/model",
                usage,
                company_name="Stripe",
                role="Backend Engineer",
                job_description="Build payout systems in Go.",
                level="SENIOR",
            )
        return result, model, usage

    def test_submitted_brief_is_returned(self):
        result, model, usage = self.run_brief([tc("submit_brief", brief_args())])
        self.assertEqual(result.title, "Payout Ledger")
        self.assertEqual(result.reference_connections[0].target, "db")
        self.assertIn("Stripe", model.calls[0][-1].content)
        self.assertIn("Build payout systems in Go.", model.calls[0][-1].content)
        self.assertEqual(usage["input_tokens"], 10)

    def test_invalid_reference_design_is_sent_back(self):
        bad = brief_args(
            reference_connections=[{"source": "api", "target": "ghost", "label": ""}]
        )
        result, model, _ = self.run_brief(
            [tc("submit_brief", bad), tc("submit_brief", brief_args(), tc_id="tc-2")]
        )
        self.assertEqual(result.title, "Payout Ledger")
        self.assertIn("ghost", model.calls[1][-1].content)

    def test_a_reply_without_the_tool_is_nudged(self):
        result, model, _ = self.run_brief(
            [ai("Here you go!"), tc("submit_brief", brief_args())]
        )
        self.assertEqual(result.title, "Payout Ledger")
        self.assertIn("submit_brief", model.calls[1][-1].content)

    def test_gives_up_after_three_attempts(self):
        with self.assertRaises(sd.AgentError):
            self.run_brief([ai("no"), ai("no"), ai("no")])


class GradeInterview(unittest.TestCase):
    def grade(self, script, graph=None):
        model = FakeChatModel(script)
        with patch.object(sd, "init_chat_model", return_value=model):
            report = sd.grade_interview(
                "openrouter:test/model",
                sd.new_usage(),
                brief=brief(),
                level="SENIOR",
                transcript=[
                    sd.TranscriptRow(
                        role="INTERVIEWER", phase="REQUIREMENTS", content="Hi"
                    ),
                    sd.TranscriptRow(
                        role="CANDIDATE", phase="REQUIREMENTS", content="How big?"
                    ),
                ],
                requirements="Shorten links",
                estimates="40 writes/s",
                graph=graph if graph is not None else normalize_scene(SCENE),
                phase_durations={"REQUIREMENTS": 400, "ESTIMATION": 200},
            )
        return report, model

    def test_grade_is_derived_from_rubric_scores(self):
        report, model = self.grade([tc("submit_grade", grade_args())])
        self.assertEqual(report.letter_grade, "B")
        self.assertEqual(report.hire_signal, "HIRE")
        self.assertAlmostEqual(report.weighted_score, 3.0)
        prompt = model.calls[0][-1].content
        for needle in (
            "CANDIDATE [Requirements]: How big?",
            "Shorten links",
            "40 writes/s",
            'n2 "Link Service"',
            "Requirements: 6m 40s (target 6m 00s)",
            "Deep Dive: not reached",
        ):
            self.assertIn(needle, prompt)
        self.assertIn("Senior", model.calls[0][0].content)

    def test_missing_dimension_is_sent_back(self):
        partial = grade_args()
        partial["grade"]["scores"] = partial["grade"]["scores"][:-1]
        report, model = self.grade(
            [
                tc("submit_grade", partial),
                tc("submit_grade", grade_args(), tc_id="tc-2"),
            ]
        )
        self.assertEqual(report.letter_grade, "B")
        self.assertIn("time_management", model.calls[1][-1].content)

    def test_out_of_range_score_is_sent_back(self):
        bad = grade_args()
        bad["grade"]["scores"][0]["score"] = 9
        report, _model = self.grade(
            [tc("submit_grade", bad), tc("submit_grade", grade_args(), tc_id="tc-2")]
        )
        self.assertEqual(report.hire_signal, "HIRE")


class BuildReport(unittest.TestCase):
    def submission(self, **over):
        return sd.GradeSubmission.model_validate(grade_args(**over)["grade"])

    def test_dimensions_follow_rubric_order_with_labels_and_weights(self):
        sub = self.submission()
        sub.scores.reverse()
        report = sd.build_report(
            sub, "MID", normalize_scene(SCENE), {"REQUIREMENTS": 60}
        )
        self.assertEqual([d["key"] for d in report.dimensions], list(DIMENSION_KEYS))
        self.assertEqual(report.dimensions[0]["label"], "Requirements")
        self.assertEqual(report.dimensions[0]["weight"], 0.15)
        self.assertEqual(report.level, "MID")
        self.assertEqual(report.phase_durations, {"REQUIREMENTS": 60})

    def test_diagram_comment_refs_resolve_to_elements(self):
        sub = self.submission(
            diagram_comments=[
                {"ref": "n2", "comment": "Single instance"},
                {"ref": "n9", "comment": "Unknown"},
            ]
        )
        report = sd.build_report(sub, "SENIOR", normalize_scene(SCENE), {})
        self.assertEqual(
            report.diagram_comments,
            [
                {
                    "ref": "n2",
                    "element_id": "s",
                    "label": "Link Service",
                    "comment": "Single instance",
                }
            ],
        )

    def test_report_serializes(self):
        report = sd.build_report(self.submission(), "SENIOR", DiagramGraph(), {})
        data = json.loads(report.to_json())
        self.assertEqual(data["letter_grade"], "B")
        self.assertEqual(data["diagram_comments"], [])


if __name__ == "__main__":
    unittest.main()

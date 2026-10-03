"""System design db_ops — real SQL against a live Postgres (TEST_PG_URL,
default the compose creds' resland_test database). Skips cleanly when no
database is reachable; refuses to truncate anything but a scratch database.

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_system_design_db_ops_pg -v
     (from the repo root with the workspace venv)
"""

import json
import os
import unittest

import psycopg
from dispatcher.agents.system_design import GradeReport
from dispatcher.runners import db_ops
from shared.testing import destructive_db_ok

TEST_PG_URL = os.getenv(
    "TEST_PG_URL", "postgres://resland:resland@localhost:5432/resland_test"
)

_DESTRUCTIVE_OK, _DESTRUCTIVE_REASON = destructive_db_ok(TEST_PG_URL)


def _pg_reachable() -> bool:
    try:
        conn = psycopg.connect(TEST_PG_URL, connect_timeout=3, autocommit=True)
    except Exception:
        return False
    conn.close()
    return True


@unittest.skipUnless(_pg_reachable(), f"needs Postgres at {TEST_PG_URL}")
class SystemDesignDbOps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = psycopg.connect(TEST_PG_URL, autocommit=True)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def setUp(self):
        if not _DESTRUCTIVE_OK:
            self.skipTest(_DESTRUCTIVE_REASON)
        self.conn.execute(
            "TRUNCATE system_design_message, user_system_design_session,"
            ' token_usage, "user" CASCADE'
        )
        self.conn.execute('INSERT INTO "user" (auth0_id) VALUES (%s)', ("u1",))

    def _session(
        self,
        sid="s1",
        phase="REQUIREMENTS",
        status="PROCESSING",
        started_ago="5 minutes",
    ):
        self.conn.execute(
            "INSERT INTO user_system_design_session"
            " (id, user_id, source, problem_id, phase, status, phase_started_at)"
            " VALUES (%s, 'u1', 'BANK', 'url-shortener', %s, %s, now() - %s::interval)",
            (sid, phase, status, started_ago),
        )

    def _get(self, sid="s1"):
        cur = self.conn.execute(
            "SELECT * FROM user_system_design_session WHERE id = %s", (sid,)
        )
        cols = [c.name for c in cur.description]
        return dict(zip(cols, cur.fetchone()))

    def _messages(self, sid="s1"):
        return self.conn.execute(
            "SELECT role, phase, content FROM system_design_message"
            " WHERE session_id = %s ORDER BY id",
            (sid,),
        ).fetchall()

    def test_fetch_session(self):
        self._session()
        row = db_ops.fetch_system_design_session(self.conn, "s1")
        self.assertEqual(row.id, "s1")
        self.assertEqual(row.level, "SENIOR")
        self.assertEqual(row.diagram, "[]")
        self.assertEqual(row.phase_durations, "{}")
        self.assertIsNone(row.brief)

    def test_fetch_missing_session_is_none(self):
        self.assertIsNone(db_ops.fetch_system_design_session(self.conn, "nope"))

    def test_start_stores_problem_and_opening(self):
        self._session()
        db_ops.start_system_design_session(
            self.conn,
            "s1",
            title="URL Shortener",
            prompt="Design it.",
            brief_json='{"title": "URL Shortener"}',
            opening="Hi there.",
            turn_id="t0",
        )
        row = self._get()
        self.assertEqual(row["title"], "URL Shortener")
        self.assertEqual(row["prompt"], "Design it.")
        self.assertEqual(json.loads(row["brief"]), {"title": "URL Shortener"})
        self.assertEqual(row["status"], "WAITING_FOR_INPUT")
        self.assertEqual(row["last_turn_id"], "t0")
        self.assertEqual(
            self._messages(), [("INTERVIEWER", "REQUIREMENTS", "Hi there.")]
        )

    def test_save_turn_hands_the_turn_back(self):
        self._session(phase="ESTIMATION")
        self.conn.execute(
            "UPDATE user_system_design_session SET notice = 'oops' WHERE id = 's1'"
        )
        db_ops.save_system_design_turn(
            self.conn,
            "s1",
            reply="Looks right.",
            phase="ESTIMATION",
            agent_context='{"graph": null}',
            interview_over=False,
            turn_id="t1",
        )
        row = self._get()
        self.assertEqual(row["status"], "WAITING_FOR_INPUT")
        self.assertEqual(row["phase"], "ESTIMATION")
        self.assertEqual(row["agent_context"], '{"graph": null}')
        self.assertEqual(row["last_turn_id"], "t1")
        self.assertIsNone(row["notice"])
        self.assertEqual(
            self._messages(), [("INTERVIEWER", "ESTIMATION", "Looks right.")]
        )

    def test_save_turn_that_ends_the_interview_moves_to_feedback(self):
        self._session(phase="DEEP_DIVE", started_ago="10 minutes")
        db_ops.save_system_design_turn(
            self.conn,
            "s1",
            reply="Thanks, that's time.",
            phase="DEEP_DIVE",
            agent_context="{}",
            interview_over=True,
            turn_id=None,
        )
        row = self._get()
        self.assertEqual(row["phase"], "FEEDBACK")
        self.assertEqual(row["status"], "PROCESSING")
        self.assertIsNone(row["last_turn_id"])
        durations = json.loads(row["phase_durations"])
        self.assertAlmostEqual(durations["DEEP_DIVE"], 600, delta=5)
        self.assertEqual(self._messages()[0][1], "DEEP_DIVE")

    def test_complete_writes_the_report(self):
        self._session(phase="FEEDBACK")
        report = GradeReport(
            letter_grade="A-",
            hire_signal="HIRE",
            weighted_score=3.7,
            level="SENIOR",
            dimensions=[],
            summary="Good",
            strengths=[],
            improvements=[],
            study_topics=[],
        )
        db_ops.complete_system_design_session(self.conn, "s1", report, "t9")
        row = self._get()
        self.assertEqual(row["status"], "COMPLETED")
        self.assertEqual(row["letter_grade"], "A-")
        self.assertEqual(row["hire_signal"], "HIRE")
        self.assertEqual(json.loads(row["result"])["summary"], "Good")
        self.assertIsNotNone(row["completed_at"])
        self.assertEqual(row["last_turn_id"], "t9")

    def test_complete_drops_the_interviewer_thread(self):
        from langgraph.checkpoint.postgres import PostgresSaver

        PostgresSaver(self.conn).setup()
        self._session(phase="FEEDBACK")
        for sid in ("s1", "other"):
            self.conn.execute(
                "INSERT INTO checkpoints (thread_id, checkpoint_ns, checkpoint_id,"
                " checkpoint, metadata) VALUES (%s, '', 'c1', '{}', '{}')",
                (sid,),
            )
        report = GradeReport(
            letter_grade="B",
            hire_signal="HIRE",
            weighted_score=3.0,
            level="SENIOR",
            dimensions=[],
            summary="",
            strengths=[],
            improvements=[],
            study_topics=[],
        )
        db_ops.complete_system_design_session(self.conn, "s1", report, None)
        threads = self.conn.execute(
            "SELECT thread_id FROM checkpoints WHERE thread_id IN ('s1', 'other')"
        ).fetchall()
        self.assertEqual(threads, [("other",)])
        self.conn.execute("DELETE FROM checkpoints WHERE thread_id = 'other'")

    def test_notice_hands_back_a_retry(self):
        self._session()
        db_ops.set_system_design_notice(self.conn, "s1", "Retry please")
        row = self._get()
        self.assertEqual(row["status"], "WAITING_FOR_INPUT")
        self.assertEqual(row["notice"], "Retry please")

    def test_failed_spares_resumable_and_finished_sessions(self):
        self._session("a", status="PROCESSING")
        self._session("b", status="WAITING_FOR_INPUT")
        self._session("c", status="COMPLETED")
        for sid in ("a", "b", "c"):
            db_ops.set_system_design_failed(self.conn, sid)
        self.assertEqual(self._get("a")["status"], "FAILED")
        self.assertEqual(self._get("b")["status"], "WAITING_FOR_INPUT")
        self.assertEqual(self._get("c")["status"], "COMPLETED")

    def test_transcript_in_order(self):
        self._session()
        for role, content in (
            ("INTERVIEWER", "Hi"),
            ("CANDIDATE", "Hello"),
            ("INTERVIEWER", "Go"),
        ):
            self.conn.execute(
                "INSERT INTO system_design_message (session_id, role, phase, content)"
                " VALUES ('s1', %s, 'REQUIREMENTS', %s)",
                (role, content),
            )
        rows = db_ops.fetch_system_design_transcript(self.conn, "s1")
        self.assertEqual([r.content for r in rows], ["Hi", "Hello", "Go"])
        self.assertEqual(rows[1].role, "CANDIDATE")


if __name__ == "__main__":
    unittest.main()

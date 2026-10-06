"""Checkpointer table setup — real DDL against a live Postgres (TEST_PG_URL,
default the compose creds' resland_test database). Skips cleanly when no
database is reachable; refuses to drop anything but a scratch database.

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_pg_setup_pg -v
     (from the repo root with the workspace venv)
"""

import os
import unittest

import psycopg
from dispatcher import pg as pg_module
from langgraph.checkpoint.postgres import PostgresSaver
from shared.checkpoints import CHECKPOINT_SCHEMA, CHECKPOINTER_TABLES
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


def _insert_checkpoint(conn, table, thread_id):
    conn.execute(
        f"INSERT INTO {table} (thread_id, checkpoint_ns, checkpoint_id,"
        " checkpoint, metadata) VALUES (%s, '', 'c1', '{}', '{}')",
        (thread_id,),
    )


@unittest.skipUnless(_pg_reachable(), f"needs Postgres at {TEST_PG_URL}")
class CheckpointerSetup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = psycopg.connect(TEST_PG_URL, autocommit=True)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def setUp(self):
        if not _DESTRUCTIVE_OK:
            self.skipTest(_DESTRUCTIVE_REASON)
        self._drop_all()
        # Leave the database set up for the suites that write checkpoints.
        self.addCleanup(pg_module.do_pg_setup, TEST_PG_URL)
        self.addCleanup(self._drop_all)

    def _drop_all(self):
        self.conn.execute(f"DROP SCHEMA IF EXISTS {CHECKPOINT_SCHEMA} CASCADE")
        for table in CHECKPOINTER_TABLES:
            self.conn.execute(f"DROP TABLE IF EXISTS public.{table}")

    def _tables_in(self, schema):
        rows = self.conn.execute(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema = %s AND table_name = ANY(%s)",
            (schema, list(CHECKPOINTER_TABLES)),
        ).fetchall()
        return sorted(r[0] for r in rows)

    def _legacy_setup(self):
        """What a dispatcher from before the schema did: PostgresSaver on a
        plain connection, so its tables land in `public`."""
        PostgresSaver(self.conn).setup()
        _insert_checkpoint(self.conn, "public.checkpoints", "t1")

    def test_fresh_database_gets_its_tables_in_the_schema(self):
        pg_module.do_pg_setup(TEST_PG_URL)
        self.assertEqual(
            self._tables_in(CHECKPOINT_SCHEMA), sorted(CHECKPOINTER_TABLES)
        )
        self.assertEqual(self._tables_in("public"), [])

    def test_legacy_public_tables_move_with_their_rows(self):
        self._legacy_setup()
        moved = pg_module.move_checkpoint_tables(self.conn)
        self.assertEqual(sorted(moved), sorted(CHECKPOINTER_TABLES))
        self.assertEqual(self._tables_in("public"), [])
        threads = self.conn.execute(
            f"SELECT thread_id FROM {CHECKPOINT_SCHEMA}.checkpoints"
        ).fetchall()
        self.assertEqual(threads, [("t1",)])

    def test_setup_after_the_move_keeps_the_migration_history(self):
        self._legacy_setup()
        before = self.conn.execute(
            "SELECT count(*) FROM public.checkpoint_migrations"
        ).fetchone()
        pg_module.do_pg_setup(TEST_PG_URL)
        after = self.conn.execute(
            f"SELECT count(*) FROM {CHECKPOINT_SCHEMA}.checkpoint_migrations"
        ).fetchone()
        self.assertEqual(after, before)
        self.assertEqual(self._tables_in("public"), [])

    def test_rerun_moves_nothing(self):
        self._legacy_setup()
        pg_module.move_checkpoint_tables(self.conn)
        self.assertEqual(pg_module.move_checkpoint_tables(self.conn), [])

    def test_never_replaces_a_table_already_in_the_schema(self):
        pg_module.do_pg_setup(TEST_PG_URL)
        _insert_checkpoint(self.conn, f"{CHECKPOINT_SCHEMA}.checkpoints", "kept")
        self._legacy_setup()
        self.assertEqual(pg_module.move_checkpoint_tables(self.conn), [])
        threads = self.conn.execute(
            f"SELECT thread_id FROM {CHECKPOINT_SCHEMA}.checkpoints"
        ).fetchall()
        self.assertEqual(threads, [("kept",)])


if __name__ == "__main__":
    unittest.main()

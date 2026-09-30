"""Unit tests for the destructive-fixture guard in shared.testing."""

import os
import unittest
from unittest import mock

from shared.testing import destructive_db_ok, pg_database_name

SCRATCH = "postgres://resland:resland@localhost:5432/resland_test"
DEV = "postgres://resland:resland@localhost:5432/resland"


class PgDatabaseNameTest(unittest.TestCase):
    def test_extracts_name(self):
        self.assertEqual(pg_database_name(SCRATCH), "resland_test")

    def test_handles_encoded_name(self):
        self.assertEqual(
            pg_database_name("postgres://u:p@h:5432/my%20db"), "my db"
        )

    def test_no_path_is_empty(self):
        self.assertEqual(pg_database_name("postgres://u:p@h:5432"), "")


class DestructiveDbOkTest(unittest.TestCase):
    def setUp(self):
        # Never let an ambient opt-in mask the guard's default behaviour.
        patcher = mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        os.environ.pop("ALLOW_DESTRUCTIVE_TESTS", None)
        self.addCleanup(patcher.stop)

    def test_allows_test_database(self):
        allowed, reason = destructive_db_ok(SCRATCH)
        self.assertTrue(allowed)
        self.assertIn("resland_test", reason)

    def test_refuses_dev_database(self):
        allowed, reason = destructive_db_ok(DEV)
        self.assertFalse(allowed)
        self.assertIn("resland", reason)
        self.assertIn("ALLOW_DESTRUCTIVE_TESTS=1", reason)

    def test_refuses_when_name_is_unknown(self):
        allowed, reason = destructive_db_ok("postgres://u:p@h:5432")
        self.assertFalse(allowed)
        self.assertIn("cannot determine", reason)

    def test_opt_in_overrides(self):
        with mock.patch.dict(os.environ, {"ALLOW_DESTRUCTIVE_TESTS": "1"}):
            allowed, reason = destructive_db_ok(DEV)
        self.assertTrue(allowed)
        self.assertIn("opt-in", reason)

    def test_opt_in_must_be_exactly_one(self):
        with mock.patch.dict(os.environ, {"ALLOW_DESTRUCTIVE_TESTS": "true"}):
            allowed, _ = destructive_db_ok(DEV)
        self.assertFalse(allowed)


if __name__ == "__main__":
    unittest.main()

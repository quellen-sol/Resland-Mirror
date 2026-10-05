"""get_pg_client tests — stdlib unittest, no database.

Run: .venv/bin/python -m unittest backend.shared.tests.test_pg -v
"""

import unittest
from unittest.mock import patch

from shared.checkpoints import CHECKPOINT_CONN_OPTIONS
from shared.pg import get_pg_client


class GetPgClient(unittest.TestCase):
    def test_forwards_url_and_defaults(self):
        with patch("shared.pg.psycopg.connect") as connect:
            get_pg_client("postgres://x")
        connect.assert_called_once_with(
            "postgres://x", autocommit=True, row_factory=None, options=None
        )

    def test_forwards_overrides(self):
        marker = object()
        with patch("shared.pg.psycopg.connect") as connect:
            get_pg_client("postgres://x", autocommit=False, row_factory=marker)
        connect.assert_called_once_with(
            "postgres://x", autocommit=False, row_factory=marker, options=None
        )

    def test_forwards_startup_options(self):
        with patch("shared.pg.psycopg.connect") as connect:
            get_pg_client("postgres://x", options=CHECKPOINT_CONN_OPTIONS)
        self.assertEqual(
            connect.call_args.kwargs["options"], "-c search_path=langgraph"
        )


if __name__ == "__main__":
    unittest.main()

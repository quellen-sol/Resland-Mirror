"""Process entrypoints — dispatcher.async_main's consumer wiring and the
module-level Postgres checkpointer setup in dispatcher.pg.

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_entrypoints -v
"""

import importlib
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import dispatcher
from shared.amqp import (
    BULLET_SUGG_QUEUE_NAME,
    RESUME_QUEUE_NAME,
    TAILOR_QUEUE_NAME,
    AddressHelper,
)

from dispatcher.handlers.resume_handler import ResumeHandler
from dispatcher.handlers.suggestion_handler import SuggestionHandler
from dispatcher.handlers.tailor_handler import TailorHandler


class AsyncMain(unittest.IsolatedAsyncioTestCase):
    async def test_dials_three_consumers_with_their_handlers(self):
        consumers = []

        class _Consumer:
            def __init__(self, destination, handler):
                self.destination = destination
                self.handler = handler
                self.ran = False

            async def run(self):
                self.ran = True

        conn = MagicMock()
        conn.dial = AsyncMock()

        async def _consumer(destination, message_handler):
            c = _Consumer(destination, message_handler)
            consumers.append(c)
            return c

        conn.consumer = _consumer
        env = MagicMock()
        env.connection = AsyncMock(return_value=conn)

        with patch.object(dispatcher, "AsyncEnvironment", return_value=env):
            await dispatcher.async_main()

        self.assertEqual(conn.dial.await_count, 3)
        self.assertEqual(
            [c.destination for c in consumers],
            [
                AddressHelper.queue_address(RESUME_QUEUE_NAME),
                AddressHelper.queue_address(BULLET_SUGG_QUEUE_NAME),
                AddressHelper.queue_address(TAILOR_QUEUE_NAME),
            ],
        )
        self.assertIsInstance(consumers[0].handler, ResumeHandler)
        self.assertIsInstance(consumers[1].handler, SuggestionHandler)
        self.assertIsInstance(consumers[2].handler, TailorHandler)
        self.assertTrue(all(c.ran for c in consumers))


class PgModule(unittest.TestCase):
    def test_import_sets_up_checkpointer(self):
        conn = MagicMock()
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=conn)
        cm.__exit__ = MagicMock(return_value=False)
        saver = MagicMock()
        sys.modules.pop("dispatcher.pg", None)
        try:
            with (
                patch("psycopg.connect", return_value=cm) as connect,
                patch(
                    "langgraph.checkpoint.postgres.PostgresSaver",
                    return_value=saver,
                ) as saver_cls,
            ):
                importlib.import_module("dispatcher.pg")
        finally:
            sys.modules.pop("dispatcher.pg", None)
        connect.assert_called_once_with(
            conninfo=dispatcher.env_vars.PG_URL, autocommit=True
        )
        saver_cls.assert_called_once_with(conn)
        saver.setup.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()

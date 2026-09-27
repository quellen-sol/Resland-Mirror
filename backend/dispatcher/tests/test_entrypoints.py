"""Process entrypoints — dispatcher.async_main's consumer wiring and the
Postgres checkpointer table setup in dispatcher.pg.do_pg_setup.

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_entrypoints -v
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import dispatcher
from dispatcher import pg as pg_module
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

        calls = []
        conn = MagicMock()
        conn.dial = AsyncMock(side_effect=lambda: calls.append("dial"))

        async def _consumer(destination, message_handler):
            c = _Consumer(destination, message_handler)
            consumers.append(c)
            return c

        conn.consumer = _consumer
        env = MagicMock()
        env.connection = AsyncMock(return_value=conn)

        with (
            patch.object(dispatcher, "AsyncEnvironment", return_value=env),
            patch.object(
                dispatcher,
                "do_pg_setup",
                side_effect=lambda: calls.append("pg_setup"),
            ) as pg_setup,
        ):
            await dispatcher.async_main()

        pg_setup.assert_called_once_with()
        self.assertEqual(calls[0], "pg_setup")
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


class PgSetup(unittest.TestCase):
    def test_do_pg_setup_creates_checkpointer_tables(self):
        conn = MagicMock()
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=conn)
        cm.__exit__ = MagicMock(return_value=False)
        saver = MagicMock()
        with (
            patch("psycopg.connect", return_value=cm) as connect,
            patch.object(
                pg_module, "PostgresSaver", return_value=saver
            ) as saver_cls,
        ):
            pg_module.do_pg_setup()
        connect.assert_called_once_with(
            conninfo=pg_module.PG_URL, autocommit=True
        )
        saver_cls.assert_called_once_with(conn)
        saver.setup.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()

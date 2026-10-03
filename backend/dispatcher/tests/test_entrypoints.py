"""Process entrypoints — dispatcher.async_main's consumer wiring and the
Postgres checkpointer table setup in dispatcher.pg.do_pg_setup.

Run: .venv/bin/python -m unittest backend.dispatcher.tests.test_entrypoints -v
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import dispatcher
from dispatcher import pg as pg_module
from dispatcher.handlers.resume_handler import ResumeHandler
from dispatcher.handlers.suggestion_handler import SuggestionHandler
from dispatcher.handlers.tailor_handler import TailorHandler
from shared.amqp import (
    BULLET_SUGG_QUEUE_NAME,
    RESUME_QUEUE_NAME,
    TAILOR_QUEUE_NAME,
)


class AsyncMain(unittest.IsolatedAsyncioTestCase):
    async def test_consumes_three_queues_with_their_handlers(self):
        calls = []
        client = MagicMock()
        client.setup = AsyncMock(side_effect=lambda: calls.append("setup"))
        client.consume = AsyncMock()
        client.close = AsyncMock()

        stop = asyncio.Event()
        stop.set()

        with (
            patch.object(dispatcher, "AmqpClient", return_value=client),
            patch.object(
                dispatcher,
                "do_pg_setup",
                side_effect=lambda: calls.append("pg_setup"),
            ) as pg_setup,
        ):
            await dispatcher.async_main(stop_event=stop)

        pg_setup.assert_called_once_with()
        # Postgres tables must exist before the AMQP work starts
        self.assertEqual(calls[0], "pg_setup")
        client.setup.assert_awaited_once()
        self.assertEqual(
            [c.args[0] for c in client.consume.await_args_list],
            [RESUME_QUEUE_NAME, BULLET_SUGG_QUEUE_NAME, TAILOR_QUEUE_NAME],
        )
        handlers = [c.args[1].__self__ for c in client.consume.await_args_list]
        self.assertIsInstance(handlers[0], ResumeHandler)
        self.assertIsInstance(handlers[1], SuggestionHandler)
        self.assertIsInstance(handlers[2], TailorHandler)
        client.close.assert_awaited_once()


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

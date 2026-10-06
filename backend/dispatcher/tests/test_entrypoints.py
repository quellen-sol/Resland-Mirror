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
from dispatcher.handlers.system_design_handler import SystemDesignHandler
from dispatcher.handlers.tailor_handler import TailorHandler
from shared.amqp import (
    BULLET_SUGG_QUEUE_NAME,
    RESUME_QUEUE_NAME,
    SYSTEM_DESIGN_QUEUE_NAME,
    TAILOR_QUEUE_NAME,
)
from shared.checkpoints import CHECKPOINT_CONN_OPTIONS


class AsyncMain(unittest.IsolatedAsyncioTestCase):
    async def test_consumes_every_queue_with_its_handler(self):
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
            [
                RESUME_QUEUE_NAME,
                BULLET_SUGG_QUEUE_NAME,
                TAILOR_QUEUE_NAME,
                SYSTEM_DESIGN_QUEUE_NAME,
            ],
        )
        handlers = [c.args[1].__self__ for c in client.consume.await_args_list]
        self.assertIsInstance(handlers[0], ResumeHandler)
        self.assertIsInstance(handlers[1], SuggestionHandler)
        self.assertIsInstance(handlers[2], TailorHandler)
        self.assertIsInstance(handlers[3], SystemDesignHandler)
        client.close.assert_awaited_once()


def _conn_cm(conn):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=conn)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


class PgSetup(unittest.TestCase):
    def test_do_pg_setup_creates_checkpointer_tables_in_their_schema(self):
        plain, scoped = MagicMock(), MagicMock()
        saver = MagicMock()
        with (
            patch(
                "psycopg.connect", side_effect=[_conn_cm(plain), _conn_cm(scoped)]
            ) as connect,
            patch.object(
                pg_module, "move_checkpoint_tables", return_value=[]
            ) as move,
            patch.object(
                pg_module, "PostgresSaver", return_value=saver
            ) as saver_cls,
        ):
            pg_module.do_pg_setup()
        # The schema (and any legacy tables) first, then PostgresSaver on a
        # connection whose search_path lands its tables in that schema.
        move.assert_called_once_with(plain)
        self.assertEqual(
            connect.call_args_list[1].kwargs,
            {
                "conninfo": pg_module.PG_URL,
                "autocommit": True,
                "options": CHECKPOINT_CONN_OPTIONS,
            },
        )
        saver_cls.assert_called_once_with(scoped)
        saver.setup.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()

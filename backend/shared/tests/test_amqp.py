"""AMQP job serialization + AmqpClient tests — stdlib unittest, no broker.

The client's connection/environment and everything returned by it are mocked;
what's exercised is our own logic: publisher caching, reconnect-once retry,
topology declaration order, and the not-connected guards.

Run: .venv/bin/python -m unittest backend.shared.tests.test_amqp -v
     (from the repo root with the workspace venv)
"""

import json
import unittest
from unittest.mock import AsyncMock, MagicMock

from rabbitmq_amqp_python_client import ConnectionClosed

from shared.amqp import (
    AmqpClient,
    AmqpClientException,
    AmqpResumeJob,
    AmqpSuggestionJob,
    AmqpTailorJob,
    BULLET_SUGG_DLQ_NAME,
    BULLET_SUGG_DLX_NAME,
    BULLET_SUGG_EXCHANGE_NAME,
    BULLET_SUGG_QUEUE_NAME,
    RESUME_DLQ_NAME,
    RESUME_DLX_NAME,
    RESUME_EXCHANGE_NAME,
    RESUME_QUEUE_NAME,
    TAILOR_DLQ_NAME,
    TAILOR_DLX_NAME,
    TAILOR_EXCHANGE_NAME,
    TAILOR_QUEUE_NAME,
)


class JobSerialization(unittest.TestCase):
    def test_resume_job_bytes(self):
        job = AmqpResumeJob(s3_key="k1", job_id="j1", user_id="u1")
        payload = json.loads(job.to_bytes())
        self.assertEqual(
            payload,
            {
                "s3_key": "k1",
                "job_id": "j1",
                "user_id": "u1",
                "job_type": "resume",
            },
        )

    def test_suggestion_job_defaults(self):
        job = AmqpSuggestionJob(session_id="s1")
        payload = json.loads(job.to_bytes())
        self.assertEqual(payload["session_id"], "s1")
        self.assertIsNone(payload["answer"])
        self.assertEqual(payload["job_type"], "suggestion")

    def test_suggestion_job_with_answer(self):
        job = AmqpSuggestionJob(session_id="s1", answer="team of 5")
        payload = json.loads(job.to_bytes())
        self.assertEqual(payload["answer"], "team of 5")

    def test_tailor_job(self):
        job = AmqpTailorJob(run_id="r1", answer="include a summary")
        payload = json.loads(job.to_bytes())
        self.assertEqual(payload["run_id"], "r1")
        self.assertEqual(payload["answer"], "include a summary")
        self.assertEqual(payload["job_type"], "tailor")

    def test_to_message_wraps_bytes(self):
        job = AmqpResumeJob(s3_key="k", job_id="j", user_id="u")
        msg = job.to_message()
        self.assertEqual(bytes(msg.body), job.to_bytes())


def _client() -> AmqpClient:
    """Client with a stubbed-out async environment."""
    client = AmqpClient.__new__(AmqpClient)
    client.async_env = MagicMock()
    client.amqp_connection = None
    client._publishers = {}
    return client


class AmqpClientConnect(unittest.IsolatedAsyncioTestCase):
    async def test_connect_dials_and_clears_publishers(self):
        client = _client()
        conn = AsyncMock()
        client.async_env.connection = AsyncMock(return_value=conn)
        client._publishers["stale"] = MagicMock()

        await client.connect()
        conn.dial.assert_awaited_once()
        self.assertIs(client.amqp_connection, conn)
        self.assertEqual(client._publishers, {})

    async def test_connect_failure_raises_client_exception(self):
        client = _client()
        client.async_env.connection = AsyncMock(side_effect=ValueError("down"))
        with self.assertRaises(AmqpClientException):
            await client.connect()

    async def test_setup_without_topology_just_connects(self):
        client = _client()
        conn = AsyncMock()
        client.async_env.connection = AsyncMock(return_value=conn)
        await client.setup(declare_topology=False)
        conn.dial.assert_awaited_once()
        conn.management.assert_not_called()

    async def test_close_idempotent(self):
        client = _client()
        await client.close()  # never connected — no-op
        conn = AsyncMock()
        client.amqp_connection = conn
        await client.close()
        conn.close.assert_awaited_once()
        self.assertIsNone(client.amqp_connection)
        await client.close()  # closing twice is fine


class AmqpClientAccessors(unittest.IsolatedAsyncioTestCase):
    async def test_publisher_requires_connection(self):
        client = _client()
        with self.assertRaises(AmqpClientException):
            await client.get_publisher("x")
        with self.assertRaises(AmqpClientException):
            await client.get_consumer("q", MagicMock())
        with self.assertRaises(AmqpClientException):
            await client.get_manager()

    async def test_publisher_cached_per_address(self):
        client = _client()
        conn = AsyncMock()
        pub = MagicMock()
        conn.publisher = AsyncMock(return_value=pub)
        client.amqp_connection = conn

        first = await client.get_publisher(RESUME_EXCHANGE_NAME)
        second = await client.get_publisher(RESUME_EXCHANGE_NAME)
        self.assertIs(first, pub)
        self.assertIs(second, pub)
        # Same address → same link — the broker kills duplicate link names.
        conn.publisher.assert_awaited_once()

        # A different exchange is a different link.
        conn.publisher = AsyncMock(return_value=MagicMock())
        await client.get_publisher(TAILOR_EXCHANGE_NAME)
        conn.publisher.assert_awaited_once()

    async def test_publisher_reconnects_once_on_closed_connection(self):
        client = _client()
        stale_conn = AsyncMock()
        fresh_conn = AsyncMock()
        fresh_pub = MagicMock()

        stale_conn.publisher = AsyncMock(
            side_effect=ConnectionClosed(MagicMock())
        )
        client.amqp_connection = stale_conn
        client.async_env.connection = AsyncMock(return_value=fresh_conn)
        fresh_conn.publisher = AsyncMock(return_value=fresh_pub)

        pub = await client.get_publisher(RESUME_EXCHANGE_NAME)
        self.assertIs(pub, fresh_pub)
        stale_conn.close.assert_awaited_once()
        fresh_conn.dial.assert_awaited_once()

    async def test_consumer_and_manager_pass_through(self):
        client = _client()
        conn = AsyncMock()
        client.amqp_connection = conn
        await client.get_consumer("q1", MagicMock())
        conn.consumer.assert_awaited_once()
        await client.get_manager()
        conn.management.assert_awaited_once()


class DeclareTopology(unittest.IsolatedAsyncioTestCase):
    async def test_declares_everything(self):
        client = _client()
        conn = AsyncMock()
        manager = AsyncMock()
        conn.management = AsyncMock(return_value=manager)
        client.amqp_connection = conn

        await client.declare_topology()

        exchanges = {
            c.args[0].name for c in manager.declare_exchange.await_args_list
        }
        self.assertEqual(
            exchanges,
            {
                RESUME_DLX_NAME,
                RESUME_EXCHANGE_NAME,
                BULLET_SUGG_EXCHANGE_NAME,
                BULLET_SUGG_DLX_NAME,
                TAILOR_EXCHANGE_NAME,
                TAILOR_DLX_NAME,
            },
        )
        queues = {c.args[0].name for c in manager.declare_queue.await_args_list}
        self.assertEqual(
            queues,
            {
                RESUME_DLQ_NAME,
                RESUME_QUEUE_NAME,
                BULLET_SUGG_QUEUE_NAME,
                BULLET_SUGG_DLQ_NAME,
                TAILOR_QUEUE_NAME,
                TAILOR_DLQ_NAME,
            },
        )
        # Every exchange ends up bound to a queue.
        bound_pairs = {
            (c.args[0].source_exchange, c.args[0].destination_queue)
            for c in manager.bind.await_args_list
        }
        self.assertEqual(len(bound_pairs), 6)

        # The work queues dead-letter into their DLX; the DLQs don't.
        queue_specs = {
            c.args[0].name: c.args[0]
            for c in manager.declare_queue.await_args_list
        }
        self.assertEqual(
            queue_specs[RESUME_QUEUE_NAME].dead_letter_exchange, RESUME_DLX_NAME
        )
        self.assertIsNone(
            getattr(
                queue_specs[RESUME_DLQ_NAME], "dead_letter_exchange", None
            )
        )


if __name__ == "__main__":
    unittest.main()

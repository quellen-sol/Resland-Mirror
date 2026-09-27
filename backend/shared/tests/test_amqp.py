"""AMQP job serialization + AmqpClient tests — stdlib unittest, no broker.

The aio-pika connection/channels and everything returned by them are mocked;
what's exercised is our own logic: publisher caching, channel reuse,
topology declaration, and the not-connected guards.

Run: .venv/bin/python -m unittest backend.shared.tests.test_amqp -v
     (from the repo root with the workspace venv)
"""

import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from aio_pika.abc import ExchangeType
from shared.amqp import (
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
    AmqpClient,
    AmqpClientException,
    AmqpResumeJob,
    AmqpSuggestionJob,
    AmqpTailorJob,
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
        self.assertEqual(msg.body, job.to_bytes())


def _client() -> AmqpClient:
    client = AmqpClient("amqp://test")
    client.amqp_connection = None
    return client


def _queue_mock():
    queue = MagicMock()
    queue.bind = AsyncMock()
    queue.consume = AsyncMock()
    return queue


def _conn_with_channel():
    """Connection mock whose channel() yields a channel mock."""
    conn = MagicMock()
    channel = MagicMock()
    channel.is_closed = False
    channel.declare_exchange = AsyncMock(return_value=MagicMock())
    channel.declare_queue = AsyncMock(side_effect=lambda *a, **k: _queue_mock())
    conn.channel = AsyncMock(return_value=channel)
    return conn, channel


class AmqpClientConnect(unittest.IsolatedAsyncioTestCase):
    async def test_connect_uses_robust_connection_and_clears_publishers(self):
        client = _client()
        conn = MagicMock()
        client._publishers[("stale", "#")] = MagicMock()

        with patch(
            "shared.amqp.aio_pika.connect_robust",
            AsyncMock(return_value=conn),
        ) as connect:
            await client.connect()

        connect.assert_awaited_once()
        self.assertIs(client.amqp_connection, conn)
        self.assertEqual(client._publishers, {})

    async def test_connect_failure_raises_client_exception(self):
        client = _client()
        with patch(
            "shared.amqp.aio_pika.connect_robust",
            AsyncMock(side_effect=ValueError("down")),
        ), self.assertRaises(AmqpClientException):
            await client.connect()

    async def test_setup_without_topology_just_connects(self):
        client = _client()
        conn, _ = _conn_with_channel()
        with patch(
            "shared.amqp.aio_pika.connect_robust", AsyncMock(return_value=conn)
        ):
            await client.setup(declare_topology=False)
        conn.channel.assert_not_awaited()

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
    async def test_requires_connection(self):
        client = _client()
        with self.assertRaises(AmqpClientException):
            await client.get_publisher("x")
        with self.assertRaises(AmqpClientException):
            await client.consume("q", AsyncMock())
        with self.assertRaises(AmqpClientException):
            await client.declare_topology()

    async def test_publisher_cached_per_exchange_and_key(self):
        client = _client()
        conn, channel = _conn_with_channel()
        client.amqp_connection = conn

        first = await client.get_publisher(RESUME_EXCHANGE_NAME)
        second = await client.get_publisher(RESUME_EXCHANGE_NAME)
        self.assertIs(first, second)
        channel.declare_exchange.assert_awaited_once()

        await client.get_publisher(TAILOR_EXCHANGE_NAME)
        self.assertEqual(channel.declare_exchange.await_count, 2)

        # One shared channel backs all publishers.
        conn.channel.assert_awaited_once()

    async def test_publisher_declares_topic_exchange(self):
        client = _client()
        conn, channel = _conn_with_channel()
        client.amqp_connection = conn

        await client.get_publisher(RESUME_EXCHANGE_NAME)
        channel.declare_exchange.assert_awaited_once_with(
            RESUME_EXCHANGE_NAME,
            ExchangeType.TOPIC,
            durable=True,
        )

    async def test_publisher_publish_routes_with_key(self):
        client = _client()
        conn, channel = _conn_with_channel()
        client.amqp_connection = conn
        exchange = AsyncMock()
        channel.declare_exchange = AsyncMock(return_value=exchange)

        publisher = await client.get_publisher(RESUME_EXCHANGE_NAME, "#")
        msg = AmqpResumeJob(s3_key="k", job_id="j", user_id="u").to_message()
        await publisher.publish(msg)
        exchange.publish.assert_awaited_once_with(
            msg, routing_key="#", mandatory=False
        )

    async def test_consume_declares_queue_and_registers_callback(self):
        client = _client()
        conn, channel = _conn_with_channel()
        client.amqp_connection = conn
        queue = _queue_mock()
        channel.declare_queue = AsyncMock(return_value=queue)

        callback = AsyncMock()
        await client.consume(RESUME_QUEUE_NAME, callback)

        channel.declare_queue.assert_awaited_once_with(
            RESUME_QUEUE_NAME,
            durable=True,
            arguments={"x-dead-letter-exchange": RESUME_DLX_NAME},
        )
        queue.consume.assert_awaited_once_with(callback)

    async def test_consume_uses_fresh_channel_per_queue(self):
        client = _client()
        conn = MagicMock()
        channels = []

        async def channel_factory():
            c = MagicMock()
            c.declare_queue = AsyncMock(return_value=_queue_mock())
            channels.append(c)
            return c

        conn.channel = channel_factory
        client.amqp_connection = conn

        await client.consume(RESUME_QUEUE_NAME, AsyncMock())
        await client.consume(TAILOR_QUEUE_NAME, AsyncMock())
        self.assertEqual(len(channels), 2)
        self.assertIsNot(channels[0], channels[1])


class DeclareTopology(unittest.IsolatedAsyncioTestCase):
    async def test_declares_everything(self):
        client = _client()
        conn, channel = _conn_with_channel()
        queues = {}

        async def declare_queue(name, **kwargs):
            q = _queue_mock()
            queues[name] = (q, kwargs)
            return q

        channel.declare_queue = declare_queue
        client.amqp_connection = conn

        await client.declare_topology()

        exchanges = {
            c.args[0] for c in channel.declare_exchange.await_args_list
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
        self.assertEqual(
            set(queues),
            {
                RESUME_DLQ_NAME,
                RESUME_QUEUE_NAME,
                BULLET_SUGG_QUEUE_NAME,
                BULLET_SUGG_DLQ_NAME,
                TAILOR_QUEUE_NAME,
                TAILOR_DLQ_NAME,
            },
        )
        # Every queue ends up bound to its exchange.
        self.assertTrue(all(q.bind.await_count == 1 for q, _ in queues.values()))

        # The work queues dead-letter into their DLX; the DLQs don't.
        self.assertEqual(
            queues[RESUME_QUEUE_NAME][1]["arguments"],
            {"x-dead-letter-exchange": RESUME_DLX_NAME},
        )
        self.assertIsNone(queues[RESUME_DLQ_NAME][1]["arguments"])

        for call in channel.declare_exchange.await_args_list:
            self.assertEqual(call.kwargs["durable"], True)
            self.assertEqual(call.kwargs.get("auto_delete", False), False)
        for _, kwargs in queues.values():
            self.assertEqual(kwargs["durable"], True)


if __name__ == "__main__":
    unittest.main()

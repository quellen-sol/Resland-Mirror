import json
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import aio_pika
from aio_pika import ExchangeType
from aio_pika.abc import (
    AbstractChannel,
    AbstractExchange,
    AbstractIncomingMessage,
    AbstractRobustConnection,
)

RESUME_QUEUE_NAME = "resume-parser-queue"
RESUME_EXCHANGE_NAME = "resume-parser-exchange"
RESUME_DLQ_NAME = "resume-parser-dlq"
RESUME_DLX_NAME = "resume-parser-dlx"

BULLET_SUGG_EXCHANGE_NAME = "bullet-sugg-exchange"
BULLET_SUGG_QUEUE_NAME = "bullet-sugg-queue"
BULLET_SUGG_DLQ_NAME = "bullet-sugg-dlq"
BULLET_SUGG_DLX_NAME = "bullet-sugg-dlx"

TAILOR_EXCHANGE_NAME = "tailor-exchange"
TAILOR_QUEUE_NAME = "tailor-queue"
TAILOR_DLQ_NAME = "tailor-dlq"
TAILOR_DLX_NAME = "tailor-dlx"

SYSTEM_DESIGN_EXCHANGE_NAME = "system-design-exchange"
SYSTEM_DESIGN_QUEUE_NAME = "system-design-queue"
SYSTEM_DESIGN_DLQ_NAME = "system-design-dlq"
SYSTEM_DESIGN_DLX_NAME = "system-design-dlx"

# Every (exchange, queue) pair is declared and bound with "#" (topic).
_TOPOLOGY_PAIRS = (
    (RESUME_DLX_NAME, RESUME_DLQ_NAME),
    (RESUME_EXCHANGE_NAME, RESUME_QUEUE_NAME),
    (BULLET_SUGG_EXCHANGE_NAME, BULLET_SUGG_QUEUE_NAME),
    (BULLET_SUGG_DLX_NAME, BULLET_SUGG_DLQ_NAME),
    (TAILOR_DLX_NAME, TAILOR_DLQ_NAME),
    (TAILOR_EXCHANGE_NAME, TAILOR_QUEUE_NAME),
    (SYSTEM_DESIGN_DLX_NAME, SYSTEM_DESIGN_DLQ_NAME),
    (SYSTEM_DESIGN_EXCHANGE_NAME, SYSTEM_DESIGN_QUEUE_NAME),
)

_WORK_QUEUE_DLX = {
    RESUME_QUEUE_NAME: RESUME_DLX_NAME,
    BULLET_SUGG_QUEUE_NAME: BULLET_SUGG_DLX_NAME,
    TAILOR_QUEUE_NAME: TAILOR_DLX_NAME,
    SYSTEM_DESIGN_QUEUE_NAME: SYSTEM_DESIGN_DLX_NAME,
}


def _queue_arguments(queue_name: str) -> dict | None:
    dlx = _WORK_QUEUE_DLX.get(queue_name)
    return {"x-dead-letter-exchange": dlx} if dlx else None


class BaseAmqpJob:
    def to_bytes(self) -> bytes:
        as_json = json.dumps(self.__dict__)
        return as_json.encode()

    def to_message(self) -> aio_pika.Message:
        return aio_pika.Message(
            body=self.to_bytes(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )


@dataclass
class AmqpResumeJob(BaseAmqpJob):
    s3_key: str
    job_id: str
    user_id: str
    job_type: str = "resume"


# Sessions and tailor runs are multi-turn: start, every answer, and every retry
# publish a new job for the same session_id/run_id. turn_id is fresh per
# publish, so the dispatcher bills each turn once — a redelivered message keeps
# its turn_id and can't charge twice.
@dataclass
class AmqpSuggestionJob(BaseAmqpJob):
    session_id: str
    answer: str | None = None
    prompt: str | None = None
    turn_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    job_type: str = "suggestion"


@dataclass
class AmqpTailorJob(BaseAmqpJob):
    run_id: str
    answer: str | None = None
    turn_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    job_type: str = "tailor"


# A system design interview is multi-turn like a tailor run. The candidate's
# notes and diagram are saved on the session row before publishing — only the
# action and chat text travel on the wire.
SYSTEM_DESIGN_ACTIONS = ("start", "message", "advance", "finish", "retry")


@dataclass
class AmqpSystemDesignJob(BaseAmqpJob):
    session_id: str
    action: str = "start"
    text: str | None = None
    turn_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    job_type: str = "system_design"


class AmqpClientException(Exception):
    pass


class AmqpPublisher:
    def __init__(self, exchange: AbstractExchange, routing_key: str):
        self._exchange = exchange
        self._routing_key = routing_key

    async def publish(self, message: aio_pika.Message):
        await self._exchange.publish(
            message, routing_key=self._routing_key, mandatory=False
        )


class AmqpClient:
    amqp_connection: AbstractRobustConnection | None = None

    def __init__(self, uri: str):
        self._uri = uri
        self._publishers: dict[tuple[str, str], AmqpPublisher] = {}
        self._channel: AbstractChannel | None = None

    async def setup(self, declare_topology=True):
        await self.connect()
        if declare_topology:
            await self.declare_topology()

    async def connect(self):
        # A fresh connection invalidates any channels/exchanges opened on it.
        self._publishers.clear()
        self._channel = None
        try:
            # Robust connections re-dial and restore channels on drops.
            self.amqp_connection = await aio_pika.connect_robust(self._uri)
        except Exception as e:
            raise AmqpClientException("Failed to connect to AMQP") from e

    async def close(self):
        if self.amqp_connection:
            await self.amqp_connection.close()
            self.amqp_connection = None
            self._channel = None

    def _require_connection(self) -> AbstractRobustConnection:
        if not self.amqp_connection:
            raise AmqpClientException("AMQPClient not connected")
        return self.amqp_connection

    async def _get_channel(self) -> AbstractChannel:
        conn = self._require_connection()
        if self._channel is None or self._channel.is_closed:
            # Cached publishers hold exchanges from the old channel — invalid.
            self._channel = await conn.channel()
            self._publishers.clear()
        return self._channel

    async def get_publisher(
        self, exchange_name: str, routing_key: str = "#"
    ) -> AmqpPublisher:
        channel = await self._get_channel()
        key = (exchange_name, routing_key)
        publisher = self._publishers.get(key)
        if publisher is None:
            exchange = await channel.declare_exchange(
                exchange_name,
                ExchangeType.TOPIC,
                durable=True,
            )
            publisher = AmqpPublisher(exchange, routing_key)
            self._publishers[key] = publisher
        return publisher

    async def consume(
        self,
        queue_name: str,
        on_message: Callable[[AbstractIncomingMessage], Awaitable[Any]],
    ) -> AbstractChannel:
        conn = self._require_connection()
        # Each consumer gets its own channel so channel errors stay isolated.
        channel = await conn.channel()
        queue = await channel.declare_queue(
            queue_name, durable=True, arguments=_queue_arguments(queue_name)
        )
        await queue.consume(on_message)
        return channel

    async def declare_topology(self):
        channel = await self._get_channel()
        for exchange_name, queue_name in _TOPOLOGY_PAIRS:
            exchange = await channel.declare_exchange(
                exchange_name,
                ExchangeType.TOPIC,
                durable=True,
            )
            queue = await channel.declare_queue(
                queue_name,
                durable=True,
                arguments=_queue_arguments(queue_name),
            )
            await queue.bind(exchange, routing_key="#")

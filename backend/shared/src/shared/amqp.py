import json
from contextlib import suppress
from dataclasses import dataclass

from rabbitmq_amqp_python_client import (
    AddressHelper,
    AMQPMessagingHandler,
    AsyncConnection,
    AsyncEnvironment,
    ClassicQueueSpecification,
    ConnectionClosed,
    ExchangeSpecification,
    ExchangeToQueueBindingSpecification,
    ExchangeType,
    Message,
)

RESUME_QUEUE_NAME = "resume-parser-queue"
RESUME_EXCHANGE_NAME = "resume-parser-exchange"
RESUME_DLQ_NAME = "resume-parser-dlq"
RESUME_DLX_NAME = "resume-parser-dlx"

BULLET_SUGG_EXCHANGE_NAME = "bullet-sugg-exchange"
BULLET_SUGG_QUEUE_NAME = "bullet-sugg-queue"
BULLET_SUGG_DLQ_NAME = "bullet-sugg-dlq"
BULLET_SUGG_DLX_NAME = "bullet-sugg-dlx"


@dataclass
class AMQPJob:
    s3_key: str
    job_id: str
    user_id: str

    def to_bytes(self) -> bytes:
        as_json = json.dumps(
            {
                "s3_key": self.s3_key,
                "job_id": self.job_id,
                "user_id": self.user_id,
            }
        )
        return as_json.encode()

    def as_message(self) -> Message:
        return Message(body=self.to_bytes())


class AMQPClientException(Exception):
    pass


class AMQPClient:
    async_env: AsyncEnvironment
    amqp_connection: AsyncConnection | None = None

    def __init__(self, uri: str):
        self.async_env = AsyncEnvironment(uri=uri)
        self._publishers: dict = {}

    async def setup(self, declare_topology=True):
        await self.connect()
        if declare_topology:
            await self.declare_topology()

    async def connect(self):
        # A fresh connection invalidates any previously opened senders.
        self._publishers.clear()
        try:
            self.amqp_connection = await self.async_env.connection()
            await self.amqp_connection.dial()
        except Exception as e:
            raise AMQPClientException("Failed to connect to AMQP") from e

    async def close(self):
        if self.amqp_connection:
            await self.amqp_connection.close()
            self.amqp_connection = None

    async def get_publisher(self, exchange_name: str, routing_key: str):
        if not self.amqp_connection:
            raise AMQPClientException("AMQPClient not connected")
        exchange_addr = AddressHelper.exchange_address(exchange_name, routing_key)
        # Reuse senders — a second link with the same address gets the same
        # link name, and the broker kills the connection (amqp:invalid-field).
        if exchange_addr in self._publishers:
            return self._publishers[exchange_addr]
        try:
            publisher = await self.amqp_connection.publisher(exchange_addr)
        except ConnectionClosed:
            # The broker may have dropped an idle connection; re-dial and retry once.
            with suppress(Exception):
                await self.amqp_connection.close()
            await self.connect()
            publisher = await self.amqp_connection.publisher(exchange_addr)
        self._publishers[exchange_addr] = publisher
        return publisher

    async def get_consumer(self, queue_name: str, handler: AMQPMessagingHandler):
        if not self.amqp_connection:
            raise AMQPClientException("AMQPClient not connected")
        queue_addr = AddressHelper.queue_address(queue_name)
        return await self.amqp_connection.consumer(
            destination=queue_addr, message_handler=handler
        )

    async def get_manager(self):
        if not self.amqp_connection:
            raise AMQPClientException("AMQPClient not connected")
        return await self.amqp_connection.management()

    async def declare_topology(self):
        if not self.amqp_connection:
            raise AMQPClientException("AMQPClient not connected")
        manager = await self.get_manager()

        # DLQs/DLXs
        await manager.declare_exchange(
            ExchangeSpecification(
                name=RESUME_DLX_NAME,
                exchange_type=ExchangeType.topic,
                is_auto_delete=True,
                is_durable=False,
            )
        )
        await manager.declare_queue(
            ClassicQueueSpecification(name=RESUME_DLQ_NAME, is_durable=True)
        )
        await manager.bind(
            ExchangeToQueueBindingSpecification(
                source_exchange=RESUME_DLX_NAME,
                destination_queue=RESUME_DLQ_NAME,
                binding_key="#",
            )
        )

        # Declare exchanges, queues, bindings here
        await manager.declare_exchange(
            ExchangeSpecification(
                name=RESUME_EXCHANGE_NAME,
                exchange_type=ExchangeType.topic,
                is_auto_delete=True,
                is_durable=False,
            )
        )
        await manager.declare_queue(
            ClassicQueueSpecification(
                name=RESUME_QUEUE_NAME,
                is_durable=True,
                dead_letter_exchange=RESUME_DLX_NAME,
            )
        )
        await manager.bind(
            ExchangeToQueueBindingSpecification(
                source_exchange=RESUME_EXCHANGE_NAME,
                destination_queue=RESUME_QUEUE_NAME,
                binding_key="#",
            )
        )

        # Bullet Sugg
        await manager.declare_exchange(
            ExchangeSpecification(
                name=BULLET_SUGG_EXCHANGE_NAME,
                exchange_type=ExchangeType.topic,
                is_auto_delete=True,
                is_durable=False,
            )
        )
        await manager.declare_queue(
            ClassicQueueSpecification(
                name=BULLET_SUGG_QUEUE_NAME,
                is_durable=True,
                dead_letter_exchange=BULLET_SUGG_DLX_NAME,
            )
        )
        await manager.bind(
            ExchangeToQueueBindingSpecification(
                source_exchange=BULLET_SUGG_EXCHANGE_NAME,
                destination_queue=BULLET_SUGG_QUEUE_NAME,
                binding_key="#",
            )
        )
        await manager.declare_exchange(
            ExchangeSpecification(
                name=BULLET_SUGG_DLX_NAME,
                exchange_type=ExchangeType.topic,
                is_auto_delete=True,
                is_durable=False,
            )
        )
        await manager.declare_queue(
            ClassicQueueSpecification(name=BULLET_SUGG_DLQ_NAME, is_durable=True)
        )
        await manager.bind(
            ExchangeToQueueBindingSpecification(
                source_exchange=BULLET_SUGG_DLX_NAME,
                destination_queue=BULLET_SUGG_DLQ_NAME,
                binding_key="#",
            )
        )

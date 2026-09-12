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


@dataclass
class AMQPJob:
    s3_key: str
    job_id: str

    def to_bytes(self) -> bytes:
        as_json = json.dumps({"s3_key": self.s3_key, "job_id": self.job_id})
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

    async def setup(self):
        await self.connect()
        await self.declare_topology()

    async def connect(self):
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
        try:
            return await self.amqp_connection.publisher(exchange_addr)
        except ConnectionClosed:
            # The broker may have dropped an idle connection; re-dial and retry once.
            with suppress(Exception):
                await self.amqp_connection.close()
            await self.connect()
            return await self.amqp_connection.publisher(exchange_addr)

    async def get_consumer(self, queue_name: str, handler: AMQPMessagingHandler):
        if not self.amqp_connection:
            raise AMQPClientException("AMQPClient not connected")
        queue_addr = AddressHelper.queue_address(queue_name)
        return await self.amqp_connection.consumer(queue_addr, message_handler=handler)

    async def get_manager(self):
        if not self.amqp_connection:
            raise AMQPClientException("AMQPClient not connected")
        return await self.amqp_connection.management()

    async def declare_topology(self):
        if not self.amqp_connection:
            raise AMQPClientException("AMQPClient not connected")
        manager = await self.get_manager()
        # Declare exchanges, queues, bindings here
        await manager.declare_exchange(ExchangeSpecification(name="test-exchange", exchange_type=ExchangeType.topic, is_auto_delete=True, is_durable=False))
        await manager.declare_queue(ClassicQueueSpecification(name="test-queue", is_durable=True))
        await manager.bind(ExchangeToQueueBindingSpecification(source_exchange="test-exchange", destination_queue="test-queue", binding_key="#"))

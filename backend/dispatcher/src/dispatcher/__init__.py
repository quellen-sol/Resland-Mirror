import asyncio

from rabbitmq_amqp_python_client import AsyncEnvironment
from shared.amqp import (
    BULLET_SUGG_QUEUE_NAME,
    RESUME_QUEUE_NAME,
    AddressHelper,
)

from .env_vars import AMQP_URL
from .handlers.resume_handler import ResumeHandler
from .handlers.suggestion_handler import SuggestionHandler


async def async_main() -> None:
    amqp_env = AsyncEnvironment(uri=AMQP_URL)

    # Resume handler and consumer
    resume_conn = await amqp_env.connection()
    await resume_conn.dial()
    resume_queue_addr = AddressHelper.queue_address(RESUME_QUEUE_NAME)
    resume_consumer = await resume_conn.consumer(
        destination=resume_queue_addr, message_handler=ResumeHandler()
    )

    # Suggestions handler and consumer
    sugg_conn = await amqp_env.connection()
    await sugg_conn.dial()
    sugg_queue_addr = AddressHelper.queue_address(BULLET_SUGG_QUEUE_NAME)
    sugg_consumer = await sugg_conn.consumer(
        destination=sugg_queue_addr, message_handler=SuggestionHandler()
    )

    async with asyncio.TaskGroup() as tg:
        tg.create_task(resume_consumer.run())
        tg.create_task(sugg_consumer.run())


def main() -> None:
    asyncio.run(async_main())

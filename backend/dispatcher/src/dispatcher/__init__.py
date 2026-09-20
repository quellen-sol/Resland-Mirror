import asyncio

from rabbitmq_amqp_python_client import AsyncEnvironment
from shared.amqp import (
    BULLET_SUGG_QUEUE_NAME,
    RESUME_QUEUE_NAME,
    TAILOR_QUEUE_NAME,
    AddressHelper,
)

from .env_vars import AMQP_URL
from .handlers.resume_handler import ResumeHandler
from .handlers.suggestion_handler import SuggestionHandler
from .handlers.tailor_handler import TailorHandler


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

    # Tailor handler and consumer
    tailor_conn = await amqp_env.connection()
    await tailor_conn.dial()
    tailor_queue_addr = AddressHelper.queue_address(TAILOR_QUEUE_NAME)
    tailor_consumer = await tailor_conn.consumer(
        destination=tailor_queue_addr, message_handler=TailorHandler()
    )

    async with asyncio.TaskGroup() as tg:
        tg.create_task(resume_consumer.run())
        tg.create_task(sugg_consumer.run())
        tg.create_task(tailor_consumer.run())


def main() -> None:
    asyncio.run(async_main())

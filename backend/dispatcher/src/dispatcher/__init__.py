import asyncio

from shared.amqp import (
    BULLET_SUGG_QUEUE_NAME,
    RESUME_QUEUE_NAME,
    TAILOR_QUEUE_NAME,
    AmqpClient,
)

from .env_vars import AMQP_URL
from .handlers.resume_handler import ResumeHandler
from .handlers.suggestion_handler import SuggestionHandler
from .handlers.tailor_handler import TailorHandler
from .pg import do_pg_setup


async def async_main(stop_event: asyncio.Event | None = None) -> None:
    do_pg_setup()

    client = AmqpClient(AMQP_URL)
    await client.setup()

    # One robust connection; each consumer gets its own channel.
    await client.consume(RESUME_QUEUE_NAME, ResumeHandler().on_message)
    await client.consume(BULLET_SUGG_QUEUE_NAME, SuggestionHandler().on_message)
    await client.consume(TAILOR_QUEUE_NAME, TailorHandler().on_message)

    try:
        await (stop_event or asyncio.Event()).wait()
    finally:
        await client.close()


def main() -> None:
    asyncio.run(async_main())

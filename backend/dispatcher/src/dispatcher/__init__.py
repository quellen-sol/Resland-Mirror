import asyncio
import signal

from shared.amqp import RESUME_QUEUE_NAME, AMQPClient

from .amqp_handler import DispatcherHandler
from .env_vars import AMQP_URL


async def async_main() -> None:
    amqp_client = AMQPClient(AMQP_URL)
    # Declarations are idempotent — whichever service starts first creates the
    # topology, so consumers never race a missing queue.
    await amqp_client.setup()

    consumer = await amqp_client.get_consumer(
        queue_name=RESUME_QUEUE_NAME, handler=DispatcherHandler()
    )
    print("Dispatcher connected, starting consumer...")
    await consumer.run()

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    try:
        await stop.wait()
    finally:
        await consumer.stop()
        await amqp_client.close()


def main() -> None:
    asyncio.run(async_main())

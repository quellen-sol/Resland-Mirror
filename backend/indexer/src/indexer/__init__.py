import os

from shared.amqp import AMQPClient
from shared.s3 import s3_client


async def async_main() -> None:
    amqp_client = AMQPClient(os.getenv("AMQP_URL"))
    await amqp_client.setup()
    
    print("Hello from indexer!")


def main() -> None:
    import asyncio
    asyncio.run(async_main())

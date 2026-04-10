import asyncio
import logging

from src.messaging.broker import broker
from src.messaging.outbox_worker import run_outbox_worker
from src.messaging.queues import retry_dlx, retry_queue
import src.messaging.subscriber as sub  # noqa: F401

logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Starting consumer")
    await broker.start()
    await broker.declare_exchange(retry_dlx)
    await broker.declare_queue(retry_queue)
    outbox_task = asyncio.create_task(run_outbox_worker())
    logger.info("Consumer started, waiting for messages")
    try:
        await asyncio.Event().wait()
    finally:
        outbox_task.cancel()
        await sub.webhook_client.close()
        await broker.close()
        logger.info("Consumer stopped")


if __name__ == "__main__":
    asyncio.run(main())

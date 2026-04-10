import asyncio
import logging

from src.config import settings
from src.db.session import async_session
from src.messaging.broker import broker
from src.messaging.queues import payments_queue
from src.payments.repository import get_pending_outbox, update_outbox_status

logger = logging.getLogger(__name__)



async def process_outbox() -> None:
    async with async_session() as session:
        messages = await get_pending_outbox(session)
        for msg in messages:
            try:
                await broker.publish(msg.payload, queue=payments_queue)
                await update_outbox_status(session, msg.id, "published")
                logger.info("Outbox message %s published to %s", msg.id, msg.topic)
            except Exception:
                msg.attempts += 1
                if msg.attempts >= settings.webhook_max_retries:
                    await update_outbox_status(session, msg.id, "failed")
                    logger.error("Outbox message %s failed permanently", msg.id)
                else:
                    await session.commit()
                    logger.warning(
                        "Outbox message %s publish failed (attempt %s/%s)",
                        msg.id, msg.attempts, settings.webhook_max_retries,
                    )


async def run_outbox_worker() -> None:
    logger.info("Outbox worker started")
    while True:
        try:
            await process_outbox()
        except Exception:
            logger.exception("Outbox worker iteration failed")
        await asyncio.sleep(settings.poll_interval)

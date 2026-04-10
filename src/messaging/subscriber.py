import asyncio
import logging
import random

from faststream.rabbit import RabbitMessage

from src.config import settings
from src.db.session import async_session
from src.messaging.broker import broker
from src.messaging.queues import dlq, dlx, payments_queue
from src.payments.repository import get_by_id, update_payment_status
from src.payments.webhook import WebhookClient

logger = logging.getLogger(__name__)

webhook_client = WebhookClient()


def _get_death_count(raw_message: RabbitMessage) -> int:
    headers = raw_message.raw_message.headers or {}
    x_death = headers.get("x-death")
    if not x_death or not isinstance(x_death, list):
        return 0
    total = 0
    for entry in x_death:
        if isinstance(entry, dict):
            total += entry.get("count", 0)
    return total


@broker.subscriber(payments_queue)
async def handle_payment(msg: dict, raw_message: RabbitMessage) -> None:
    payment_id = msg["payment_id"]
    webhook_url = msg["webhook_url"]
    death_count = _get_death_count(raw_message)
    logger.info("Processing payment %s (attempt %s/%s)", payment_id, death_count + 1, settings.webhook_max_retries)

    if death_count == 0:
        delay = random.uniform(2, 5)
        await asyncio.sleep(delay)
        success = random.random() < 0.9
        status = "succeeded" if success else "failed"
        async with async_session() as session:
            await update_payment_status(session, payment_id, status)
        logger.info("Payment %s %s", payment_id, status)
    else:
        async with async_session() as session:
            payment = await get_by_id(session, payment_id)
            status = payment.status if payment else "failed"
        logger.info("Retrying webhook for payment %s (status=%s)", payment_id, status)

    payload = {
        "payment_id": payment_id,
        "status": status,
    }
    sent = await webhook_client.send(webhook_url, payload)
    if not sent:
        if death_count + 1 >= settings.webhook_max_retries:
            logger.error("Payment %s exhausted %s retries, sending to DLQ", payment_id, settings.webhook_max_retries)
            await raw_message.ack()
            await broker.publish(msg, queue=dlq, exchange=dlx)
            return
        logger.warning("Webhook failed for payment %s, rejecting (attempt %s/%s)", payment_id, death_count + 1, settings.webhook_max_retries)
        await raw_message.reject()
        return

    await raw_message.ack()
    logger.info("Payment %s fully processed", payment_id)


@broker.subscriber(dlq, dlx)
async def handle_dlq(msg: dict) -> None:
    logger.error("DLQ received unprocessable message: payment_id=%s", msg.get("payment_id"))

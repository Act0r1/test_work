import logging

from faststream.rabbit import RabbitQueue

from src.messaging.broker import broker
from src.messaging.queues import payments_queue

logger = logging.getLogger(__name__)


async def publish(msg, queue: RabbitQueue=payments_queue):
    await broker.publish(msg.model_dump(mode="json"), queue=queue)

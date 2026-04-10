from src.config import settings
from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue

retry_dlx = RabbitExchange("payments.retry.dlx", type=ExchangeType.DIRECT)

dlx = RabbitExchange("payments.dlx", type=ExchangeType.DIRECT)

retry_queue = RabbitQueue(
    "payments.new.retry",
    durable=True,
    routing_key="payments.new",
    arguments={
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "payments.new",
        "x-message-ttl": int(settings.webhook_base_delay * 1000),
    },
)

dlq = RabbitQueue(
    "payments.new.dlq",
    routing_key="payments.new",
    durable=True,
)

payments_queue = RabbitQueue(
    "payments.new",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.retry.dlx",
        "x-dead-letter-routing-key": "payments.new",
    },
)

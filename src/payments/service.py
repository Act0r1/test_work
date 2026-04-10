import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import OutboxMessageModel, PaymentModel
from src.payments.errors import IdempotencyConflict
from src.payments.repository import get_by_idempotency_key, insert_payment
from src.payments.schemas import PaymentCreateRequest, PaymentStatus

logger = logging.getLogger(__name__)


def _same_payment_request(
    payment: PaymentModel,
    payload: PaymentCreateRequest,
) -> bool:
    return (
        payment.amount == payload.amount
        and payment.currency == payload.currency.value
        and payment.description == payload.description
        and payment.metadata_ == payload.metadata
        and payment.webhook_url == str(payload.webhook_url)
    )


def _build_outbox_message(payment: PaymentModel) -> OutboxMessageModel:
    return OutboxMessageModel(
        topic="payments.new",
        payload={
            "payment_id": str(payment.id),
            "amount": str(payment.amount),
            "currency": payment.currency,
            "description": payment.description,
            "metadata": payment.metadata_,
            "status": payment.status,
            "idempotency_key": str(payment.idempotency_key),
            "webhook_url": payment.webhook_url,
            "created_at": payment.created_at.isoformat(),
            "processed_at": (
                payment.processed_at.isoformat()
                if payment.processed_at is not None
                else None
            ),
        },
        status="pending",
        occurred_at=datetime.now(UTC),
    )



async def create_payment(
    session: AsyncSession,
    payload: PaymentCreateRequest,
    idempotency_key: UUID,
) -> tuple[PaymentModel, bool]:
    existing = await get_by_idempotency_key(session, idempotency_key)
    if existing is not None:
        if _same_payment_request(existing, payload):
            logger.info(
                "Returning existing payment for idempotency_key=%s payment_id=%s",
                idempotency_key,
                existing.id,
            )
            return existing, False
        logger.warning("Idempotency conflict for idempotency_key=%s", idempotency_key)
        raise IdempotencyConflict(str(idempotency_key))

    payment = PaymentModel(
        id=uuid4(),
        amount=payload.amount,
        currency=payload.currency.value,
        description=payload.description,
        metadata_=payload.metadata,
        status=PaymentStatus.PENDING.value,
        idempotency_key=idempotency_key,
        webhook_url=str(payload.webhook_url),
        created_at=datetime.now(UTC),
    )
    outbox = _build_outbox_message(payment)

    logger.info(
        "Creating payment id=%s idempotency_key=%s amount=%s currency=%s",
        payment.id,
        idempotency_key,
        payload.amount,
        payload.currency.value,
    )

    payment = await insert_payment(session, payment, outbox)
    logger.info("Payment created id=%s and outbox event stored", payment.id)
    return payment, True

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import OutboxMessageModel, PaymentModel


async def get_by_id(
    session: AsyncSession,
    payment_id: UUID,
) -> PaymentModel | None:
    return await session.get(PaymentModel, payment_id)


async def get_by_idempotency_key(
    session: AsyncSession,
    idempotency_key: UUID,
) -> PaymentModel | None:
    return await session.scalar(
        select(PaymentModel).where(PaymentModel.idempotency_key == idempotency_key)
    )


async def insert_payment(
    session: AsyncSession,
    payment: PaymentModel,
    outbox: OutboxMessageModel,
) -> PaymentModel:
    session.add(payment)
    await session.flush()
    session.add(outbox)
    await session.commit()
    await session.refresh(payment)
    return payment


async def get_pending_outbox(
    session: AsyncSession,
    limit: int = 50,
) -> list[OutboxMessageModel]:
    result = await session.scalars(
        select(OutboxMessageModel)
        .where(OutboxMessageModel.status == "pending")
        .order_by(OutboxMessageModel.occurred_at)
        .limit(limit)
    )
    return list(result.all())


async def update_outbox_status(
    session: AsyncSession,
    outbox_id: UUID,
    status: str,
) -> None:
    outbox = await session.get(OutboxMessageModel, outbox_id)
    if outbox is None:
        return
    outbox.status = status
    outbox.attempts += 1
    if status == "published":
        outbox.published_at = datetime.now(UTC)
    await session.commit()


async def update_payment_status(
    session: AsyncSession,
    payment_id: UUID,
    status: str,
) -> None:
    payment = await session.get(PaymentModel, payment_id)
    if payment is None:
        return
    payment.status = status
    if status in ("succeeded", "failed"):
        payment.processed_at = datetime.now(UTC)
    await session.commit()

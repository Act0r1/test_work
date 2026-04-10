from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import parse_idempotency_key, verify_api_key
from src.api.schemas import ErrorResponse
from src.db.models import PaymentModel
from src.db.session import get_session
from src.payments.repository import get_by_id
from src.payments.schemas import PaymentCreateRequest, PaymentCreateResponse, PaymentResponse
from src.payments.service import create_payment

router = APIRouter(prefix="/api/v1", dependencies=[Depends(verify_api_key)])


@router.post(
    "/payments",
    response_model=PaymentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def create_payment_handler(
    body: PaymentCreateRequest,
    response: Response,
    idempotency_key: UUID = Depends(parse_idempotency_key),
    session: AsyncSession = Depends(get_session),
) -> PaymentCreateResponse:
    payment, created = await create_payment(session, body, idempotency_key)
    if not created:
        response.status_code = status.HTTP_200_OK
    return PaymentCreateResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
    )


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_payment_handler(
    payment_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> PaymentResponse:
    payment: PaymentModel | None = await get_by_id(session, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentResponse(payment.to_dict())

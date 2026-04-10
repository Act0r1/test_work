import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.schemas import ErrorResponse
from src.payments.errors import IdempotencyConflict

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class MissingIdempotencyKey(ApiError):
    def __init__(self):
        super().__init__(
            status_code=400,
            code="missing_idempotency_key",
            message="Idempotency-Key header is required",
        )


class InvalidIdempotencyKey(ApiError):
    def __init__(self):
        super().__init__(
            status_code=400,
            code="invalid_idempotency_key",
            message="Idempotency-Key must be a valid UUID",
        )


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(code=code, message=message, details=details).model_dump(),
    )


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    logger.warning(
        "API error code=%s status=%s message=%s",
        exc.code,
        exc.status_code,
        exc.message,
    )
    return _error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
    )


async def idempotency_conflict_handler(
    _: Request, exc: IdempotencyConflict
) -> JSONResponse:
    logger.warning("Idempotency conflict key=%s", exc.key)
    return _error_response(
        status_code=409,
        code=exc.code,
        message=exc.message,
    )


async def validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning("Request validation error details=%s", exc.errors())
    return _error_response(
        status_code=422,
        code="validation_error",
        message="Invalid request",
        details=exc.errors(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(IdempotencyConflict, idempotency_conflict_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

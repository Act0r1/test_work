from uuid import UUID

from fastapi import Header, Security
from fastapi.security import APIKeyHeader

from src.api.errors import InvalidIdempotencyKey, MissingIdempotencyKey
from src.config import settings



def verify_api_key(
    api_key: str = Security(APIKeyHeader(name="X-API-Key")),
) -> str:
    if api_key != settings.api_key:
        from src.api.errors import ApiError
        raise ApiError(status_code=403, code="forbidden", message="Invalid API key")
    return api_key


def parse_idempotency_key(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> UUID:
    if idempotency_key is None:
        raise MissingIdempotencyKey()
    try:
        return UUID(idempotency_key)
    except ValueError:
        raise InvalidIdempotencyKey()

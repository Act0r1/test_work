import asyncio
import logging

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class WebhookClient:
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=settings.webhook_timeout)

    async def send(self, url: str, payload: dict) -> bool:
        max_retries = settings.webhook_max_retries
        for attempt in range(1, max_retries + 1):
            try:
                response = await self._client.post(url, json=payload)
                if response.is_success:
                    logger.info("Webhook sent to %s status=%s", url, response.status_code)
                    return True
                logger.warning(
                    "Webhook %s returned %s (attempt %s/%s)",
                    url, response.status_code, attempt, max_retries,
                )
            except httpx.HTTPError:
                logger.warning(
                    "Webhook %s failed (attempt %s/%s)",
                    url, attempt, max_retries, exc_info=True,
                )
            if attempt < max_retries:
                delay = settings.webhook_base_delay * (2 ** (attempt - 1))
                await asyncio.sleep(delay)
        logger.error("Webhook %s failed after %s attempts", url, max_retries)
        return False

    async def close(self) -> None:
        await self._client.aclose()

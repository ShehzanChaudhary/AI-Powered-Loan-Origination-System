"""Adapter for the credit bureau (CIBIL-style) API. Currently points at our
own demo endpoint (app/api/routes/credit_bureau.py); swapping to a real
bureau integration later means changing only this file (base URL, auth
headers, response mapping) - callers never change."""

import asyncio
import random

import httpx

from app.core.config import settings
from app.adapters.logger import logger
from app.schemas.credit_bureau import CibilReport

class CreditBureauService:
    """Fetches a credit report for a given PAN, with automatic retries."""

    def __init__(self):
        self._client = httpx.AsyncClient(base_url=settings.credit_bureau_base_url)
        logger.info(f"Credit bureau client created, base_url={settings.credit_bureau_base_url}")

    @staticmethod
    def _backoff_delay(attempt: int) -> float:
        return (2 ** attempt) + random.uniform(0, 1)

    async def get_credit_report(self, pan: str, max_retries: int = 2) -> CibilReport:
        last_error = None

        for attempt in range(max_retries):
            try:
                response = await self._client.get(f"/api/v1/bureau/credit-report/{pan}")
                response.raise_for_status()
                return CibilReport(**response.json())
            except Exception as ex:
                last_error = ex
                logger.error(f"Credit bureau request failed on attempt {attempt + 1} {ex}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(self._backoff_delay(attempt))

        raise RuntimeError(f"Credit bureau request failed after {max_retries} attempts") from last_error

    async def close(self):
        await self._client.aclose()

credit_bureau = CreditBureauService()
    
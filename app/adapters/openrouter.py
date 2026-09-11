import asyncio
import random

from openai import AsyncOpenAI

from app.core.config import settings
from app.adapters.logger import logger

class OpenRouterService:
    """Handles chat completions against OpenRouter, with automatic retries"""
    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url
        )
        self._model = settings.MODEL
        logger.info(f"OpenRouter client created {self._model}")

    @staticmethod
    def _backoff_delay(attempt: int) -> float:
        return (2 ** attempt) + random.uniform(0, 1) 

    async def chat(self, prompt: str, json_mode: bool = False, max_retries: int = 2) -> str:
        last_error = None

        for attempt in range(max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    **({"response_format": {"type": "json_object"}} if json_mode else {})
                )
                return response.choices[0].message.content
            except Exception as ex:
                last_error = ex
                logger.error(f"OpenRouter request failed on attempt {attempt + 1} {ex}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(self._backoff_delay(attempt))

        raise RuntimeError(f"OpenRouter request failed after {max_retries} attempts") from last_error

openrouter = OpenRouterService()
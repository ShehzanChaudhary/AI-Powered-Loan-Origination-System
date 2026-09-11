import asyncio
import random

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient

from app.core.config import settings
from app.adapters.logger import logger

class DocumentIntelligentService:
    """Handles document analysis calls against Azure Document Intelligence, with retries."""

    def __init__(self):
        self._client = DocumentIntelligenceClient(
            endpoint=settings.azure_document_intelligence_endpoint,
            credential=AzureKeyCredential(settings.azure_document_intelligence_key)
        )
        logger.info("Azure Document Intelligence client created")

    @staticmethod
    def _backoff_delay(attempt: int) -> float:
        return (2 ** attempt) + random.uniform(0, 1)

    async def analyze(self, model_id: str, file_path: str, max_retries: int = 2):
        """
        Runs the given Azure prebuilt model (e.g. "prebuilt-layout" or
        "prebuilt-idDocument") against a local file and returns the raw
        Azure AnalyzeResult.
        """
        with open(file_path, "rb") as document:
            document_bytes = document.read()

        last_error = None
        for attempt in range(max_retries):
            try:
                poller = await self._client.begin_analyze_document(model_id, body=document_bytes)
                return await poller.result()
            except Exception as ex:
                last_error = ex
                logger.error("Azure analyze (%s) failed on attempt %d: %s", model_id, attempt + 1, ex)
                if attempt < max_retries - 1:
                    await asyncio.sleep(self._backoff_delay(attempt))

        raise RuntimeError(f"Azure analyze ({model_id}) failed after {max_retries}")

    async def close(self):
        """Closes the underlying HTTP session. Call this once, on app shutdown."""
        await self._client.close()

document_intelligence = DocumentIntelligentService()
from pathlib import Path
from functools import lru_cache
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

from app.core.config import settings
from app.schemas.application import ExtractedDocument

class DocumentExtractor:
    """Connects to Azure Document Intelligence and extracts content from documents."""

    def __init__(self):
        """Creates the Azure Document Intelligence client using the configured credentials."""
        self.client = DocumentIntelligenceClient(
            endpoint=settings.azure_document_intelligence_endpoint,
            credential=AzureKeyCredential(
                settings.azure_document_intelligence_key
            )
        )

    def extract_document(self, file_path: str):
        """Sends a local document to Azure Document Intelligence and returns the extraction result."""
        with open(file_path, "rb") as document:
            document_bytes = document.read()

        poller = self.client.begin_analyze_document(
            "prebuilt-layout",
            body=document_bytes
        )

        return poller.result()

    def extract_tables(self, azure_result) -> list:
        """Converts Azure table data into a simple row-and-column structure."""
        tables = []

        for table in azure_result.tables:
            rows = [[] for _ in range(table.row_count)]

            for cell in table.cells:
                row = rows[cell.row_index]

                while len(row) <= cell.column_index:
                    row.append("")

                row[cell.column_index] = cell.content

            tables.append(rows)

        return tables
    
    def build_extraction_result(self, file_path: str, azure_result) -> ExtractedDocument:
        """Converts Azure's raw analysis result into our application's clean extraction structure."""
        return ExtractedDocument(
            file_name=Path(file_path).name,
            page_count=len(azure_result.pages),
            text=azure_result.content,
            tables=self.extract_tables(azure_result)
        )

    def extract_documents(self, file_paths: list[str]) -> list[ExtractedDocument]:
        """Extracts all documents from a directory and converts them into internal extraction results."""
        extracted_documents = []

        for file_path in file_paths:
            azure_result = self.extract_document(file_path)

            extracted_document = self.build_extraction_result(
                file_path,
                azure_result
            )

            extracted_documents.append(extracted_document)

        return extracted_documents

@lru_cache
def get_document_extractor() -> DocumentExtractor:
    """
    Returns a single shared DocumentExtractor instance across the whole app,
    instead of creating a new Azure client (and a new network connection
    pool) on every request.
    """
    return DocumentExtractor()


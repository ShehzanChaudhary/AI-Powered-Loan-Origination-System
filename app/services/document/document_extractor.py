import asyncio
from pathlib import Path

from app.adapters.document_intelligence import document_intelligence
from app.schemas.application import ExtractedDocument

def extract_tables(azure_result) -> list:
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

def build_extraction_result(file_path: str, azure_result) -> ExtractedDocument:
    """Converts Azure's raw analysis result into our application's clean extraction structure."""
    return ExtractedDocument(
        file_name=Path(file_path).name,
        page_count=len(azure_result.pages),
        text=azure_result.content,
        tables=extract_tables(azure_result)
    )

async def extract_document(file_path: str) -> ExtractedDocument:
    """Sends a local document to Azure Document Intelligence and returns the extraction result."""
    azure_result = await document_intelligence.analyze("prebuilt-layout", file_path)
    return build_extraction_result(file_path, azure_result)

async def extract_documents(file_paths: list[str]) -> list[ExtractedDocument]:
    """Extracts ALL documents CONCURRENTLY, instead of one after another."""
    return await asyncio.gather(*(extract_document(fp) for fp in file_paths))



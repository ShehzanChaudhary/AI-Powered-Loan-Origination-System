from pydantic import BaseModel

class DocumentInfo(BaseModel):
    """Represents one document received as part of a loan application."""
    file_name: str
    document_type: str
    status: str

class ApplicationResponse(BaseModel):
    """Represents the structured response returned after processing an application upload."""
    application_id: str
    status: str
    file_name: str
    documents: list[DocumentInfo]

class ExtractedDocument(BaseModel):
    """Represents the clean document extraction result used internally by the application."""
    file_name: str
    page_count: int
    text: str
    tables: list

class DocumentClassificationResult(BaseModel):
    """Represents the document type and evidence produced by the document classifier."""
    document_type: str
    matched_keywords: list[str]
    score: int
    confidence: float
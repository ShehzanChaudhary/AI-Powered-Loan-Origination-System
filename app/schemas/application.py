from typing import Optional
from pydantic import BaseModel

class ExtractedFields(BaseModel):
    """
    Structured fields pulled out of a document, regardless of whether the
    source was Azure's ID model or the LLM fallback. Not every document
    type will populate every field - e.g. a PAN card won't have gross_salary.
    """
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    document_number: Optional[str] = None # PAN no. / Aadhaar no. / account no. etc.
    address: Optional[str] = None
    employer: Optional[str] = None
    designation: Optional[str] = None
    gross_salary: Optional[float] = None
    net_pay: Optional[float] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc: Optional[str] = None
    loan_amount_requested: Optional[float] = None
    loan_purpose: Optional[str] = None
    tenure_months: Optional[int] = None
    existing_emi: Optional[float] = None

    extraction_source: str = "LLM" # "azure_id_model" or "llm"

class DocumentInfo(BaseModel):
    """Represents one document received as part of a loan application."""
    file_name: str
    document_type: str
    status: str
    fields: Optional[ExtractedFields] = None

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
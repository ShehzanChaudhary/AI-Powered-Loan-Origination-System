import asyncio
from uuid import uuid4
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.ingestion.zip_handler import extract_zip
from app.services.document import document_extractor
from app.services.document.document_classifier import DocumentClassifier
from app.services.document.field_extractor import extract_structured_fields
from app.services.verification.cross_document_verifier import CrossDocumentVerifier
from app.schemas.application import DocumentInfo, ApplicationResponse

router = APIRouter(prefix="/api/v1/applications", tags=["Applications"])

UPLOAD_DIR = Path("data/uploads")
classifier = DocumentClassifier()
verifier = CrossDocumentVerifier()


def generate_application_id() -> str:
    """Generates a unique application ID for each loan application."""
    return f"LN-{uuid4().hex[:8].upper()}"


@router.post("/upload", response_model=ApplicationResponse)
async def upload_applications(file: UploadFile = File(...)):
    """Receives the customer's ZIP file, validates it, extracts, classifies,
    verifies every document inside, and returns the processed application
    summary."""
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed.")

    application_id = generate_application_id()
    application_dir = UPLOAD_DIR / application_id
    application_dir.mkdir(parents=True, exist_ok=True)

    zip_path = application_dir / file.filename
    file_content = await file.read()
    with open(zip_path, "wb") as output_file:
        output_file.write(file_content)

    extract_dir = Path("data/extracted") / application_id
    extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        extracted_files = extract_zip(zip_path=zip_path, extract_dir=extract_dir)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    # Stage 1: layout extraction for ALL documents, concurrently
    extracted_documents = await document_extractor.extract_documents(
        [str(path) for path in extracted_files]
    )

    # Stage 2: classification - fast keyword match first, LLM fallback for
    # low-confidence documents.
    classifications = await asyncio.gather(*(
        classifier.classify(doc.text) for doc in extracted_documents
    ))

    # Stage 3: structured field extraction for ALL documents, concurrently
    field_results = await asyncio.gather(*(
        extract_structured_fields(str(file_path), classification.document_type, doc.text)
        for file_path, doc, classification in zip(extracted_files, extracted_documents, classifications)
    ))

    documents = [
        DocumentInfo(
            file_name=doc.file_name,
            document_type=classification.document_type,
            status="received",
            fields=fields,
        )
        for doc, classification, fields in zip(extracted_documents, classifications, field_results)
    ]

    # Stage 4: cross-document verification - rule-based, deterministic
    documents_by_type = {doc.document_type: doc.fields for doc in documents}
    verification = verifier.verify(documents_by_type)

    return ApplicationResponse(
        application_id=application_id,
        status="received",
        file_name=file.filename,
        documents=documents,
        verification=verification,
    )
from uuid import uuid4
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.services.ingestion.zip_handler import extract_zip
from app.services.document.document_extractor import get_document_extractor
from app.services.document.document_classifier import DocumentClassifier
from app.schemas.application import DocumentInfo, ApplicationResponse

router = APIRouter(
    prefix="/api/v1/applications",
    tags=["Applications"]
)

UPLOAD_DIR = Path("data/uploads")

classifier = DocumentClassifier()


def generate_application_id() -> str:
    """Generates a unique application ID for each loan application."""
    return f"LN-{uuid4().hex[:8].upper()}"


@router.post("/upload", response_model=ApplicationResponse)
async def upload_applications(file: UploadFile = File(...)):
    """Receives the customer's ZIP file, validates it, extracts and classifies
       every document inside, and returns the processed application summary."""

    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Only ZIP files are allowed."
        )

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
        extracted_files = extract_zip(
            zip_path=zip_path,
            extract_dir=extract_dir
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    """The Azure SDK calls here are synchronous/blocking. If called directly within an `async def` route, they would block the entire server's event loop (meaning the server wouldn't be able to handle any other requests until the Azure response arrives). `run_in_threadpool executes this in a separate thread, keeping the event loop free."""
    
    extractor = get_document_extractor()
    extracted_documents = await run_in_threadpool(
        extractor.extract_documents,
        [str(path) for path in extracted_files]
    )

    documents = [
        DocumentInfo(
            file_name=document.file_name,
            document_type=classifier.classify(document.text).document_type,
            status="received"
        )
        for document in extracted_documents
    ]

    return ApplicationResponse(
        application_id=application_id,
        status="received",
        file_name=file.filename,
        documents=documents
    )
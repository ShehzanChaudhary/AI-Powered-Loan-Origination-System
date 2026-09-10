from uuid import uuid4
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.ingestion.zip_handler import extract_zip
from app.schemas.application import DocumentInfo, ApplicationResponse

router = APIRouter(
    prefix="/api/v1/applications",
    tags=["Applications"]
)

UPLOAD_DIR = Path("data/uploads")

def generate_application_id() -> str:
    """Generates a unique application ID for each loan application."""
    return f"LN-{uuid4().hex[:8].upper()}"



@router.post("/upload")
async def upload_applications(file: UploadFile = File(...)):
    """Receives the customer's ZIP file, validates it, generates an application ID,
       and saves the uploaded ZIP inside its application-specific directory."""
    
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException (
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

    documents = [
        DocumentInfo(
            file_name=file_path.name,
            document_type="UNKNOWN",
            status="Recieved"
        )
        for file_path in extracted_files
    ]

    return {
        "application_id": application_id,
        "Status": "recieved",
        "file_name": file.filename,
        "documents": documents
    }




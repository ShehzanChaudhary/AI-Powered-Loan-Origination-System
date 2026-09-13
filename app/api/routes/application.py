import asyncio
from uuid import uuid4
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.adapters.logger import logger
from app.services.ingestion.zip_handler import extract_zip
from app.services.document import document_extractor
from app.services.document.document_classifier import DocumentClassifier
from app.services.document.field_extractor import extract_structured_fields
from app.services.verification.cross_document_verifier import CrossDocumentVerifier
from app.schemas.application import DocumentInfo, ApplicationResponse
from app.adapters.credit_bureau import credit_bureau
from app.services.risk.risk_scorer import RiskScorer
from app.services.decision.decision_engine import DecisionEngine
from app.services.decision.justification_generator import generate_justification

router = APIRouter(prefix="/api/v1/applications", tags=["Applications"])

UPLOAD_DIR = Path("data/uploads")
classifier = DocumentClassifier()
verifier = CrossDocumentVerifier()
risk_scorer = RiskScorer()
decision_engine = DecisionEngine()


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

    # Stage 5: credit bureau lookup - needs the applicant's PAN, which we
    # only have once Stage 3 (field extraction) has run.
    credit_report = None
    pan_fields = documents_by_type.get("PAN_CARD")
    pan_number = getattr(pan_fields, "document_number", None)

    if pan_number:
        try:
            credit_report = await credit_bureau.get_credit_report(pan_number)
        except Exception as error:
            logger.error(f"[{application_id}] Credit bureau lookup failed for PAN {pan_number}: {error!r}")
        else:
            logger.info(f"[{application_id}] No PAN found in documents, skipping credit bureau lookup.")

    # Stage 6: Risk Scoring - Rule-Based, Deterministic Scorecard
    loan_application_fields = documents_by_type.get("LOAN_APPLICATION")
    risk_assessment = risk_scorer.calculate(
        loan_application=loan_application_fields,
        credit_report=credit_report,
        verification_status=verification.overall_status
    )

    # Stage 7: final decision - deterministic, rule-based (see DecisionEngine)
    final_decision = decision_engine.decide(verification, credit_report, risk_assessment)

    # Stage 8: LLM-generated plain-language justification - explanation
    # only, does not affect the decision already made in Stage 7
    try:
        final_decision.justification = await generate_justification(final_decision, risk_assessment, verification)
    except Exception as error:
        logger.error(f"[{application_id}] Justification generation failed: {error!r}")

    return ApplicationResponse(
        application_id=application_id,
        status="received",
        file_name=file.filename,
        documents=documents,
        verification=verification,
        credit_report=credit_report,
        risk_assessment=risk_assessment,
        final_decision=final_decision
    )
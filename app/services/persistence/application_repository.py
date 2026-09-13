"""Persists a completed ApplicationResponse to the database. Pydantic
models are converted to plain dicts (.model_dump()) before storage, since
JSON columns need native Python types, not Pydantic objects."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.logger import logger
from app.models.loan_application import LoanApplication
from app.schemas.application import ApplicationResponse

async def save_application(db: AsyncSession, response: ApplicationResponse) -> None:
    """Saves the application. Failure here is logged but does not fail the
    request - the applicant should still get their result even if the
    database write fails (matches the resilience pattern used everywhere
    else in this pipeline: credit bureau, LLM justification, etc.)."""
    try:
        record = LoanApplication(
            application_id=response.application_id,
            file_name=response.file_name,
            status=response.status,
            decision=response.final_decision.decision if response.final_decision else None,
            risk_band=response.risk_assessment.risk_band if response.risk_assessment else None,
            total_score=response.risk_assessment.total_score if response.risk_assessment else None,
            documents=[doc.model_dump() for doc in response.documents],
            verification=response.verification.model_dump() if response.verification else None,
            credit_report=response.credit_report.model_dump() if response.credit_report else None,
            risk_assessment=response.risk_assessment.model_dump() if response.risk_assessment else None,
            final_decision=response.final_decision.model_dump() if response.final_decision else None,
        )
        db.add(record)
        await db.commit()
    except Exception as error:
        logger.error(f"[{response.application_id}] Failed to persist application to database: {error!r}")
        await db.rollback()
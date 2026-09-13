"""SQLAlchemy ORM model for persisted loan applications. Core fields are
real columns (queryable/filterable); the rich nested pipeline output
(documents, verification, credit report, risk factors, decision) is stored
as JSON columns"""

from datetime import datetime, timezone

from sqlalchemy import String, Integer, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20))

    decision: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    risk_band: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    total_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    documents: Mapped[list] = mapped_column(JSON)
    verification: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    credit_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_assessment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    final_decision: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
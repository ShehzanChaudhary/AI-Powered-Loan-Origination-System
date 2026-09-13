"""Rule-based, deterministic risk scoring - an additive scorecard, not an
LLM judgment (consistent with the project's core rule: credit decisions
must be deterministic and auditable). Every point awarded/deducted carries
a human-readable 'detail' string, which Phase 6's decision engine (and its
LLM-generated plain-language justification) will rely on."""

from datetime import datetime, timezone

from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

from app.schemas.application import LoanApplicationFields, RiskFactor, RiskAssessment
from app.schemas.credit_bureau import CibilReport

ASSUMED_INTEREST_RATE_PCT = 9.0 #illustrative rate, used only to estimate the proposed loan's EMI for FOIR
ENQUIRY_LOOKBACK_MONTHS = 6

LOW_RISK_THRESHOLD = 60
MEDIUM_RISK_THRESHOLD = 25

def _calculate_emi(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
    """Standard reducing-balance EMI formula"""
    if not principal or not tenure_months:
        return 0.0
    monthly_rate = annual_rate_pct / 12 / 100
    factor = (1 + monthly_rate) ** tenure_months
    return principal * monthly_rate * factor / (factor - 1)

class RiskScorer:
    """Computes the additive risk scorecard for one application"""

    def _score_credit_score(self, credit_report: CibilReport | None) -> RiskFactor:
        if credit_report is None:
            return RiskFactor(name="Credit Score", points=0, detail="Credit report unavailable - default to 0")

        score = credit_report.credit_score.score
        if score >= 750:
            return RiskFactor(name="Credit Score", points=30, detail=f"Score {score} (>=750)")
        if score >= 650:
            return RiskFactor(name="Credit Score", points=15, detail=f"Score {score} (650-749)")
        return RiskFactor(name="Credit Score", points=0, detail=f"Score {score} (<650)")

    def _score_foir(self, loan_application: LoanApplicationFields | None, credit_report: CibilReport | None) -> RiskFactor:
        if loan_application is None or not loan_application.monthly_income:
            return RiskFactor(name="FOIR", points=0, detail="Monthly income unavailable - could not calculate FOIR")

        existing_emis = 0.0
        if credit_report is not None:
            existing_emis = sum(
                account.emi or 0
                for account in credit_report.credit_accounts if account.account_status == "ACTIVE"
            )

        proposed_emi = _calculate_emi(
            principal=loan_application.loan_amount_requested or 0,
            annual_rate_pct=ASSUMED_INTEREST_RATE_PCT,
            tenure_months=loan_application.tenure_months or 0
        )

        foir_pct = ((existing_emis + proposed_emi) / loan_application.monthly_income) * 100

        if foir_pct <= 40:
            points = 20
        elif foir_pct <= 55:
            points = 10
        else:
            points -= 20

        return RiskFactor(
            name="FOIR",
            points=points,
            detail=(
                f"Existing active EMIs Rs.{existing_emis:.0f} + proposed EMI Rs.{proposed_emi:.0f} "
                f"= {foir_pct:.1f}% of monthly income (assumed {ASSUMED_INTEREST_RATE_PCT}% p.a. on new loan)"
            ),
        )

    def _score_verification(self, verification_status: str | None) -> RiskFactor:
        if verification_status == "CLEAN":
            return RiskFactor(name="Verification", points=15, detail="Cross-document verification CLEAN")
        if verification_status == "FLAGGED":
            return RiskFactor(name="Verification", points=-30, detail="Cross-document verification FLAGGED")
        return RiskFactor(name="Verification", points=0, detail="Verification status unavailable")

    def _score_account_health(self, credit_report: CibilReport | None) -> RiskFactor:
        if credit_report is None:
            return RiskFactor(name="Credit Account Health", points=0, detail="Credit report unavailable")

        accounts = credit_report.credit_accounts
        if any(account.account_status == "WRITTEN_OFF" for account in accounts):
            return RiskFactor(name="Credit Account Health", points=-30, detail="At least one written-off/defaulted account")
        if any((account.overdue_amount or 0) > 0 for account in accounts):
            return RiskFactor(name="Credit Account Health", points=-15, detail="At least one account with an overdue amount")
        return RiskFactor(name="Credit Account Health", points=15, detail="No overdue or written-off accounts")

    def _score_enquiries(self, credit_report: CibilReport | None) -> RiskFactor:
        if credit_report is None:
            return RiskFactor(name="Recent Enquiries", points=0, detail="Credit report unavailable")

        cutoff = datetime.now(timezone.utc) - relativedelta(months=ENQUIRY_LOOKBACK_MONTHS)
        recent_count = 0
        for enquiry in credit_report.enquiries:
            try:
                enquiry_date = date_parser.parse(enquiry.date)
                if enquiry_date.tzinfo is None:
                    enquiry_date = enquiry_date.replace(tzinfo=timezone.utc)
                if enquiry_date >= cutoff:
                    recent_count += 1
            except (ValueError, TypeError):
                continue

        if recent_count <= 2:
            points = 10
        elif recent_count <= 5:
            points = 0
        else:
            points = -10

        return RiskFactor(
            name="Recent Enquiries",
            points=points,
            detail=f"{recent_count} enquiries in the last {ENQUIRY_LOOKBACK_MONTHS} months",
        )

    def calculate(
        self,
        loan_application: LoanApplicationFields | None,
        credit_report: CibilReport | None,
        verification_status: str | None,
    ) -> RiskAssessment:
        factors = [
            self._score_credit_score(credit_report),
            self._score_foir(loan_application, credit_report),
            self._score_verification(verification_status),
            self._score_account_health(credit_report),
            self._score_enquiries(credit_report),
        ]

        total_score = sum(factor.points for factor in factors)

        if total_score >= LOW_RISK_THRESHOLD:
            risk_band = "LOW"
        elif total_score >= MEDIUM_RISK_THRESHOLD:
            risk_band = "MEDIUM"
        else:
            risk_band = "HIGH"

        return RiskAssessment(total_score=total_score, risk_band=risk_band, factors=factors)

        
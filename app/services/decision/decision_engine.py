"""Deterministic, rule-based final decision engine. Hard-decline rules are
checked first (identity mismatch, past defaults, open disputes) - these
override the risk score entirely. If no hard rule fires, the decision
falls back to the risk band from Phase 5's scorecard. No LLM involvement
here - this is the one place in the system that actually decides
anything, and it must stay fully auditable."""

from app.schemas.application import FinalDecision, RiskAssessment, VerificationReport
from app.schemas.credit_bureau import CibilReport

IDENTITY_FIELDS = {"Name", "DOB", "PAN"}

RISK_BAND_TO_DECISION = {
    "LOW": "APPROVED",
    "MEDIUM": "MANUAL_REVIEW",
    "HIGH": "REJECTED"
}

class DecisionEngine:
    """Applies hard-decline rules, then falls back to the risk scorecard."""

    def decide(self, verification: VerificationReport, credit_report: CibilReport | None, risk_assessment: RiskAssessment) -> FinalDecision:
        identity_mismatches = [
            check.field_name
            for check in verification.checks
            if check.field_name in IDENTITY_FIELDS and check.status == "MISMATCH"
        ]
        if identity_mismatches:
            return FinalDecision(
                decision="MANUAL_REVIEW",
                reasons=[f"Identity mismatch detected in: {', '.join(identity_mismatches)}"],
            )

        if credit_report is not None:
            written_off_accounts = [
                account for account in credit_report.credit_accounts
                if account.account_status == "WRITTEN_OFF"
            ]
            if written_off_accounts:
                return FinalDecision(
                    decision="REJECTED",
                    reasons=[f"{len(written_off_accounts)} written-off/defaulted account(s) on credit report"],
                )

            open_disputes = [dispute for dispute in credit_report.disputes if dispute.status == "OPEN"]
            if open_disputes:
                return FinalDecision(
                    decision="MANUAL_REVIEW",
                    reasons=[f"{len(open_disputes)} open dispute(s) on credit report"],
                )

        decision = RISK_BAND_TO_DECISION[risk_assessment.risk_band]
        return FinalDecision(
            decision=decision,
            reasons=[f"Risk score {risk_assessment.total_score} -> {risk_assessment.risk_band} risk band"],
        )
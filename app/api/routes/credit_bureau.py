"""DEMO ONLY: simulates a credit bureau (CIBIL-style) API. Real bureau data
isn't available to individuals/personal projects - banks get it through a
paid, regulated integration. This endpoint stands in for that integration
so the rest of the pipeline (adapter -> risk scoring) can be built and
tested against something realistic. Swapping this for a real bureau API
later would only mean changing the adapter's target URL/auth - not the
CibilReport schema or anything downstream."""

import random

from fastapi import APIRouter

from app.schemas.credit_bureau import (
    CibilReport,
    PersonalInfo,
    CreditScoreInfo,
    CreditAccount,
    CreditEnquiry,
    EmploymentInfo
)

router = APIRouter(prefix="/api/v1/bureau", tags=["Credit Bureau (Demo)"])

LENDERS = ["Sample National Bank", "Sample Finance Ltd", "Fictional Credit Co", "Demo Bank Ltd"]
ACCOUNT_TYPES = ["Home Loan", "Auto Loan", "Personal Loan", "Credit Card", "Two-Wheeler Loan"]

# A hand-crafted "clean" profile for the project's known test applicant, so
# the full pipeline (verification + risk scoring) always has a consistent,
# realistic CLEAN case to test against.
KNOWN_APPLICANTS = {
    "ABCDE1234F": CibilReport(
        personal_information=PersonalInfo(
            name="Rohan Ashok Deshmukh",
            dob="15/08/1990",
            gender="Male",
            pan="ABCDE1234F",
            phone="9876543210",
            email="rohan.deshmukh@example.com",
            addresses=["Flat No. 402, Sunrise Heights, Andheri West, Mumbai, Maharashtra 400058"],
        ),
        credit_score=CreditScoreInfo(
            score=782,
            score_factors=["Long credit history", "Low credit utilization", "No missed payments"],
        ),
        credit_accounts=[
            CreditAccount(
                lender="Sample Finance Ltd",
                account_number="SFL-AUTO-2024-778812",
                account_type="Auto Loan",
                ownership="INDIVIDUAL",
                sanctioned_amount=600000,
                current_balance=342000,
                overdue_amount=0,
                emi=12500,
                interest_rate=9.5,
                open_date="2024-01-15",
                account_status="ACTIVE",
                payment_history=["0"] * 24,
            )
        ],
        enquiries=[
            CreditEnquiry(date="2026-07-01", lender="Sample National Bank", purpose="Home Loan", amount=3500000),
        ],
        employment_information=EmploymentInfo(
            occupation="Senior Software Engineer", income=95000, income_frequency="MONTHLY"
        ),
        disputes=[],
    )
}

def _generate_demo_report(pan: str) -> CibilReport:
    """Deterministically generates a plausible fictional report for any PAN
    not in KNOWN_APPLICANTS, seeded by the PAN itself so the same PAN
    always returns the same report (useful for repeatable testing)."""
    rng = random.Random(pan)

    score = rng.randint(550, 850)
    num_accounts = rng.randint(1, 3)
    accounts = []
    for i in range(num_accounts):
        overdue = rng.choice([0, 0, 0, rng.randint(1000, 20000)])  # mostly clean, occasionally overdue
        accounts.append(
            CreditAccount(
                lender=rng.choice(LENDERS),
                account_number=f"DEMO-{pan[-4:]}-{i}",
                account_type=rng.choice(ACCOUNT_TYPES),
                ownership="INDIVIDUAL",
                sanctioned_amount=rng.choice([200000, 500000, 800000, 1500000]),
                current_balance=rng.randint(10000, 500000),
                overdue_amount=overdue,
                emi=rng.randint(3000, 25000),
                interest_rate=round(rng.uniform(8.5, 14.0), 2),
                open_date="2022-01-01",
                account_status="ACTIVE" if overdue < 15000 else "WRITTEN_OFF",
                payment_history=[rng.choice(["0", "0", "0", "30"]) for _ in range(12)],
            )
        )

    return CibilReport(
        personal_information=PersonalInfo(pan=pan, addresses=[]),
        credit_score=CreditScoreInfo(score=score, score_factors=["Demo-generated profile"]),
        credit_accounts=accounts,
        enquiries=[],
        employment_information=EmploymentInfo(income_frequency="MONTHLY"),
        disputes=[],
    )


@router.get("/credit-report/{pan}", response_model=CibilReport)
def get_credit_report(pan: str):
    """Returns a fictional CIBIL-style report for the given PAN. Known test
    PANs return a hand-crafted profile; anything else gets a deterministic,
    randomly-generated one."""
    return KNOWN_APPLICANTS.get(pan.upper(), _generate_demo_report(pan.upper()))

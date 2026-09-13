from typing import Optional
from pydantic import BaseModel

class PersonalInfo(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    pan: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    addresses: list[str] = []

class CreditScoreInfo(BaseModel):
    score: int # CIBIL-style, typically 300-900
    score_factors: list[str] = []

class CreditAccount(BaseModel):
    lender: str
    account_number: str
    account_type: str  # e.g. "Home Loan", "Auto Loan", "Credit Card" - free text, too varied for an enum
    ownership: str  # "INDIVIDUAL" / "JOINT" / "GUARANTOR"
    sanctioned_amount: Optional[float] = None
    credit_limit: Optional[float] = None
    current_balance: Optional[float] = None
    overdue_amount: Optional[float] = None
    emi: Optional[float] = None
    interest_rate: Optional[float] = None
    open_date: Optional[str] = None
    close_date: Optional[str] = None
    last_payment_date: Optional[str] = None
    account_status: str  # "ACTIVE" / "CLOSED" / "WRITTEN_OFF" / "SETTLED"
    written_off_amount: Optional[float] = None
    settlement_amount: Optional[float] = None
    payment_history: list[str] = []  # DPD per month, e.g. ["0", "0", "30", "0"]


class CreditEnquiry(BaseModel):
    date: str
    lender: str
    purpose: str
    amount: Optional[float] = None


class EmploymentInfo(BaseModel):
    occupation: Optional[str] = None
    income: Optional[float] = None
    income_frequency: Optional[str] = None  # "MONTHLY" / "ANNUAL"


class CreditDispute(BaseModel):
    dispute_id: str
    date: str
    information: str
    status: str  # "OPEN" / "RESOLVED" / "REJECTED"

class CibilReport(BaseModel):
    """A CIBIL-style credit bureau report. Fictional/demo data only - real
    bureau integration would later replace the demo endpoint this is
    fetched from, without changing this schema or anything downstream."""
    personal_information: PersonalInfo
    credit_score: CreditScoreInfo
    credit_accounts: list[CreditAccount] = []
    enquiries: list[CreditEnquiry] = []
    employment_information: EmploymentInfo
    disputes: list[CreditDispute] = []


from typing import Optional, Union
from pydantic import BaseModel, Field


class BaseExtractedFields(BaseModel):
    """Fields common to every document type, regardless of extraction source."""
    full_name: Optional[str] = None
    document_number: Optional[str] = Field(
        None, description="the primary ID number on this document"
    )
    extraction_source: str = "LLM"  # "azure_id_model" or "LLM"


class AadhaarFields(BaseExtractedFields):
    document_number: Optional[str] = Field(None, description="the 12-digit Aadhaar number")
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = Field(None, description="Male, Female, or Other")


class PanFields(BaseExtractedFields):
    document_number: Optional[str] = Field(None, description="the 10-character PAN number")
    date_of_birth: Optional[str] = None
    father_name: Optional[str] = None


class SalarySlipFields(BaseExtractedFields):
    document_number: Optional[str] = Field(
        None, description="the employee ID or employee code printed on the payslip - NOT the PAN, even if a PAN number also appears on the document"
    )
    employer: Optional[str] = None
    designation: Optional[str] = Field(None, description="the applicant's job title")
    pay_period: Optional[str] = Field(None, description="the month this payslip covers, e.g. 'August 2026'")
    gross_salary: Optional[float] = Field(None, description="total salary before any deductions")
    basic_pay: Optional[float] = None
    hra: Optional[float] = Field(None, description="House Rent Allowance component")
    deductions: Optional[float] = Field(None, description="total amount deducted this period (PF, tax, etc.) - a single combined figure, not itemized")
    net_pay: Optional[float] = Field(None, description="take-home pay after all deductions")


class BankStatementFields(BaseExtractedFields):
    document_number: Optional[str] = Field(None, description="the bank account number (same value as account_number)")
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc: Optional[str] = Field(None, description="IFSC code of the account's bank branch")
    statement_period: Optional[str] = None
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    average_monthly_balance: Optional[float] = Field(None, description="the average balance maintained over the statement period, often abbreviated AMB")


class ItrFields(BaseExtractedFields):
    document_number: Optional[str] = Field(
        None, description="leave this null - use acknowledgement_number and pan fields below instead"
    )
    assessment_year: Optional[str] = Field(None, description="e.g. '2025-26'")
    filing_date: Optional[str] = None
    filing_status: Optional[str] = Field(
        None, description="the taxpayer category this return was filed under, e.g. Individual, HUF, Company - NOT marital status"
    )
    gross_total_income: Optional[float] = None
    standard_deduction: Optional[float] = None
    deductions_80c: Optional[float] = None
    deductions_80d: Optional[float] = None
    total_taxable_income: Optional[float] = None
    tax_payable: Optional[float] = Field(None, description="income tax computed on the taxable income, BEFORE health & education cess is added")
    cess: Optional[float] = None
    total_tax_liability: Optional[float] = Field(None, description="tax_payable PLUS cess - the final total tax owed")
    tds_paid: Optional[float] = Field(None, description="Tax Deducted at Source - tax already paid/withheld during the year")
    refund_amount: Optional[float] = None
    acknowledgement_number: Optional[str] = None
    pan: Optional[str] = None


class LoanApplicationFields(BaseExtractedFields):
    document_number: Optional[str] = Field(
        None, description="the loan application/form reference number printed on the form, if any - NOT the applicant's PAN"
    )
    loan_amount_requested: Optional[float] = None
    loan_purpose: Optional[str] = None
    tenure_months: Optional[int] = None
    employment_type: Optional[str] = Field(
        None, description="the applicant's employment category, e.g. Salaried, Self-Employed, or Business - NOT their job title/designation"
    )
    monthly_income: Optional[float] = None
    co_applicant_name: Optional[str] = None
    declared_address: Optional[str] = Field(None, description="the residential address the applicant declared on this form")
    declared_employer: Optional[str] = Field(None, description="the employer name the applicant declared on this form")


class LoanHistoryFields(BaseExtractedFields):
    document_number: Optional[str] = Field(None, description="the existing loan account number")
    lender_name: Optional[str] = None
    loan_type: Optional[str] = None
    sanctioned_amount: Optional[float] = None
    outstanding_amount: Optional[float] = None
    emi_amount: Optional[float] = None
    loan_status: Optional[str] = Field(None, description="e.g. 'Active - paid on time', 'Closed', 'Defaulted'")


ExtractedFieldsUnion = Union[
    AadhaarFields,
    PanFields,
    SalarySlipFields,
    BankStatementFields,
    ItrFields,
    LoanApplicationFields,
    LoanHistoryFields,
]


class DocumentInfo(BaseModel):
    """Represents one document received as part of a loan application."""
    file_name: str
    document_type: str
    status: str
    fields: Optional[ExtractedFieldsUnion] = None


class VerificationCheck(BaseModel):
    """Result of comparing one applicant detail (Name, DOB, etc.) across
    the documents that mention it."""
    field_name: str
    status: str  # "MATCHED" / "MISMATCH" / "MISSING"
    values_found: dict[str, Optional[str]]
    similarity_score: Optional[float] = None
    note: Optional[str] = None


class VerificationReport(BaseModel):
    """All cross-document verification checks for one application, plus an
    overall verdict."""
    checks: list[VerificationCheck]
    overall_status: str  # "CLEAN" or "FLAGGED"


class ApplicationResponse(BaseModel):
    """Represents the structured response returned after processing an application upload."""
    application_id: str
    status: str
    file_name: str
    documents: list[DocumentInfo]
    verification: Optional[VerificationReport] = None


class ExtractedDocument(BaseModel):
    """Represents the clean document extraction result used internally by the application."""
    file_name: str
    page_count: int
    text: str
    tables: list


class DocumentClassificationResult(BaseModel):
    """Represents the document type and evidence produced by the document classifier."""
    document_type: str
    matched_keywords: list[str]
    score: int
    confidence: float
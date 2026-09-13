"""Cross-document verification: rule-based fuzzy/exact matching of applicant
details across the documents in one application, to catch inconsistency
signals (name mismatches, address mismatches, self-declared vs. actual
income, etc). Deliberately rule-based, NOT LLM-based - decisions in this
system must stay deterministic and auditable."""

import re

from dateutil import parser as date_parser
from rapidfuzz import fuzz

from app.schemas.application import (
    AadhaarFields,
    PanFields,
    SalarySlipFields,
    ItrFields,
    LoanApplicationFields,
    VerificationCheck,
    VerificationReport,
)

NAME_MATCH_THRESHOLD = 85
SALARY_MATCH_TOLERANCE_PCT = 10

_HONORIFIC_PATTERN = re.compile(r"^(mr|mrs|ms|dr|shri|smt)\.?\s+", re.IGNORECASE)


def _normalize_for_fuzzy(text: str) -> str:
    """Lowercases and strips honorific prefixes (Mr./Mrs./etc.) before
    fuzzy comparison, so 'ROSHAN ASHOK DESHMUKH' (Azure, all-caps) and
    'Mr. Rohan Ashok Deshmukh' (LLM, mixed-case) compare fairly - the
    difference that's left is the actual OCR spelling variation, not
    casing or a title."""
    text = _HONORIFIC_PATTERN.sub("", text.strip())
    return text.lower()


def _normalize_dob(value: str) -> str | None:
    """Parses a date string in any common format and returns ISO
    (YYYY-MM-DD), so '15/08/1990' and '1990-08-15' compare as equal."""
    try:
        return date_parser.parse(value, dayfirst=True).date().isoformat()
    except (ValueError, TypeError):
        return None


def _normalize_pan(value: str) -> str:
    return value.strip().upper().replace(" ", "")


def _fuzzy_check(field_name: str, values: dict[str, str | None]) -> VerificationCheck:
    """Compares all present text values pairwise using fuzzy similarity
    (case-insensitive, honorifics stripped); MATCHED only if every pair
    clears the threshold."""
    present = {doc: val for doc, val in values.items() if val}

    if len(present) < 2:
        return VerificationCheck(
            field_name=field_name,
            status="MISSING",
            values_found=values,
            note=f"Fewer than 2 documents have a value for {field_name}.",
        )

    pairs = list(present.items())
    scores = [
        fuzz.token_sort_ratio(
            _normalize_for_fuzzy(pairs[i][1]),
            _normalize_for_fuzzy(pairs[j][1]),
        )
        for i in range(len(pairs))
        for j in range(i + 1, len(pairs))
    ]
    min_score = min(scores)

    return VerificationCheck(
        field_name=field_name,
        status="MATCHED" if min_score >= NAME_MATCH_THRESHOLD else "MISMATCH",
        values_found=values,
        similarity_score=min_score,
    )


def _exact_check(field_name: str, values: dict[str, str | None], normalizer) -> VerificationCheck:
    """Compares all present values after normalization; MATCHED only if
    every normalized value is identical."""
    present = {doc: val for doc, val in values.items() if val}

    if len(present) < 2:
        return VerificationCheck(
            field_name=field_name,
            status="MISSING",
            values_found=values,
            note=f"Fewer than 2 documents have a value for {field_name}.",
        )

    normalized = {doc: normalizer(val) for doc, val in present.items()}

    if None in normalized.values():
        return VerificationCheck(
            field_name=field_name,
            status="MISMATCH",
            values_found=values,
            note=f"Could not parse one or more {field_name} values.",
        )

    unique_values = set(normalized.values())
    return VerificationCheck(
        field_name=field_name,
        status="MATCHED" if len(unique_values) == 1 else "MISMATCH",
        values_found=values,
    )


def _salary_check(values: dict[str, float | None]) -> VerificationCheck:
    present = {doc: val for doc, val in values.items() if val is not None}
    display_values = {doc: (str(val) if val is not None else None) for doc, val in values.items()}

    if len(present) < 2:
        return VerificationCheck(
            field_name="Salary",
            status="MISSING",
            values_found=display_values,
            note="Fewer than 2 documents have a salary figure.",
        )

    numbers = list(present.values())
    higher, lower = max(numbers), min(numbers)
    pct_diff = ((higher - lower) / higher) * 100 if higher else 0

    return VerificationCheck(
        field_name="Salary",
        status="MATCHED" if pct_diff <= SALARY_MATCH_TOLERANCE_PCT else "MISMATCH",
        values_found=display_values,
        similarity_score=round(100 - pct_diff, 2),
    )


class CrossDocumentVerifier:
    """Runs all rule-based cross-document checks for one application."""

    def verify(self, documents_by_type: dict[str, object]) -> VerificationReport:
        aadhaar: AadhaarFields | None = documents_by_type.get("AADHAAR_CARD")
        pan: PanFields | None = documents_by_type.get("PAN_CARD")
        salary_slip: SalarySlipFields | None = documents_by_type.get("SALARY_SLIP")
        itr: ItrFields | None = documents_by_type.get("ITR_ACKNOWLEDGEMENT")
        loan_application: LoanApplicationFields | None = documents_by_type.get("LOAN_APPLICATION")

        # Name - compare full_name across every document that has one, not just a pair
        name_values = {
            doc_type: getattr(doc, "full_name", None)
            for doc_type, doc in documents_by_type.items()
            if doc is not None and getattr(doc, "full_name", None)
        }

        checks = [
            _fuzzy_check("Name", name_values),
            _exact_check(
                "DOB",
                {
                    "AADHAAR_CARD": aadhaar.date_of_birth if aadhaar else None,
                    "PAN_CARD": pan.date_of_birth if pan else None,
                },
                _normalize_dob,
            ),
            _exact_check(
                "PAN",
                {
                    "PAN_CARD": pan.document_number if pan else None,
                    "ITR_ACKNOWLEDGEMENT": itr.pan if itr else None,
                },
                _normalize_pan,
            ),
            _fuzzy_check(
                "Address",
                {
                    "AADHAAR_CARD": aadhaar.address if aadhaar else None,
                    "LOAN_APPLICATION": loan_application.declared_address if loan_application else None,
                },
            ),
            _fuzzy_check(
                "Employer",
                {
                    "SALARY_SLIP": salary_slip.employer if salary_slip else None,
                    "LOAN_APPLICATION": loan_application.declared_employer if loan_application else None,
                },
            ),
            _salary_check(
                {
                    "SALARY_SLIP": salary_slip.gross_salary if salary_slip else None,
                    "LOAN_APPLICATION": loan_application.monthly_income if loan_application else None,
                }
            ),
        ]

        overall_status = "FLAGGED" if any(check.status == "MISMATCH" for check in checks) else "CLEAN"
        return VerificationReport(checks=checks, overall_status=overall_status)
"""Defines the keywords used to identify each supported document type,
with an LLM-based fallback for documents whose keyword-match confidence
is too low (different language, unusual phrasing/format, etc.)."""

import json

from app.adapters.openrouter import openrouter
from app.adapters.logger import logger
from app.prompts import render_prompt
from app.schemas.application import DocumentClassificationResult

CLASSIFICATION_THRESHOLD = 0.60

DOCUMENT_RULES = {
    "PAN_CARD": [
        "permanent account number",
        "income tax department",
        "pan",
    ],
    "AADHAAR_CARD": [
        "aadhaar",
        "unique identification authority",
        "government of india",
    ],
    "SALARY_SLIP": [
        "employee id",
        "earnings",
        "deductions",
        "net pay",
    ],
    "ITR_ACKNOWLEDGEMENT": [
        "income tax return",
        "acknowledgement number",
        "assessment year",
    ],
    "BANK_STATEMENT": [
        "bank statement",
        "account statement",
        "statement period",
        "opening balance",
        "closing balance",
        "ifsc",
        "narration",
        "account holder",
        "withdrawal",
    ],
    "LOAN_APPLICATION": [
        "loan application",
        "loan amount",
        "applicant",
    ],
    "EXISTING_LOAN_HISTORY": [
        "loan account",
        "outstanding amount",
        "emi",
        "loan history",
    ],
}

# Used only for the LLM fallback prompt - includes the two types that have
# no keyword rules (they're never expected in a real applicant ZIP, but the
# LLM should still be able to name them correctly instead of guessing wrong).
DOCUMENT_TYPE_DESCRIPTIONS = {
    "PAN_CARD": "Indian Permanent Account Number (PAN) card, issued by the Income Tax Department",
    "AADHAAR_CARD": "Indian Aadhaar identity card, issued by UIDAI",
    "SALARY_SLIP": "a monthly payslip/salary slip showing an employee's earnings and deductions",
    "ITR_ACKNOWLEDGEMENT": "Income Tax Return acknowledgement/filing receipt",
    "BANK_STATEMENT": "a bank account statement showing transactions and balances",
    "LOAN_APPLICATION": "a loan application form filled out by the applicant",
    "EXISTING_LOAN_HISTORY": "a record of the applicant's existing/past loans",
    "CREDIT_INFORMATION": "a credit bureau report (e.g. CIBIL) showing credit score and history",
    "GROUND_TRUTH_PROFILE": "an internal testing/reference document - not a real applicant document",
}

class DocumentClassifier:
    """Classifies a document: fast keyword match first, falling back to an
    LLM classifier only when the keyword match confidence is too low."""
    def _classify_by_keywords(self, text: str) -> DocumentClassificationResult:
        text = text.lower()

        scores = {}
        matched_keywords = {}

        for document_type, keywords in DOCUMENT_RULES.items():
            score = 0
            matches = []

            for keyword in keywords:
                if keyword in text:
                    score += 1
                    matches.append(keyword)

            scores[document_type] = score
            matched_keywords[document_type] = matches

        best_document_type = max(scores, key=scores.get)
        confidence = scores[best_document_type] / len(DOCUMENT_RULES[best_document_type])

        return DocumentClassificationResult(
            document_type=best_document_type,
            matched_keywords=matched_keywords[best_document_type],
            score=scores[best_document_type],
            confidence=confidence,
        )

    async def _classify_via_llm(self, text: str) -> DocumentClassificationResult:
        document_types = "\n".join(
            f"-{doc_type}: {description}"
            for doc_type, description in DOCUMENT_TYPE_DESCRIPTIONS.items()
        )
        prompt = render_prompt(
            "classify_document.jinja2",
            document_types=document_types,
            raw_text=text[:400] # classification doesn't whole document
        )
        content = await openrouter.chat(prompt=prompt, json_mode=True)
        data = json.loads(content)

        return DocumentClassificationResult(
            document_type=data.get("document_type", "UNKNOWN"),
            matched_keywords=[],
            score=0,
            confidence=float(data.get("confidence", 0.0))
        )

    async def classify(self, text: str) -> DocumentClassificationResult:
        """Determines the document type. Tries the fast, free keyword match
        first; only calls the LLM (slower, costs a request) if the keyword
        confidence is below CLASSIFICATION_THRESHOLD."""
        keyword_result = self._classify_by_keywords(text)

        if keyword_result.confidence >= CLASSIFICATION_THRESHOLD:
            return keyword_result

        logger.info(f"[Classification] keyword confidence too low ({keyword_result.confidence:.2f}), falling back to LLM")
        try:
            return await self._classify_via_llm(text)
        except Exception as error:
            logger.error(f"[classification] LLM fallback failed ({error!r}), returning UNKNOWN")
            return DocumentClassificationResult(
                document_type="UNKNOWN",
                matched_keywords=keyword_result.matched_keywords,
                score=keyword_result.score,
                confidence=0.0
            )
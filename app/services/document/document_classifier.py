"""Defines the keywords used to identify each supported document type."""

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
        "account statement",
        "transaction date",
        "withdrawal",
        "deposit",
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

class DocumentClassifier:
    """Classifies a document based on keyword matches in its extracted text."""

    def classify(self, text: str) -> DocumentClassificationResult:
        """Determines the document type with the highest keyword match score."""
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

        best_document_type = max(
            scores,
            key=scores.get
        )

        confidence = scores[best_document_type] / len(
        DOCUMENT_RULES[best_document_type]
        )

        if confidence < CLASSIFICATION_THRESHOLD:
                return DocumentClassificationResult(
                document_type="UNKNOWN",
                matched_keywords=matched_keywords[best_document_type],
                score=scores[best_document_type],
                confidence=0.0
            )

        return DocumentClassificationResult(
            document_type=best_document_type,
            matched_keywords=matched_keywords[best_document_type],
            score=scores[best_document_type],
            confidence=confidence
        )
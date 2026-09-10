from app.services.document.document_extractor import DocumentExtractor
from app.services.document.document_classifier import DocumentClassifier


# Tests document classification using text extracted from real documents through Azure.
def test_real_document_classification():
    extractor = DocumentExtractor()
    classifier = DocumentClassifier()

    file_paths = [
        "data/extracted/LN-8B20CA29/LOS-Data/SALARY_SLIP.pdf",
        "data/extracted/LN-8B20CA29/LOS-Data/PAN_CARD.pdf",
    ]

    extracted_documents = extractor.extract_documents(file_paths)

    for document in extracted_documents:
        document_type = classifier.classify(document.text)

        print(
            f"{document.file_name} → {document_type}"
        )


test_real_document_classification()
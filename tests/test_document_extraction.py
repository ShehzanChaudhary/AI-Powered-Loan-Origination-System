from app.services.document.document_extractor import DocumentExtractor


# Tests extraction of multiple documents through the document extraction service.
def test_multiple_document_extraction():
    extractor = DocumentExtractor()

    file_paths = [
    "data/extracted/LN-8B20CA29/LOS-Data/SALARY_SLIP.pdf",
    "data/extracted/LN-8B20CA29/LOS-Data/PAN_CARD.pdf",
    ]

    extracted_documents = extractor.extract_documents(file_paths)

    print("\nMultiple document extraction successful!")
    print("Documents extracted:", len(extracted_documents))

    for document in extracted_documents:
        print(
            f"- {document.file_name} | "
            f"Pages: {document.page_count} | "
            f"Text: {len(document.text)} chars | "
            f"Tables: {len(document.tables)}"
        )


test_multiple_document_extraction()
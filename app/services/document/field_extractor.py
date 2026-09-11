"""Routes each document to the right extraction strategy:
  - Aadhaar/PAN -> Azure's prebuilt-idDocument model
  - everything else, or if the above fails -> LLM extraction"""

import json

from app.adapters.document_intelligence import document_intelligence
from app.adapters.openrouter import openrouter
from app.prompts import render_prompt
from app.schemas.application import ExtractedFields

ID_DOCUMENT_TYPES = {"ADHAAR_CARD", "PAN_CARD"}

async def extract_fields_via_azure_id_model(file_path: str) -> ExtractedFields | None:
    azure_result = await document_intelligence.analyze("prebuilt-idDocument", file_path)

    if not azure_result.documents:
        return None

    fields = azure_result.documents[0].fields

    def _field(name: str) -> str | None:
        field = fields.get(name)
        return field.content if field and field.content else None

    first_name = _field("FirstName")
    last_name = _field("LastName")
    full_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else None

    return ExtractedFields(
        full_name=full_name,
        date_of_birth=_field("DateOfBirth"),
        document_number=_field("DocumentNumber"),
        address=_field("Address"),
        extraction_source="azure_id_model"
    )

async def extract_fields_via_llm(document_type: str, raw_text: str) -> ExtractedFields:
    prompt = render_prompt("extract_fields.jinja2", document_type=document_type, raw_text=raw_text)
    content = await openrouter.chat(prompt, json_mode=True)
    data = json.loads(content)
    return ExtractedFields(**data, extraction_source="LLM")

async def extract_structured_fields(file_path: str, document_type: str, raw_text: str) -> ExtractedFields:
    if document_type in ID_DOCUMENT_TYPES:
        try:
            azure_result = await extract_fields_via_azure_id_model(file_path)
            if azure_result is not None:
                return azure_result
        except Exception:
            pass

    return await extract_fields_via_llm(document_type, raw_text)
"""Routes each document to the right extraction strategy:
  - Aadhaar/PAN -> Azure's prebuilt-idDocument model, falls back to LLM
    (using the matching schema) if Azure fails
  - everything else -> LLM extraction, using a document-type-specific
    schema + dynamically built prompt"""

import json
from pathlib import Path
from typing import get_args, get_origin, Union

from pydantic import BaseModel

from app.adapters.document_intelligence import document_intelligence
from app.adapters.openrouter import openrouter
from app.adapters.logger import logger
from app.prompts import render_prompt
from app.schemas.application import (
    AadhaarFields,
    PanFields,
    SalarySlipFields,
    BankStatementFields,
    ItrFields,
    LoanApplicationFields,
    LoanHistoryFields,
)

ID_DOCUMENT_TYPES = {"AADHAAR_CARD", "PAN_CARD"}

# Maps a classified document type to the Pydantic schema describing exactly
# what fields matter for that type. Keys MUST exactly match the
# document_type strings produced by DocumentClassifier (see DOCUMENT_RULES
# in document_classifier.py) - not the ZIP file names.
DOCUMENT_TYPE_SCHEMAS: dict[str, type[BaseModel]] = {
    "AADHAAR_CARD": AadhaarFields,
    "PAN_CARD": PanFields,
    "SALARY_SLIP": SalarySlipFields,
    "BANK_STATEMENT": BankStatementFields,
    "ITR_ACKNOWLEDGEMENT": ItrFields,
    "LOAN_APPLICATION": LoanApplicationFields,
    "EXISTING_LOAN_HISTORY": LoanHistoryFields,
}

_TYPE_LABELS = {
    str: "string or null",
    int: "integer or null",
    float: "number or null",
}


def _field_type_label(annotation) -> str:
    """Turns a Pydantic field annotation (e.g. Optional[float]) into a
    human-readable hint for the prompt, e.g. 'number or null'."""
    if get_origin(annotation) is Union:
        args = [a for a in get_args(annotation) if a is not type(None)]
        if args:
            annotation = args[0]
    return _TYPE_LABELS.get(annotation, "string or null")


def build_json_schema_snippet(schema_cls: type[BaseModel]) -> str:
    """Builds the JSON-shaped schema block for the prompt, one line per
    field in the given schema, with an inline comment for any field whose
    meaning isn't obvious from its name alone. Skips 'extraction_source'
    since that's set by us after the fact, not something the LLM fills in."""
    lines = []
    for name, field in schema_cls.model_fields.items():
        if name == "extraction_source":
            continue
        line = f'  "{name}": {_field_type_label(field.annotation)}'
        if field.description:
            line += f"  // {field.description}"
        lines.append(line)
    return "{\n" + ",\n".join(lines) + "\n}"


async def extract_fields_via_azure_id_model(file_path: str, schema_cls: type[BaseModel]):
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

    common = dict(
        full_name=full_name,
        document_number=_field("DocumentNumber"),
        extraction_source="azure_id_model",
    )

    if schema_cls is AadhaarFields:
        return AadhaarFields(
            **common,
            date_of_birth=_field("DateOfBirth"),
            address=_field("Address"),
            gender=_field("Gender"),
        )
    if schema_cls is PanFields:
        return PanFields(
            **common,
            date_of_birth=_field("DateOfBirth"),
            father_name=_field("FatherName"),
        )
    return None


async def extract_fields_via_llm(document_type: str, schema_cls: type[BaseModel], raw_text: str):
    schema_json = build_json_schema_snippet(schema_cls)
    prompt = render_prompt(
        "extract_fields.jinja2",
        document_type=document_type,
        schema_json=schema_json,
        raw_text=raw_text,
    )
    content = await openrouter.chat(prompt, json_mode=True)
    data = json.loads(content)
    return schema_cls(**data, extraction_source="LLM")


async def extract_structured_fields(file_path: str, document_type: str, raw_text: str):
    schema_cls = DOCUMENT_TYPE_SCHEMAS.get(document_type)
    if schema_cls is None:
        logger.info(f"[field-extraction] No schema mapped for document_type={document_type}, skipping field extraction.")
        return None

    if document_type in ID_DOCUMENT_TYPES:
        try:
            azure_result = await extract_fields_via_azure_id_model(file_path, schema_cls)
            if azure_result is not None:
                return azure_result
        except Exception as error:
            logger.info(f"[field-extraction] {Path(file_path).name} azure_id_model failed ({error!r}), falling back to LLM")

    return await extract_fields_via_llm(document_type, schema_cls, raw_text)
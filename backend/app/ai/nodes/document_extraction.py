from typing import Dict, Any
from app.ai.state import AgentState
from app.ai.prompts.document_extraction import (
    DOCUMENT_EXTRACTION_SYSTEM_PROMPT,
    build_document_extraction_user_prompt,
    ExtractedComplaintData,
)
from app.services.groq_service import groq_service
from app.core.logging_config import logger


async def document_extract_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node for processing uploaded document text and extracting
    structured pharmaceutical complaint attributes via Groq gemma2-9b-it.
    """
    logger.info("Executing real document_extract_node workflow branch")
    
    document_text = state.get("document_text")
    document_metadata = state.get("document_metadata") or {}

    if not document_text or not document_text.strip():
        logger.warning("Document extraction node called without document text.")
        return {
            "error": "No readable text extracted from document.",
            "response_message": "I could not extract readable text from this document. Please upload a text-based PDF or supported TXT/EML document.",
            "updated_fields": [],
        }

    try:
        user_prompt = build_document_extraction_user_prompt(document_text, document_metadata)
        messages = [
            {"role": "system", "content": DOCUMENT_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        logger.info(f"Calling GroqService to extract complaint data from document '{document_metadata.get('file_name', 'file')}'...")
        extracted: ExtractedComplaintData = await groq_service.generate_structured(
            messages=messages,
            response_model=ExtractedComplaintData,
            temperature=0.0,
        )

        extracted_dict = extracted.model_dump()
        current_complaint = {k: v for k, v in extracted_dict.items() if v is not None}
        updated_fields = list(current_complaint.keys())

        # Construct friendly summary message highlighting missing critical fields if any
        missing = []
        if not current_complaint.get("batch_number"):
            missing.append("batch number")
        if not current_complaint.get("expiry_date"):
            missing.append("expiry date")

        response_msg = "I extracted the complaint information from the uploaded document and populated the complaint form. I also generated an AI-assisted preliminary risk assessment."
        if missing:
            response_msg += f" Note: {', '.join(missing)} was not provided in the document and remains empty for review."

        logger.info(f"Document extraction successful. Extracted fields: {list(current_complaint.keys())}")

        return {
            "current_complaint": current_complaint,
            "updated_fields": updated_fields,
            "response_message": response_msg,
        }

    except Exception as e:
        logger.warning(f"Groq document extraction failed in document_extract_node ({e}). Utilizing fallback rule-based NLP extraction.")
        from app.ai.nodes.fallback_extractor import fallback_extract_complaint_data

        extracted_dict = fallback_extract_complaint_data(document_text)
        current_complaint = {k: v for k, v in extracted_dict.items() if v is not None}
        updated_fields = list(current_complaint.keys())

        missing = []
        if not current_complaint.get("batch_number"):
            missing.append("batch number")
        if not current_complaint.get("expiry_date"):
            missing.append("expiry date")

        response_msg = "I extracted the complaint information from the uploaded document and populated the complaint form."
        if missing:
            response_msg += f" Note: {', '.join(missing)} was not provided in the document and remains empty for review."

        return {
            "current_complaint": current_complaint,
            "updated_fields": updated_fields,
            "response_message": response_msg,
        }


from typing import Dict, Any
from app.ai.state import AgentState
from app.ai.prompts.log_complaint import LOG_COMPLAINT_SYSTEM_PROMPT, ExtractedComplaintData
from app.services.groq_service import groq_service
from app.core.logging_config import logger


async def log_complaint_node(state: AgentState) -> Dict[str, Any]:
    """
    Log Complaint Node.
    Uses Groq LLM (gemma2-9b-it via GroqService) to extract structured pharmaceutical
    complaint information from natural language messages into ComplaintData schema.
    Populates state['current_complaint'] and state['updated_fields'].
    """
    messages = state.get("messages", [])
    if not messages:
        logger.info("Log complaint node: No messages provided.")
        return {"response_message": "No complaint text provided for logging."}

    last_message = messages[-1].get("content", "").strip()
    if not last_message:
        return {"response_message": "Empty complaint text provided."}

    logger.info(f"Log complaint node processing extraction for: '{last_message[:60]}...'")

    llm_messages = [
        {"role": "system", "content": LOG_COMPLAINT_SYSTEM_PROMPT},
        {"role": "user", "content": last_message},
    ]

    try:
        extracted_data: ExtractedComplaintData = await groq_service.generate_structured(
            messages=llm_messages,
            response_model=ExtractedComplaintData,
            operation="log_complaint_extraction",
        )

        extracted_dict = extracted_data.model_dump()
        updated_fields = [k for k, v in extracted_dict.items() if v is not None]

        logger.info(f"Log complaint node extracted {len(updated_fields)} fields: {updated_fields}")

        # Construct conversational response summary
        summary_items = []
        if extracted_dict.get("customer_name"):
            summary_items.append(f"Customer: {extracted_dict['customer_name']}")
        if extracted_dict.get("product_name"):
            prod = extracted_dict["product_name"]
            if extracted_dict.get("strength_grade"):
                prod += f" ({extracted_dict['strength_grade']})"
            summary_items.append(f"Product: {prod}")
        if extracted_dict.get("batch_number"):
            summary_items.append(f"Batch: {extracted_dict['batch_number']}")

        summary_str = ", ".join(summary_items) if summary_items else "complaint details"
        response_msg = f"Successfully recorded {summary_str}. The complaint form has been populated."

        return {
            "current_complaint": extracted_dict,
            "updated_fields": updated_fields,
            "response_message": response_msg,
        }

    except Exception as e:
        logger.error(f"Groq complaint extraction failed in log_complaint_node: {e}", exc_info=True)
        return {
            "error": "Failed to extract complaint details via AI.",
            "response_message": "I could not automatically extract the complaint details. Please verify your message or enter fields manually.",
        }

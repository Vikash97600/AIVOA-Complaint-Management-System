from typing import Dict, Any
from app.ai.state import AgentState, Intent
from app.core.logging_config import logger

def response_synthesis_node(state: AgentState) -> Dict[str, Any]:
    """
    Formulates the final response returned to the Copilot.
    Uses deterministic placeholder responses for Prompt 5 architecture testing.
    """
    intent = state.get("intent", Intent.UNKNOWN)
    existing_msg = state.get("response_message")

    logger.info(f"Executing response_synthesis_node for intent: {intent.value if isinstance(intent, Intent) else intent}")

    if existing_msg:
        final_msg = existing_msg
    elif intent == Intent.LOG_COMPLAINT:
        final_msg = "Log Complaint workflow selected. Form will be populated once LLM extraction is connected."
    elif intent == Intent.EDIT_COMPLAINT:
        final_msg = "Edit Complaint workflow selected. Target fields will be updated once LLM extraction is connected."
    elif intent == Intent.DOCUMENT_EXTRACTION:
        final_msg = "Document Extraction workflow selected. PDF details will be extracted once document processor is connected."
    else:
        final_msg = "AIVOA Copilot is ready. How can I assist with your customer complaint today?"

    return {
        "response_message": final_msg
    }

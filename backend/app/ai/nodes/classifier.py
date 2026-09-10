from typing import Dict, Any
from app.ai.state import AgentState, Intent
from app.core.logging_config import logger

def classifier_node(state: AgentState) -> Dict[str, Any]:
    """
    Temporary deterministic classifier node used to validate LangGraph routing.
    TODO: Replace with Groq-powered intent classification in Prompt 6.
    """
    messages = state.get("messages", [])
    if not messages:
        logger.info("Classifier node: No messages provided. Defaulting to UNKNOWN.")
        return {"intent": Intent.UNKNOWN}

    last_message = messages[-1].get("content", "").lower()
    logger.info(f"Classifier node evaluating message: '{last_message}'")

    if any(k in last_message for k in ["edit", "change", "correct", "update", "sorry, batch", "batch number is"]):
        detected_intent = Intent.EDIT_COMPLAINT
    elif any(k in last_message for k in ["upload", "pdf", "document", "extract information from this pdf"]):
        detected_intent = Intent.DOCUMENT_EXTRACTION
    elif any(k in last_message for k in ["log", "reported", "discolored", "capsules", "complaint", "apollo pharmacy"]):
        detected_intent = Intent.LOG_COMPLAINT
    else:
        detected_intent = Intent.UNKNOWN

    logger.info(f"Classifier node selected intent: {detected_intent.value}")
    return {"intent": detected_intent}

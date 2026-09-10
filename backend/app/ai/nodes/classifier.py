from typing import Dict, Any
from app.ai.state import AgentState, Intent
from app.ai.prompts.classifier import CLASSIFIER_SYSTEM_PROMPT, ClassifierOutput
from app.services.groq_service import groq_service
from app.core.ai_exceptions import LLMBaseError
from app.core.logging_config import logger


async def classifier_node(state: AgentState) -> Dict[str, Any]:
    """
    Groq-powered intent classifier node for LangGraph.
    Classifies user message intent into LOG_COMPLAINT, EDIT_COMPLAINT,
    DOCUMENT_EXTRACTION, or UNKNOWN using gemma2-9b-it via GroqService.
    Falls back gracefully to keyword heuristic if Groq is unconfigured or unavailable.
    """
    messages = state.get("messages", [])
    if not messages:
        logger.info("Classifier node: No messages provided. Defaulting to UNKNOWN.")
        return {"intent": Intent.UNKNOWN}

    last_message = messages[-1].get("content", "").strip()
    if not last_message:
        return {"intent": Intent.UNKNOWN}

    logger.info(f"Classifier node classifying user message: '{last_message[:60]}...'")

    # Format LLM messages payload
    llm_messages = [
        {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
        {"role": "user", "content": last_message},
    ]

    try:
        classifier_res: ClassifierOutput = await groq_service.generate_structured(
            messages=llm_messages,
            response_model=ClassifierOutput,
            operation="classify_intent",
        )
        logger.info(f"Groq classifier node selected intent: {classifier_res.intent.value}")
        return {"intent": classifier_res.intent}

    except Exception as e:
        logger.warning(
            f"Groq LLM intent classification failed ({e}). Utilizing fallback rule-based classification."
        )
        msg_lower = last_message.lower()
        if any(k in msg_lower for k in ["edit", "change", "correct", "update", "sorry, batch", "batch number is"]):
            fallback_intent = Intent.EDIT_COMPLAINT
        elif any(k in msg_lower for k in ["upload", "pdf", "document", "extract information from this pdf"]):
            fallback_intent = Intent.DOCUMENT_EXTRACTION
        elif any(k in msg_lower for k in ["log", "reported", "discolored", "capsules", "complaint", "apollo pharmacy"]):
            fallback_intent = Intent.LOG_COMPLAINT
        else:
            fallback_intent = Intent.UNKNOWN

        logger.info(f"Rule-based fallback classifier selected intent: {fallback_intent.value}")
        return {"intent": fallback_intent}

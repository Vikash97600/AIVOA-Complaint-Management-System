from typing import Dict, Any
from app.ai.state import AgentState, Intent
from app.core.logging_config import logger


def response_synthesis_node(state: AgentState) -> Dict[str, Any]:
    """
    Formulates the final conversational response returned to the Copilot.
    Incorporates preliminary risk assessment summary when available.
    """
    intent = state.get("intent", Intent.UNKNOWN)
    existing_msg = state.get("response_message")
    risk_data = state.get("risk_assessment")

    logger.info(
        f"Executing response_synthesis_node for intent: {intent.value if isinstance(intent, Intent) else intent}"
    )

    if existing_msg:
        final_msg = existing_msg
        if risk_data and isinstance(risk_data, dict) and risk_data.get("severity_suggested"):
            severity = risk_data.get("severity_suggested")
            final_msg += f" A preliminary AI quality risk assessment has also been generated (Suggested Severity: {severity})."
    elif intent == Intent.LOG_COMPLAINT:
        final_msg = "Complaint logged successfully."
        if risk_data and isinstance(risk_data, dict) and risk_data.get("severity_suggested"):
            final_msg += f" Preliminary risk assessment generated (Suggested Severity: {risk_data['severity_suggested']})."
    elif intent == Intent.EDIT_COMPLAINT:
        final_msg = "Complaint updated successfully."
        if risk_data and isinstance(risk_data, dict) and risk_data.get("severity_suggested"):
            final_msg += f" Risk assessment updated (Suggested Severity: {risk_data['severity_suggested']})."
    elif intent == Intent.DOCUMENT_EXTRACTION:
        final_msg = "Document processed successfully."
        if risk_data and isinstance(risk_data, dict) and risk_data.get("severity_suggested"):
            final_msg += f" Risk assessment generated (Suggested Severity: {risk_data['severity_suggested']})."
    else:
        final_msg = "AIVOA Copilot is ready. How can I assist with your customer complaint today?"

    return {"response_message": final_msg}

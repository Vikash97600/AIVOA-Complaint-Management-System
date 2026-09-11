from typing import Dict, Any
from app.ai.state import AgentState
from app.services.summary_service import generate_complaint_summary
from app.core.logging_config import logger

async def summary_node(state: AgentState) -> Dict[str, Any]:
    """
    Generates executive complaint summary using Groq gemma2-9b-it.
    """
    logger.info("Executing summary_node...")
    current_complaint = state.get("current_complaint") or {}
    risk_assessment = state.get("risk_assessment")

    res = await generate_complaint_summary(current_complaint, risk_assessment)
    sum_dict = res.model_dump(mode="json")

    return {
        "summary_result": sum_dict,
        "response_message": f"Executive Complaint Summary: {res.summary_text}",
    }

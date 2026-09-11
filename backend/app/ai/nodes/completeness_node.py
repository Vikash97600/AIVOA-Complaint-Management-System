from typing import Dict, Any
from app.ai.state import AgentState
from app.services.completeness_service import calculate_completeness
from app.core.logging_config import logger

async def completeness_node(state: AgentState) -> Dict[str, Any]:
    """
    Evaluates complaint detail completeness using deterministic completeness calculator.
    """
    logger.info("Executing completeness_node...")
    current_complaint = state.get("current_complaint") or {}
    res = calculate_completeness(current_complaint)

    msg = (
        f"Complaint Completeness Assessment: {res.completion_score}% ({res.status_label}). "
        + (f"Missing important details: {', '.join(res.missing_fields)}." if res.missing_fields else "All primary fields are filled.")
    )

    return {
        "completeness_result": res.model_dump(mode="json"),
        "response_message": msg,
    }

from typing import Dict, Any
from app.ai.state import AgentState
from app.services.duplicate_detection_service import detect_duplicate_complaints
from app.core.logging_config import logger

async def duplicate_node(state: AgentState, db: Any = None) -> Dict[str, Any]:
    """
    Evaluates potential candidate duplicate complaints in database.
    """
    logger.info("Executing duplicate_node...")
    current_complaint = state.get("current_complaint") or {}
    complaint_id = state.get("complaint_id")

    if db:
        res = await detect_duplicate_complaints(db, current_complaint, complaint_id)
        dup_dict = res.model_dump(mode="json")
        msg = res.summary_reasoning
    else:
        dup_dict = {
            "is_duplicate": False,
            "confidence": 0.0,
            "matched_complaint_id": None,
            "matched_qms_reference": None,
            "matches": [],
            "summary_reasoning": "Duplicate search requires database context.",
        }
        msg = "Duplicate complaint check completed."

    return {
        "duplicate_result": dup_dict,
        "response_message": msg,
    }

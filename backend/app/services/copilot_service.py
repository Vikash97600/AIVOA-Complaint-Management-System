import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.state import AgentState, Intent
from app.schemas.copilot import CopilotMessageRequest, CopilotResponse
from app.schemas.complaint import ComplaintResponse, ComplaintCreate, ComplaintUpdate
from app.services import complaint_service
from app.core.logging_config import logger


async def process_copilot_message(
    db: AsyncSession,
    request: CopilotMessageRequest
) -> CopilotResponse:
    """
    Orchestrates user messages through the LangGraph AI Copilot state graph
    and persists/updates DRAFT complaints in MySQL database.
    """
    current_complaint_dict: Optional[Dict[str, Any]] = None
    existing_complaint_obj: Optional[ComplaintResponse] = None

    # Fetch active complaint if complaint_id is provided
    if request.complaint_id:
        try:
            complaint_entity = await complaint_service.get_complaint_by_id(db, request.complaint_id)
            existing_complaint_obj = ComplaintResponse.model_validate(complaint_entity)
            current_complaint_dict = existing_complaint_obj.model_dump(mode="json")
        except Exception as e:
            logger.warning(f"Could not load active complaint '{request.complaint_id}' for Copilot context: {e}")

    # Construct initial AgentState
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": request.message}],
        "complaint_id": request.complaint_id,
        "current_complaint": current_complaint_dict,
        "updated_fields": [],
    }

    try:
        logger.info(f"Invoking AIVOA LangGraph Agent for message: '{request.message[:50]}...'")
        from app.ai.graph import compiled_graph

        final_state: AgentState = await compiled_graph.ainvoke(initial_state)

        detected_intent = final_state.get("intent", Intent.UNKNOWN)
        intent_str = detected_intent.value if isinstance(detected_intent, Intent) else str(detected_intent)
        response_msg = final_state.get("response_message") or "AIVOA Copilot request processed."
        extracted_complaint = final_state.get("current_complaint")
        updated_fields = final_state.get("updated_fields") or []
        err_msg = final_state.get("error")

        # Database Persistence: Create or Update DRAFT complaint
        if extracted_complaint and isinstance(extracted_complaint, dict):
            try:
                # Filter out None values or construct valid schema input
                clean_payload = {k: v for k, v in extracted_complaint.items() if v is not None}
                
                if request.complaint_id:
                    # Update active existing draft
                    update_in = ComplaintUpdate(**clean_payload)
                    saved_entity = await complaint_service.update_complaint(
                        db, request.complaint_id, update_in
                    )
                    existing_complaint_obj = ComplaintResponse.model_validate(saved_entity)
                    logger.info(f"Updated active complaint ID '{request.complaint_id}' from Copilot flow.")
                elif detected_intent == Intent.LOG_COMPLAINT and clean_payload:
                    # Create new DRAFT complaint
                    create_in = ComplaintCreate(**clean_payload)
                    saved_entity = await complaint_service.create_complaint(db, create_in)
                    existing_complaint_obj = ComplaintResponse.model_validate(saved_entity)
                    logger.info(f"Persisted new DRAFT complaint ID '{saved_entity.id}' from Log Complaint AI workflow.")
            except Exception as db_err:
                logger.error(f"Failed to persist complaint data to database: {db_err}", exc_info=True)
                err_msg = err_msg or "Failed to save complaint state to database."

        return CopilotResponse(
            message=response_msg,
            intent=intent_str,
            complaint=existing_complaint_obj,
            risk_assessment=None,
            updated_fields=updated_fields,
            error=err_msg,
        )

    except Exception as e:
        logger.error(f"LangGraph execution failed for message '{request.message}': {e}", exc_info=True)
        return CopilotResponse(
            message="I couldn't process the request due to an internal workflow error.",
            intent=Intent.UNKNOWN.value,
            complaint=existing_complaint_obj,
            risk_assessment=None,
            updated_fields=[],
            error="AI workflow execution failed",
        )

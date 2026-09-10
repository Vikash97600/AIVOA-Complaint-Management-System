from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.graph import compiled_graph
from app.ai.state import AgentState, Intent
from app.schemas.copilot import CopilotMessageRequest, CopilotResponse
from app.schemas.complaint import ComplaintResponse
from app.services import complaint_service
from app.core.logging_config import logger

async def process_copilot_message(
    db: AsyncSession,
    request: CopilotMessageRequest
) -> CopilotResponse:
    """
    Orchestrates user messages through the LangGraph AI Copilot state graph.
    """
    current_complaint_dict: Optional[Dict[str, Any]] = None
    existing_complaint_obj: Optional[ComplaintResponse] = None

    # Fetch existing complaint if complaint_id is provided
    if request.complaint_id:
        try:
            complaint_entity = await complaint_service.get_complaint_by_id(db, request.complaint_id)
            existing_complaint_obj = ComplaintResponse.model_validate(complaint_entity)
            current_complaint_dict = existing_complaint_obj.model_dump(mode="json")
        except Exception as e:
            logger.warning(f"Could not load active complaint '{request.complaint_id}' for Copilot context: {e}")

    # Build initial LangGraph AgentState
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": request.message}],
        "complaint_id": request.complaint_id,
        "current_complaint": current_complaint_dict,
        "updated_fields": [],
    }

    try:
        logger.info(f"Invoking AIVOA LangGraph Agent for message: '{request.message[:50]}...'")
        
        # Invoke LangGraph agent
        final_state: AgentState = await compiled_graph.ainvoke(initial_state)
        
        detected_intent = final_state.get("intent", Intent.UNKNOWN)
        intent_str = detected_intent.value if isinstance(detected_intent, Intent) else str(detected_intent)
        response_msg = final_state.get("response_message") or "AIVOA Copilot request processed."
        updated_fields = final_state.get("updated_fields") or []
        err_msg = final_state.get("error")

        return CopilotResponse(
            message=response_msg,
            intent=intent_str,
            complaint=existing_complaint_obj,
            risk_assessment=None,
            updated_fields=updated_fields,
            error=err_msg
        )

    except Exception as e:
        logger.error(f"LangGraph execution failed for message '{request.message}': {e}", exc_info=True)
        return CopilotResponse(
            message="I couldn't process the request due to an internal workflow error.",
            intent=Intent.UNKNOWN.value,
            complaint=existing_complaint_obj,
            risk_assessment=None,
            updated_fields=[],
            error="AI workflow execution failed"
        )

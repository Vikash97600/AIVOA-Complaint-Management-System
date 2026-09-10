from typing import Dict, Any
from app.ai.state import AgentState
from app.ai.prompts.edit_complaint import EDIT_COMPLAINT_SYSTEM_PROMPT, ComplaintEditOutput
from app.services.groq_service import groq_service
from app.core.logging_config import logger

ALLOWED_EDITABLE_FIELDS = {
    "customer_name",
    "complaint_source",
    "contact_info",
    "complaint_date",
    "product_name",
    "strength_grade",
    "batch_number",
    "manufacturing_date",
    "expiry_date",
    "affected_quantity",
    "manufacturing_facility",
    "packaging_info",
    "complaint_category",
    "defect_type",
    "complaint_description",
}


async def edit_complaint_node(state: AgentState) -> Dict[str, Any]:
    """
    Edit Complaint Node for LangGraph.
    Uses Groq LLM (gemma2-9b-it via GroqService) to extract partial field deltas
    requested by the user, then applies a deterministic Python merge onto the current_complaint.
    Preserves all unmentioned fields and system attributes.
    """
    current_complaint = state.get("current_complaint")
    complaint_id = state.get("complaint_id")

    if not current_complaint or not isinstance(current_complaint, dict):
        logger.warning("Edit complaint node: Attempted edit without an active complaint in state.")
        return {
            "response_message": "Please select or log a complaint before attempting to make updates.",
            "updated_fields": [],
            "error": "No active complaint available to edit.",
        }

    messages = state.get("messages", [])
    if not messages:
        return {
            "response_message": "No edit instructions provided.",
            "updated_fields": [],
        }

    last_message = messages[-1].get("content", "").strip()
    if not last_message:
        return {
            "response_message": "Empty edit instructions provided.",
            "updated_fields": [],
        }

    logger.info(f"Edit complaint node processing edit request for complaint ID '{complaint_id}': '{last_message[:60]}...'")

    # Format current complaint context for LLM prompt
    formatted_current_lines = [
        f"{k}: {v}" for k, v in current_complaint.items() if v is not None and k in ALLOWED_EDITABLE_FIELDS
    ]
    formatted_current = "\n".join(formatted_current_lines) if formatted_current_lines else "Empty complaint draft."

    llm_messages = [
        {"role": "system", "content": EDIT_COMPLAINT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"CURRENT COMPLAINT:\n{formatted_current}\n\n"
                f"USER EDIT REQUEST:\n{last_message}"
            ),
        },
    ]

    try:
        edit_res: ComplaintEditOutput = await groq_service.generate_structured(
            messages=llm_messages,
            response_model=ComplaintEditOutput,
            operation="edit_complaint_extraction",
        )

        # Sanitize and validate extracted fields against allowed editable schema
        requested_fields = [f for f in edit_res.updated_fields if f in ALLOWED_EDITABLE_FIELDS]
        sanitized_changes = {
            k: v for k, v in edit_res.changes.items() if k in ALLOWED_EDITABLE_FIELDS and k in requested_fields
        }

        if not requested_fields:
            logger.info("Edit complaint node: No valid/supported fields identified in edit request.")
            return {
                "current_complaint": current_complaint,
                "response_message": "I could not identify any supported complaint fields to update. Please specify what you want to change (e.g. batch number, affected quantity).",
                "updated_fields": [],
            }

        # Deterministic Python Merge: Update ONLY requested fields; preserve all unmentioned fields
        merged_complaint = dict(current_complaint)
        change_summaries = []

        for field in requested_fields:
            new_val = sanitized_changes.get(field, None)
            merged_complaint[field] = new_val

            field_label = field.replace("_", " ").title()
            if new_val is None:
                change_summaries.append(f"{field_label} cleared")
            else:
                change_summaries.append(f"{field_label} changed to '{new_val}'")

        summary_str = ", ".join(change_summaries)
        response_msg = f"Complaint updated successfully ({summary_str})."

        logger.info(f"Edit complaint node updated {len(requested_fields)} fields: {requested_fields}")

        return {
            "current_complaint": merged_complaint,
            "updated_fields": requested_fields,
            "response_message": response_msg,
        }

    except Exception as e:
        logger.error(f"Groq edit extraction failed in edit_complaint_node: {e}", exc_info=True)
        return {
            "current_complaint": current_complaint,
            "error": "Failed to extract complaint edits via AI.",
            "response_message": "I encountered an issue processing your edit request. The existing complaint remains unchanged.",
            "updated_fields": [],
        }

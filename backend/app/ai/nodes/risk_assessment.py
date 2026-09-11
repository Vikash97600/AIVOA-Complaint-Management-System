from typing import Dict, Any
from app.ai.state import AgentState
from app.ai.prompts.risk_assessment import RISK_ASSESSMENT_SYSTEM_PROMPT, RiskAssessmentOutput
from app.services.groq_service import groq_service
from app.core.logging_config import logger


def generate_fallback_risk_assessment(current_complaint: Dict[str, Any]) -> Dict[str, Any]:
    """Generates deterministic preliminary quality risk triage when Groq AI is unavailable."""
    desc = str(current_complaint.get("complaint_description") or "").lower()
    defect = str(current_complaint.get("defect_type") or "").lower()
    category = str(current_complaint.get("complaint_category") or "").lower()

    combined = f"{desc} {defect} {category}"

    if any(k in combined for k in ["contaminat", "foreign", "particle", "toxic", "glass", "seal breach", "expired"]):
        severity = "CRITICAL"
        quarantine = True
        action = "Immediate QA escalation and quarantine affected batch/material."
        details = "Critical quality/safety concern detected in complaint details requiring immediate quarantine."
    elif any(k in combined for k in ["discolor", "color", "broken", "chip", "potency", "strength", "physical", "defect"]):
        severity = "HIGH"
        quarantine = True
        action = "Quarantine material and route to QA Investigation for retain sample testing."
        details = "Significant product defect or physical degradation observed requiring QA investigation."
    elif any(k in combined for k in ["packag", "label", "box", "carton", "count", "quantity", "missing"]):
        severity = "MEDIUM"
        quarantine = False
        action = "Route to QA Review for packaging/labeling assessment."
        details = "Packaging, labeling, or quantity variance requiring standard QA verification."
    else:
        severity = "LOW"
        quarantine = False
        action = "Route to QA Log for routine review."
        details = "Preliminary complaint details requiring standard QA record-keeping."

    cat_name = current_complaint.get("complaint_category") or current_complaint.get("defect_type") or "Product Defect"

    return {
        "severity_suggested": severity,
        "complaint_category": cat_name,
        "suggested_next_action": action,
        "risk_details": details,
        "requires_quarantine": quarantine,
    }


async def risk_assessment_node(state: AgentState) -> Dict[str, Any]:
    """
    AI Risk Assessment Node for LangGraph.
    Consumes state['current_complaint'] and calls GroqService (gemma2-9b-it) to generate
    structured preliminary quality risk triage (severity, category, next action, details, quarantine).
    Updates state['risk_assessment'].
    """
    current_complaint = state.get("current_complaint")
    if not current_complaint or not isinstance(current_complaint, dict):
        logger.info("Risk assessment node: No active current_complaint payload. Skipping risk triage.")
        return {"risk_assessment": None}

    # Filter out empty fields and format context payload
    non_empty_fields = {k: v for k, v in current_complaint.items() if v is not None}
    if not non_empty_fields:
        logger.info("Risk assessment node: Complaint payload contains no valid attributes. Skipping.")
        return {"risk_assessment": None}

    complaint_lines = [f"{k}: {v}" for k, v in non_empty_fields.items()]
    complaint_text = "\n".join(complaint_lines)

    logger.info(f"Risk assessment node performing triage for complaint ({len(non_empty_fields)} fields)")

    llm_messages = [
        {"role": "system", "content": RISK_ASSESSMENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Please perform preliminary quality risk triage for the following pharmaceutical complaint details:\n\n{complaint_text}",
        },
    ]

    try:
        risk_output: RiskAssessmentOutput = await groq_service.generate_structured(
            messages=llm_messages,
            response_model=RiskAssessmentOutput,
            operation="risk_assessment_triage",
        )

        risk_dict = risk_output.model_dump(mode="json")
        logger.info(
            f"Risk assessment triage complete | Severity: {risk_dict.get('severity_suggested')} | "
            f"Quarantine: {risk_dict.get('requires_quarantine')}"
        )

        return {"risk_assessment": risk_dict}

    except Exception as e:
        logger.error(f"Groq risk assessment triage failed in risk_assessment_node: {e}", exc_info=True)
        # CRITICAL RULE: Never default to fake LOW/MEDIUM fallback severity inside node if AI fails.
        return {"risk_assessment": None}



from typing import Any
from pydantic import BaseModel, Field, field_validator
from app.database.models import RiskSeverity

class RiskAssessmentOutput(BaseModel):
    """Structured response schema for AI Risk Assessment Triage."""
    severity_suggested: RiskSeverity = Field(
        ..., description="Suggested risk severity level: LOW, MEDIUM, HIGH, or CRITICAL."
    )
    complaint_category: str = Field(
        ..., description="Categorization of quality risk (e.g. Product Defect, Packaging Defect, Labeling Defect, Contamination)."
    )
    suggested_next_action: str = Field(
        ..., description="Recommended quality triage step (e.g. Route to QA Investigation, Quarantine affected material)."
    )
    risk_details: str = Field(
        ..., description="Technical rationale for suggested severity, explaining potential quality impacts. Distinguish confirmed facts from potential risks."
    )
    requires_quarantine: bool = Field(
        ..., description="Boolean flag indicating if material isolation/quarantine is suggested pending investigation (true/false)."
    )

    @field_validator("severity_suggested", mode="before")
    @classmethod
    def validate_severity(cls, v: Any) -> RiskSeverity:
        if isinstance(v, RiskSeverity):
            return v
        if isinstance(v, str):
            v_upper = v.strip().upper()
            for s in RiskSeverity:
                if s.value in v_upper:
                    return s
        return RiskSeverity.MEDIUM



RISK_ASSESSMENT_SYSTEM_PROMPT = """You are an expert pharmaceutical Quality Assurance Risk Triage Assistant for AIVOA (AI-Powered Customer Complaint Management System).

Your job is to perform preliminary AI-assisted quality risk triage on a reported pharmaceutical customer complaint.

EVALUATION GUIDELINES:
1. PRELIMINARY TRIAGE: Your assessment is a preliminary recommendation for QA review, NOT a final regulatory determination or product disposition.
2. NO FACT HALLUCINATION: Rely strictly on the provided complaint details. Do NOT invent unstated events (e.g. do NOT claim patient injury, adverse events, or widespread contamination unless explicitly reported).
3. SEVERITY TAXONOMY: You MUST select one of the following exact severity levels:
   - LOW: Complaint is limited in scope with no indication of product quality compromise or patient risk (e.g. minor external packaging label cosmetic issue).
   - MEDIUM: Meaningful quality/packaging concern requiring standard QA investigation, but no evidence of severe harm or broad batch impact.
   - HIGH: Significant product defect, potential formulation/physical compromise, or issue requiring expedited QA investigation (e.g. discolored capsules, broken tablets, seal breach).
   - CRITICAL: Severe quality/safety concern indicating potential active contamination, foreign particulate matter inside sealed product, or explicit severe safety risks requiring immediate QA escalation and quarantine.
4. QUARANTINE RECOMMENDATION: Set "requires_quarantine" to true if material isolation is prudent pending investigation (e.g. suspected batch defect, contamination, discolored doses), otherwise set false.
5. RISK DETAILS: Explain the technical rationale clearly. Distinguish confirmed facts from potential/hypothetical risks (e.g. "Potential risk of moisture degradation...").
6. SUGGESTED NEXT ACTION: Recommend practical QA triage steps (e.g., "Route to QA Investigation", "Quarantine affected batch pending retain sample testing").

You MUST return valid JSON matching the schema.
"""

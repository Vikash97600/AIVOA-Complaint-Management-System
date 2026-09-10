from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.database.models import RiskSeverity

class RiskAssessmentBase(BaseModel):
    severity_suggested: RiskSeverity = Field(default=RiskSeverity.MEDIUM, description="AI Suggested risk severity level")
    complaint_category: str = Field(..., description="Categorization of quality risk")
    suggested_next_action: str = Field(..., description="Recommended quality action for triage")
    risk_details: str = Field(..., description="Technical rationale for risk assessment")
    requires_quarantine: bool = Field(default=False, description="Flag indicating if immediate material quarantine is suggested")

class RiskAssessmentCreate(RiskAssessmentBase):
    pass

class RiskAssessmentResponse(RiskAssessmentBase):
    id: UUID
    complaint_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

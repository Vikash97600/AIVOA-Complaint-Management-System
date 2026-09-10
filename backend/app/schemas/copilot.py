from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from app.schemas.complaint import ComplaintResponse
from app.schemas.risk import RiskAssessmentResponse

class CopilotMessageRequest(BaseModel):
    message: str = Field(..., description="Natural language prompt or update request from the user")
    complaint_id: Optional[str] = Field(None, description="Optional active draft complaint UUID")

class CopilotResponse(BaseModel):
    message: str = Field(..., description="Conversational summary response from AIVOA Copilot")
    intent: str = Field(..., description="Detected AI request intent")
    complaint: Optional[ComplaintResponse] = Field(None, description="Structured complaint state object")
    risk_assessment: Optional[RiskAssessmentResponse] = Field(None, description="AI-assisted quality risk assessment object")
    updated_fields: List[str] = Field(default_factory=list, description="List of modified complaint attributes")
    error: Optional[str] = Field(None, description="Error details if execution failed")

    model_config = ConfigDict(from_attributes=True)

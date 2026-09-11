from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class CompletenessResponse(BaseModel):
    is_complete: bool = Field(..., description="Whether the complaint has sufficient details for QA review")
    completion_score: int = Field(..., description="Score from 0 to 100 representing complaint detail completeness")
    status_label: str = Field(..., description="Label: Complete (90-100), Mostly Complete (75-89), Incomplete (50-74), Highly Incomplete (0-49)")
    missing_fields: List[str] = Field(default_factory=list, description="List of important complaint attributes currently missing")
    warnings: List[str] = Field(default_factory=list, description="Quality/investigative warnings regarding missing details")
    recommendations: List[str] = Field(default_factory=list, description="Recommended next data-collection steps")

    model_config = ConfigDict(from_attributes=True)

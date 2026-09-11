from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class ComplaintSummaryResponse(BaseModel):
    summary_text: str = Field(..., description="Concise executive summary of customer complaint")
    key_facts: List[str] = Field(default_factory=list, description="Key bullet points summarizing product, batch, defect, and severity")
    generated_at: str = Field(..., description="ISO Timestamp when summary was generated")

    model_config = ConfigDict(from_attributes=True)

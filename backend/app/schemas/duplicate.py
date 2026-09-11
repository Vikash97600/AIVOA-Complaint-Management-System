from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class DuplicateMatch(BaseModel):
    complaint_id: str = Field(..., description="UUID of matching complaint")
    qms_reference_number: Optional[str] = Field(None, description="QMS Reference Number if committed")
    product_name: Optional[str] = Field(None, description="Product Name")
    batch_number: Optional[str] = Field(None, description="Batch / Lot Number")
    similarity_score: float = Field(..., description="Similarity confidence score from 0.0 to 1.0")
    reasons: List[str] = Field(default_factory=list, description="Specific fields or semantic features matching existing complaint")

class DuplicateDetectionResponse(BaseModel):
    is_duplicate: bool = Field(..., description="Whether a likely or potential duplicate was detected")
    confidence: float = Field(..., description="Overall confidence level (0.0 to 1.0)")
    matched_complaint_id: Optional[str] = Field(None, description="Top matching complaint UUID")
    matched_qms_reference: Optional[str] = Field(None, description="Top matching QMS Reference Code")
    matches: List[DuplicateMatch] = Field(default_factory=list, description="List of potential candidate duplicate complaints")
    summary_reasoning: str = Field(..., description="Explanation of duplicate detection finding")

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class ComplaintDocumentBase(BaseModel):
    file_name: str
    file_path: str
    file_type: str
    file_size: Optional[int] = None
    extracted_text: Optional[str] = None

class ComplaintDocumentCreate(ComplaintDocumentBase):
    pass

class ComplaintDocumentResponse(ComplaintDocumentBase):
    id: UUID
    complaint_id: UUID
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

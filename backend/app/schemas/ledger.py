from pydantic import BaseModel, ConfigDict
from typing import Any
from datetime import datetime
from uuid import UUID

class QMSLedgerResponse(BaseModel):
    id: UUID
    complaint_id: UUID
    qms_reference_number: str
    committed_at: datetime
    frozen_payload_json: Any

    model_config = ConfigDict(from_attributes=True)

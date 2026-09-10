from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.database.models import ComplaintStatus
from app.schemas.risk import RiskAssessmentResponse
from app.schemas.document import ComplaintDocumentResponse
from app.schemas.ledger import QMSLedgerResponse

class ComplaintBase(BaseModel):
    customer_name: Optional[str] = None
    complaint_source: Optional[str] = None
    contact_info: Optional[str] = None
    complaint_date: Optional[str] = None
    
    product_name: Optional[str] = None
    strength_grade: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    affected_quantity: Optional[str] = None
    
    manufacturing_facility: Optional[str] = None
    packaging_info: Optional[str] = None
    
    complaint_category: Optional[str] = None
    defect_type: Optional[str] = None
    complaint_description: Optional[str] = None

class ComplaintCreate(ComplaintBase):
    status: Optional[ComplaintStatus] = ComplaintStatus.DRAFT

class ComplaintUpdate(BaseModel):
    customer_name: Optional[str] = None
    complaint_source: Optional[str] = None
    contact_info: Optional[str] = None
    complaint_date: Optional[str] = None
    
    product_name: Optional[str] = None
    strength_grade: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    affected_quantity: Optional[str] = None
    
    manufacturing_facility: Optional[str] = None
    packaging_info: Optional[str] = None
    
    complaint_category: Optional[str] = None
    defect_type: Optional[str] = None
    complaint_description: Optional[str] = None
    status: Optional[ComplaintStatus] = None
    qms_reference_number: Optional[str] = None

class ComplaintResponse(ComplaintBase):
    id: UUID
    status: ComplaintStatus
    qms_reference_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    risk_assessment: Optional[RiskAssessmentResponse] = None
    documents: List[ComplaintDocumentResponse] = []
    qms_ledger: Optional[QMSLedgerResponse] = None

    model_config = ConfigDict(from_attributes=True)

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate, ComplaintResponse
from app.schemas.ledger import QMSCommitRequest, QMSLedgerResponse
from app.schemas.completeness import CompletenessResponse
from app.schemas.duplicate import DuplicateDetectionResponse
from app.schemas.summary import ComplaintSummaryResponse
from app.schemas.common import PaginatedResponse
from app.services import complaint_service

router = APIRouter(prefix="/complaints", tags=["Complaints"])

@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint_endpoint(
    payload: ComplaintCreate,
    db: AsyncSession = Depends(get_db)
):
    """Creates a new complaint record in DRAFT status."""
    complaint = await complaint_service.create_complaint(db, payload)
    return complaint

@router.get("/{complaint_id}", response_model=ComplaintResponse, status_code=status.HTTP_200_OK)
async def get_complaint_endpoint(
    complaint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a single complaint by UUID."""
    complaint = await complaint_service.get_complaint_by_id(db, complaint_id)
    return complaint

@router.get("", response_model=PaginatedResponse[ComplaintResponse], status_code=status.HTTP_200_OK)
async def list_complaints_endpoint(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(default=None, description="Filter by complaint status (e.g. DRAFT, COMMITTED)"),
    search: Optional[str] = Query(default=None, description="Search query matching customer, product, batch, or QMS reference"),
    db: AsyncSession = Depends(get_db)
):
    """Lists complaints with pagination, optional status/search filters, ordered by updated_at / created_at descending."""
    items, total = await complaint_service.list_complaints(
        db, page=page, page_size=page_size, status=status, search=search
    )
    return PaginatedResponse[ComplaintResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )

@router.patch("/{complaint_id}", response_model=ComplaintResponse, status_code=status.HTTP_200_OK)
async def update_complaint_endpoint(
    complaint_id: str,
    payload: ComplaintUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Updates ONLY the supplied non-None fields of a complaint.
    Preserves all existing unedited complaint fields (Safe Delta Update).
    """
    complaint = await complaint_service.update_complaint(db, complaint_id, payload)
    return complaint

@router.delete("/{complaint_id}", status_code=status.HTTP_200_OK)
async def delete_complaint_endpoint(
    complaint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently deletes a complaint in DRAFT status.
    Rejects deletion if status is COMMITTED with HTTP 409 Conflict.
    """
    return await complaint_service.delete_draft_complaint(db, complaint_id)

@router.post("/commit", response_model=ComplaintResponse, status_code=status.HTTP_200_OK)
async def commit_complaint_body_endpoint(
    payload: "QMSCommitRequest",
    db: AsyncSession = Depends(get_db)
):
    """
    Formally commits a draft complaint to the QMS Ledger via JSON body payload.
    """
    from app.services import qms_service
    complaint = await qms_service.commit_complaint_to_ledger(db, payload.complaint_id)
    return complaint

@router.post("/{complaint_id}/commit", response_model=ComplaintResponse, status_code=status.HTTP_200_OK)
async def commit_complaint_endpoint(
    complaint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Formally commits a draft complaint to the QMS Ledger via path parameter.
    """
    from app.services import qms_service
    complaint = await qms_service.commit_complaint_to_ledger(db, complaint_id)
    return complaint

@router.get("/{complaint_id}/qms", response_model=QMSLedgerResponse, status_code=status.HTTP_200_OK)
async def get_complaint_qms_ledger_endpoint(
    complaint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the frozen QMS Ledger entry and snapshot for a committed complaint.
    """
    from app.services import qms_service
    from app.core.exceptions import ComplaintNotFoundError
    ledger_entry = await qms_service.get_ledger_entry_by_complaint_id(db, complaint_id)
    if not ledger_entry:
        raise ComplaintNotFoundError(complaint_id)
    return ledger_entry

@router.post("/{complaint_id}/completeness", response_model=CompletenessResponse, status_code=status.HTTP_200_OK)
async def check_complaint_completeness_endpoint(
    complaint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluates complaint detail completeness and missing field warnings.
    """
    from app.services import completeness_service, complaint_service
    complaint = await complaint_service.get_complaint_by_id(db, complaint_id)
    complaint_dict = ComplaintResponse.model_validate(complaint).model_dump(mode="json")
    return completeness_service.calculate_completeness(complaint_dict)

@router.post("/{complaint_id}/duplicates", response_model=DuplicateDetectionResponse, status_code=status.HTTP_200_OK)
async def detect_duplicate_complaints_endpoint(
    complaint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Searches candidate complaints in MySQL for potential duplicate matches.
    """
    from app.services import duplicate_detection_service, complaint_service
    complaint = await complaint_service.get_complaint_by_id(db, complaint_id)
    complaint_dict = ComplaintResponse.model_validate(complaint).model_dump(mode="json")
    return await duplicate_detection_service.detect_duplicate_complaints(db, complaint_dict, complaint_id)

@router.post("/{complaint_id}/summary", response_model=ComplaintSummaryResponse, status_code=status.HTTP_200_OK)
async def generate_complaint_summary_endpoint(
    complaint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Generates a concise executive complaint summary using Groq gemma2-9b-it.
    """
    from app.services import summary_service, complaint_service
    complaint = await complaint_service.get_complaint_by_id(db, complaint_id)
    complaint_dict = ComplaintResponse.model_validate(complaint).model_dump(mode="json")
    risk_dict = complaint_dict.get("risk_assessment")
    return await summary_service.generate_complaint_summary(complaint_dict, risk_dict)


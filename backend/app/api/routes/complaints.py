import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate, ComplaintResponse
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
    db: AsyncSession = Depends(get_db)
):
    """Lists complaints with pagination ordered by creation date."""
    items, total = await complaint_service.list_complaints(db, page=page, page_size=page_size)
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

@router.post("/{complaint_id}/commit", response_model=ComplaintResponse, status_code=status.HTTP_200_OK)
async def commit_complaint_endpoint(
    complaint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Formally commits a draft complaint to the QMS Ledger, generates a unique QMS reference number,
    and freezes payload snapshot.
    """
    complaint = await complaint_service.commit_complaint_to_qms(db, complaint_id)
    return complaint


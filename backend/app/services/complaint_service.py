import uuid
from typing import Tuple, List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database.models import Complaint, ComplaintStatus
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate
from app.core.exceptions import ComplaintNotFoundError, DatabaseOperationError
from app.core.logging_config import logger

async def create_complaint(db: AsyncSession, obj_in: ComplaintCreate) -> Complaint:
    """Creates a new complaint in DRAFT state."""
    try:
        data = obj_in.model_dump(exclude_unset=True)
        complaint = Complaint(**data)
        db.add(complaint)
        await db.commit()
        await db.refresh(complaint)
        logger.info(f"Created complaint ID: {complaint.id}")
        return complaint
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create complaint: {e}", exc_info=True)
        raise DatabaseOperationError("Failed to create complaint record")


async def get_complaint_by_id(db: AsyncSession, complaint_id: uuid.UUID | str) -> Complaint:
    """Retrieves a single complaint by UUID. Raises ComplaintNotFoundError if missing."""
    if isinstance(complaint_id, str):
        try:
            complaint_id = uuid.UUID(complaint_id)
        except ValueError:
            raise ComplaintNotFoundError(str(complaint_id))

    try:
        stmt = select(Complaint).where(Complaint.id == complaint_id)
        result = await db.execute(stmt)
        complaint = result.scalar_one_or_none()
        if not complaint:
            raise ComplaintNotFoundError(str(complaint_id))
        return complaint
    except ComplaintNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching complaint {complaint_id}: {e}", exc_info=True)
        raise DatabaseOperationError(f"Error fetching complaint with ID '{complaint_id}'")


async def list_complaints(
    db: AsyncSession, page: int = 1, page_size: int = 20
) -> Tuple[List[Complaint], int]:
    """Lists complaints with pagination ordered by created_at descending."""
    try:
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        offset = (page - 1) * page_size

        # Count total items
        count_stmt = select(func.count(Complaint.id))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one() or 0

        # Query paginated list
        stmt = (
            select(Complaint)
            .order_by(desc(Complaint.created_at))
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total
    except Exception as e:
        logger.error(f"Failed to list complaints: {e}", exc_info=True)
        raise DatabaseOperationError("Failed to list complaints")


async def update_complaint(
    db: AsyncSession, complaint_id: uuid.UUID | str, obj_in: ComplaintUpdate
) -> Complaint:
    """
    Updates ONLY the supplied non-None fields of an existing complaint.
    Preserves all other existing field values (Safe Delta Merge).
    """
    complaint = await get_complaint_by_id(db, complaint_id)

    update_data = obj_in.model_dump(exclude_unset=True)
    if not update_data:
        return complaint

    try:
        for field, value in update_data.items():
            setattr(complaint, field, value)

        complaint.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(complaint)
        logger.info(f"Updated complaint ID {complaint_id} fields: {list(update_data.keys())}")
        return complaint
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update complaint {complaint_id}: {e}", exc_info=True)
        raise DatabaseOperationError(f"Failed to update complaint '{complaint_id}'")

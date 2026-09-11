import uuid
from typing import Tuple, List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
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
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> Tuple[List[Complaint], int]:
    """Lists complaints with pagination, optional status/search filters, ordered by updated_at / created_at descending."""
    try:
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        offset = (page - 1) * page_size

        filters = []
        if status:
            from app.database.models import ComplaintStatus
            try:
                status_enum = ComplaintStatus(status.upper())
                filters.append(Complaint.status == status_enum)
            except ValueError:
                pass

        if search and search.strip():
            search_pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Complaint.customer_name.ilike(search_pattern),
                    Complaint.product_name.ilike(search_pattern),
                    Complaint.batch_number.ilike(search_pattern),
                    Complaint.qms_reference_number.ilike(search_pattern),
                )
            )

        # Count total items
        count_stmt = select(func.count(Complaint.id))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one() or 0

        # Query paginated list ordered by updated_at DESC, then created_at DESC
        stmt = (
            select(Complaint)
            .order_by(desc(Complaint.updated_at), desc(Complaint.created_at))
            .offset(offset)
            .limit(page_size)
        )
        if filters:
            stmt = stmt.where(*filters)

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
    Rejects modification if the complaint is already COMMITTED to the QMS Ledger.
    """
    complaint = await get_complaint_by_id(db, complaint_id)

    if complaint.status == ComplaintStatus.COMMITTED:
        from app.core.exceptions import ComplaintAlreadyCommittedError
        raise ComplaintAlreadyCommittedError(str(complaint_id))

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


async def create_complaint_document(
    db: AsyncSession,
    complaint_id: uuid.UUID | str,
    doc_in: "ComplaintDocumentCreate",
) -> "ComplaintDocument":
    """Creates a new ComplaintDocument record linked to a complaint."""
    from app.database.models import ComplaintDocument
    if isinstance(complaint_id, str):
        complaint_id = uuid.UUID(complaint_id)

    try:
        data = doc_in.model_dump()
        doc = ComplaintDocument(complaint_id=complaint_id, **data)
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        logger.info(f"Created ComplaintDocument ID '{doc.id}' for complaint '{complaint_id}'.")
        return doc
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create ComplaintDocument for complaint {complaint_id}: {e}", exc_info=True)
        raise DatabaseOperationError("Failed to save complaint document metadata to database")


async def commit_complaint_to_qms(
    db: AsyncSession,
    complaint_id: uuid.UUID | str,
) -> Complaint:
    """
    Formally commits a DRAFT complaint to the QMS Ledger.
    Delegates to qms_service.commit_complaint_to_ledger.
    """
    from app.services import qms_service
    return await qms_service.commit_complaint_to_ledger(db, complaint_id)


async def delete_draft_complaint(
    db: AsyncSession,
    complaint_id: uuid.UUID | str,
) -> dict:
    """
    Permanently deletes a draft complaint record and dependent draft metadata.
    Rejects deletion with ComplaintAlreadyCommittedError (HTTP 409 Conflict) if status is COMMITTED.
    Rejects deletion if a QMS ledger record is attached.
    """
    complaint = await get_complaint_by_id(db, complaint_id)

    if complaint.status == ComplaintStatus.COMMITTED:
        from app.core.exceptions import ComplaintAlreadyCommittedError
        raise ComplaintAlreadyCommittedError(str(complaint_id))

    from app.services import qms_service
    ledger_entry = await qms_service.get_ledger_entry_by_complaint_id(db, complaint.id)
    if ledger_entry:
        from app.core.exceptions import ComplaintAlreadyCommittedError
        raise ComplaintAlreadyCommittedError(str(complaint_id))

    try:
        deleted_id_str = str(complaint.id)
        await db.delete(complaint)
        await db.commit()
        logger.info(f"Deleted DRAFT complaint ID '{deleted_id_str}'.")
        return {
            "success": True,
            "complaint_id": deleted_id_str,
            "message": "Draft complaint deleted successfully."
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete draft complaint {complaint_id}: {e}", exc_info=True)
        raise DatabaseOperationError(f"Failed to delete complaint '{complaint_id}'")




import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.models import Complaint, ComplaintStatus, QMSLedger
from app.services import complaint_service
from app.core.exceptions import (
    ComplaintNotFoundError,
    ComplaintAlreadyCommittedError,
    ComplaintNotReadyForCommitError,
    RiskAssessmentMissingError,
    QMSCommitError,
)
from app.core.logging_config import logger


async def generate_qms_reference(db: AsyncSession) -> str:
    """
    Generates a unique, server-side QMS Reference Number in the format QMS-YYYY-XXXXXX.
    """
    current_year = datetime.now(timezone.utc).year
    prefix = f"QMS-{current_year}-"

    stmt = select(func.count(QMSLedger.id)).where(QMSLedger.qms_reference_number.like(f"{prefix}%"))
    res = await db.execute(stmt)
    count = (res.scalar_one() or 0) + 1

    qms_ref = f"{prefix}{count:06d}"

    check_stmt = select(QMSLedger).where(QMSLedger.qms_reference_number == qms_ref)
    existing = await db.execute(check_stmt)
    if existing.scalar_one_or_none():
        qms_ref = f"{prefix}{str(uuid.uuid4())[:6].upper()}"

    return qms_ref


def validate_for_commit(complaint: Complaint) -> None:
    """
    Validates that a complaint is eligible for QMS Ledger commit:
    - Status must be DRAFT (not already COMMITTED)
    - Core identity details must exist
    - Preliminary AI Risk Assessment must exist
    """
    if complaint.status == ComplaintStatus.COMMITTED:
        raise ComplaintAlreadyCommittedError(str(complaint.id))

    has_core_info = bool(
        (complaint.customer_name and complaint.customer_name.strip())
        or (complaint.product_name and complaint.product_name.strip())
        or (complaint.complaint_description and complaint.complaint_description.strip())
    )
    if not has_core_info:
        raise ComplaintNotReadyForCommitError(
            "Complaint cannot be committed without minimum customer, product, or complaint description details."
        )

    if not complaint.risk_assessment:
        raise RiskAssessmentMissingError(
            "Complaint cannot be committed because the risk assessment is unavailable."
        )


def build_frozen_snapshot(complaint: Complaint, qms_reference_number: str) -> Dict[str, Any]:
    """
    Constructs a clean, JSON-serializable frozen payload snapshot of the complaint,
    its risk assessment, document metadata, and commit timestamp.
    """
    complaint_dict = {
        "id": str(complaint.id),
        "status": ComplaintStatus.COMMITTED.value,
        "qms_reference_number": qms_reference_number,
        "customer_name": complaint.customer_name,
        "complaint_source": complaint.complaint_source,
        "contact_info": complaint.contact_info,
        "complaint_date": complaint.complaint_date,
        "product_name": complaint.product_name,
        "strength_grade": complaint.strength_grade,
        "batch_number": complaint.batch_number,
        "manufacturing_date": complaint.manufacturing_date,
        "expiry_date": complaint.expiry_date,
        "affected_quantity": complaint.affected_quantity,
        "manufacturing_facility": complaint.manufacturing_facility,
        "packaging_info": complaint.packaging_info,
        "complaint_category": complaint.complaint_category,
        "defect_type": complaint.defect_type,
        "complaint_description": complaint.complaint_description,
        "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
        "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None,
    }

    risk_dict = None
    if complaint.risk_assessment:
        ra = complaint.risk_assessment
        severity_val = ra.severity_suggested.value if hasattr(ra.severity_suggested, "value") else str(ra.severity_suggested)
        risk_dict = {
            "id": str(ra.id),
            "complaint_id": str(ra.complaint_id),
            "severity_suggested": severity_val,
            "complaint_category": ra.complaint_category,
            "suggested_next_action": ra.suggested_next_action,
            "risk_details": ra.risk_details,
            "requires_quarantine": ra.requires_quarantine,
            "created_at": ra.created_at.isoformat() if ra.created_at else None,
        }

    documents_list = [
        {
            "id": str(d.id),
            "file_name": d.file_name,
            "file_type": d.file_type,
            "file_size": d.file_size,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
        }
        for d in (complaint.documents or [])
    ]

    committed_at = datetime.now(timezone.utc).isoformat()

    return {
        "complaint": complaint_dict,
        "risk_assessment": risk_dict,
        "documents": documents_list,
        "committed_at": committed_at,
    }


async def commit_complaint_to_ledger(
    db: AsyncSession,
    complaint_id: uuid.UUID | str
) -> Complaint:
    """
    Executes atomic transactional commit of a complaint to the QMS Ledger:
    1. Validates complaint and risk assessment state
    2. Generates server-side QMS reference number
    3. Builds frozen snapshot payload
    4. Persists QMSLedger record
    5. Updates complaint status to COMMITTED
    6. Commits transaction atomically
    """
    complaint = await complaint_service.get_complaint_by_id(db, complaint_id)

    if complaint.status == ComplaintStatus.COMMITTED:
        logger.info(f"Complaint '{complaint_id}' is already committed to QMS Ledger.")
        return complaint

    if isinstance(complaint_id, str):
        complaint_id = uuid.UUID(complaint_id)

    validate_for_commit(complaint)

    qms_ref = await generate_qms_reference(db)
    frozen_payload = build_frozen_snapshot(complaint, qms_ref)
    commit_time = datetime.now(timezone.utc)

    try:
        ledger_entry = QMSLedger(
            complaint_id=complaint_id,
            qms_reference_number=qms_ref,
            committed_at=commit_time,
            frozen_payload_json=frozen_payload,
        )
        db.add(ledger_entry)

        complaint.status = ComplaintStatus.COMMITTED
        complaint.qms_reference_number = qms_ref
        complaint.updated_at = commit_time

        await db.commit()
        await db.refresh(complaint)
        logger.info(f"Successfully committed complaint '{complaint_id}' to QMS Ledger with reference '{qms_ref}'.")
        return complaint
    except Exception as e:
        await db.rollback()
        logger.error(f"Transaction rollback: Failed to commit complaint '{complaint_id}' to QMS: {e}", exc_info=True)
        raise QMSCommitError(f"Failed to commit complaint '{complaint_id}' to QMS Ledger.")


async def get_ledger_entry_by_complaint_id(
    db: AsyncSession,
    complaint_id: uuid.UUID | str
) -> Optional[QMSLedger]:
    """Retrieves QMSLedger entry by complaint UUID."""
    if isinstance(complaint_id, str):
        complaint_id = uuid.UUID(complaint_id)

    stmt = select(QMSLedger).where(QMSLedger.complaint_id == complaint_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

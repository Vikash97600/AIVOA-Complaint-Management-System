import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from app.database.models import Complaint
from app.schemas.duplicate import DuplicateDetectionResponse, DuplicateMatch
from app.core.logging_config import logger

async def detect_duplicate_complaints(
    db: AsyncSession,
    complaint_data: Dict[str, Any],
    current_complaint_id: Optional[str] = None
) -> DuplicateDetectionResponse:
    """
    Searches MySQL database for potential candidate duplicate complaints
    matching Product Name, Batch Number, Customer, or Defect Type.
    Computes similarity metrics and candidate reasons.
    """
    if not complaint_data:
        return DuplicateDetectionResponse(
            is_duplicate=False,
            confidence=0.0,
            matched_complaint_id=None,
            matched_qms_reference=None,
            matches=[],
            summary_reasoning="No complaint data provided for duplicate evaluation."
        )

    product_name = complaint_data.get("product_name")
    batch_number = complaint_data.get("batch_number")
    customer_name = complaint_data.get("customer_name")
    complaint_category = complaint_data.get("complaint_category")

    filters = []
    if product_name and len(product_name.strip()) > 2:
        filters.append(Complaint.product_name == product_name)
    if batch_number and len(batch_number.strip()) > 2:
        filters.append(Complaint.batch_number == batch_number)
    if customer_name and len(customer_name.strip()) > 2:
        filters.append(Complaint.customer_name == customer_name)

    if not filters:
        return DuplicateDetectionResponse(
            is_duplicate=False,
            confidence=0.0,
            matched_complaint_id=None,
            matched_qms_reference=None,
            matches=[],
            summary_reasoning="Insufficient product or batch details to perform duplicate candidate search."
        )

    stmt = select(Complaint).where(or_(*filters))

    if current_complaint_id:
        try:
            curr_uuid = uuid.UUID(current_complaint_id)
            stmt = stmt.where(Complaint.id != curr_uuid)
        except ValueError:
            pass

    res = await db.execute(stmt.limit(10))
    candidates = list(res.scalars().all())

    if not candidates:
        return DuplicateDetectionResponse(
            is_duplicate=False,
            confidence=0.0,
            matched_complaint_id=None,
            matched_qms_reference=None,
            matches=[],
            summary_reasoning="No duplicate complaint candidates found in database."
        )

    matches: List[DuplicateMatch] = []

    for cand in candidates:
        score = 0.0
        reasons = []

        # Product Name Match
        if product_name and cand.product_name and product_name.lower().strip() == cand.product_name.lower().strip():
            score += 0.35
            reasons.append(f"Matching Product Name ('{cand.product_name}')")

        # Batch Number Match
        if batch_number and cand.batch_number and batch_number.lower().strip() == cand.batch_number.lower().strip():
            score += 0.55
            reasons.append(f"Matching Batch Number ('{cand.batch_number}')")

        # Customer Name Match
        if customer_name and cand.customer_name and customer_name.lower().strip() == cand.customer_name.lower().strip():
            score += 0.10
            reasons.append(f"Matching Customer ('{cand.customer_name}')")

        # Category Match
        if complaint_category and cand.complaint_category and complaint_category.lower().strip() == cand.complaint_category.lower().strip():
            score += 0.10
            reasons.append("Matching Complaint Category")

        final_score = round(min(1.0, score), 2)
        if final_score >= 0.40:
            matches.append(
                DuplicateMatch(
                    complaint_id=str(cand.id),
                    qms_reference_number=cand.qms_reference_number,
                    product_name=cand.product_name,
                    batch_number=cand.batch_number,
                    similarity_score=final_score,
                    reasons=reasons
                )
            )

    matches.sort(key=lambda m: m.similarity_score, reverse=True)

    if not matches:
        return DuplicateDetectionResponse(
            is_duplicate=False,
            confidence=0.0,
            matched_complaint_id=None,
            matched_qms_reference=None,
            matches=[],
            summary_reasoning="No high-confidence duplicate candidates detected."
        )

    top_match = matches[0]
    is_dup = top_match.similarity_score >= 0.70

    summary_text = (
        f"Potential duplicate detected ({int(top_match.similarity_score * 100)}% match confidence) "
        f"matching complaint ID {top_match.complaint_id}"
        + (f" (QMS Ref: {top_match.qms_reference_number})" if top_match.qms_reference_number else "")
        + f" due to: {', '.join(top_match.reasons)}."
        if is_dup else
        f"Low-to-moderate similarity found with existing complaint ID {top_match.complaint_id} ({int(top_match.similarity_score * 100)}% match)."
    )

    return DuplicateDetectionResponse(
        is_duplicate=is_dup,
        confidence=top_match.similarity_score,
        matched_complaint_id=top_match.complaint_id,
        matched_qms_reference=top_match.qms_reference_number,
        matches=matches,
        summary_reasoning=summary_text
    )

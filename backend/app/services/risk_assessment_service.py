import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import RiskAssessment
from app.schemas.risk import RiskAssessmentCreate
from app.core.exceptions import DatabaseOperationError
from app.core.logging_config import logger


async def save_or_update_risk_assessment(
    db: AsyncSession,
    complaint_id: uuid.UUID | str,
    obj_in: RiskAssessmentCreate
) -> RiskAssessment:
    """
    Creates or updates the single RiskAssessment for a given complaint_id in MySQL database.
    """
    if isinstance(complaint_id, str):
        try:
            complaint_id = uuid.UUID(complaint_id)
        except ValueError:
            raise DatabaseOperationError(f"Invalid UUID string format: '{complaint_id}'")

    try:
        stmt = select(RiskAssessment).where(RiskAssessment.complaint_id == complaint_id)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()

        data = obj_in.model_dump()
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            await db.commit()
            await db.refresh(existing)
            logger.info(f"Updated existing RiskAssessment for complaint ID: {complaint_id}")
            return existing
        else:
            new_risk = RiskAssessment(complaint_id=complaint_id, **data)
            db.add(new_risk)
            await db.commit()
            await db.refresh(new_risk)
            logger.info(f"Created new RiskAssessment for complaint ID: {complaint_id}")
            return new_risk
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to save RiskAssessment for complaint '{complaint_id}': {e}", exc_info=True)
        raise DatabaseOperationError(f"Failed to save risk assessment for complaint '{complaint_id}'")

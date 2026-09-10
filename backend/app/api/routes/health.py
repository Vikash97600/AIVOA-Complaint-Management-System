from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.dependencies import get_db
from app.core.config import settings
from app.core.logging_config import logger

router = APIRouter(tags=["Health"])

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Application health endpoint."""
    return {
        "status": "ok",
        "service": f"{settings.APP_NAME} API",
        "version": "1.0.0"
    }

@router.get("/health/database", status_code=status.HTTP_200_OK)
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Database connectivity health check endpoint."""
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "mysql"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "database": "mysql"
        }

@router.get("/health/ai", status_code=status.HTTP_200_OK)
async def ai_health_check():
    """AI service configuration status check endpoint."""
    is_configured = bool(
        settings.GROQ_API_KEY
        and settings.GROQ_API_KEY.strip()
        and settings.GROQ_API_KEY != "your_groq_api_key_here"
    )
    return {
        "provider": "groq",
        "model": settings.GROQ_MODEL,
        "configured": is_configured
    }

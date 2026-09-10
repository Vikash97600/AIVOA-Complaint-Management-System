from typing import AsyncGenerator, Optional
from fastapi import Header
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db as _get_db

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session and ensures cleanup."""
    async for session in _get_db():
        yield session

async def get_request_id(x_request_id: Optional[str] = Header(None)) -> str:
    """Returns incoming X-Request-ID header or generates a new UUID request ID."""
    return x_request_id or str(uuid.uuid4())

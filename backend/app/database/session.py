from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.database.models import Base

engine = None
AsyncSessionLocal = None

def get_engine():
    global engine, AsyncSessionLocal
    if engine is None:
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif db_url.startswith("sqlite://") and not db_url.startswith("sqlite+aiosqlite://"):
            db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
            
        engine = create_async_engine(db_url, echo=(settings.ENVIRONMENT == "development"))
        AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine

async def get_db():
    get_engine()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

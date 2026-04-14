"""
Database connection and session management using SQLAlchemy async.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Ensure the URL uses the async driver (postgresql+asyncpg://)
# This handles cases where the env var might just be "postgresql://"
async_url = settings.DATABASE_URL
if async_url.startswith("postgresql://"):
    async_url = async_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Renamed 'engine' to 'async_engine' to match your pgvector_service import
async_engine = create_async_engine(
    async_url, 
    echo=settings.DEBUG, 
    pool_pre_ping=True,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass

async def create_tables():
    """Create all tables on startup."""
    # Import models here to ensure they are registered with Base.metadata
    from app.models.user import User
    from app.models.document import Document
    from app.models.query import Query
    
    async with async_engine.begin() as conn:
        # Note: In production with migrations (Alembic), 
        # you might skip run_sync(Base.metadata.create_all)
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """FastAPI dependency that yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # We don't necessarily need a global commit here as services 
            # usually handle their own commits, but keeping it for safety.
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
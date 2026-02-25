"""
Async SQLAlchemy engine and session factory.
Supports SQLite (development) and PostgreSQL (production) via DATABASE_URL env var.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_ENV == "development",
    # SQLite-specific: allow concurrent access from multiple async tasks
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def create_tables():
    """Create all tables. Called on startup if running without Alembic."""
    from models.db_models import Base as ModelsBase  # noqa: F401 (trigger import)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

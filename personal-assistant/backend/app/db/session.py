"""Database session management and configuration."""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Create async engine with connection pooling
# SQLite requires specific connect_args for proper async support
connect_args = {}
if settings.database_url.startswith("sqlite+"):
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    str(settings.database_url),
    echo=settings.debug,
    connect_args=connect_args,
    pool_pre_ping=True if not settings.database_url.startswith("sqlite+") else False,
    pool_size=10 if not settings.database_url.startswith("sqlite+") else 5,
    max_overflow=20 if not settings.database_url.startswith("sqlite+") else 10,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """
    Dependency that provides a database session.

    Yields:
        AsyncSession: Database session

    Raises:
        Exception: If session creation fails
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the database by creating all tables.

    Note: In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()

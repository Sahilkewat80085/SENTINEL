from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.config import settings
from app.core.logging import logger

# Create the async engine
# For postgres, we use postgresql+asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True to log raw SQL queries in dev if needed
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection helper for FastAPI endpoints.

    Yields a db session and automatically closes it when finished.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database session exception, rolling back", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager helper for running database operations in background tasks

    or CLI scripts (where FastAPI Dependency injection is unavailable).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database context session exception, rolling back", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()

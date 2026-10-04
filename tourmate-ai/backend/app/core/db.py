"""
Database connectivity module for PostgreSQL + pgvector.
Configures Async SQLAlchemy 2.0 engine, session maker, and FastAPI dependency.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

# Prepare connection arguments (disable statement cache for connection poolers like Neon, PgBouncer, Supabase)
connect_args = {}
if any(keyword in settings.database_url.lower() for keyword in ["neon.tech", "pooler", "pgbouncer", "supabase"]):
    connect_args["statement_cache_size"] = 0

# Create Async Engine with production-hardened connection pool settings
async_engine: AsyncEngine = create_async_engine(
    settings.async_database_url,
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=10.0,
    pool_recycle=300,
    pool_pre_ping=True,
    connect_args=connect_args,
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an async database session per request.
    Rolls back automatically on exception and guarantees closure.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            if session.in_transaction():
                await session.rollback()
            raise
        finally:
            if session.in_transaction():
                await session.rollback()
            await session.close()


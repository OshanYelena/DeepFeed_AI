"""
DeepFeed AI - Database Infrastructure
Async SQLAlchemy engine, session factory, and Base model.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import NullPool
from sqlalchemy import text
import uuid
from datetime import datetime, timezone
from config import settings
from logger import get_logger

logger = get_logger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────
# Test runs create a fresh event loop per test (pytest-asyncio), but this
# engine is a module-level singleton imported once for the whole session.
# A sized pool hands out connections that were checked out under a now-
# closed loop, which asyncpg's cancel-on-close path then fails on with
# "attached to a different loop" — surfaces specifically through Starlette's
# BaseHTTPMiddleware (used by TraceIDMiddleware/RateLimitMiddleware/
# AuditMiddleware), which runs the app in its own anyio TaskGroup. NullPool
# sidesteps it by never reusing a connection across checkouts; production
# keeps the real sized pool.
_pool_kwargs = (
    {"poolclass": NullPool}
    if settings.app_env == "test"
    else {"pool_size": settings.database_pool_size, "max_overflow": settings.database_max_overflow}
)

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_pre_ping=True,
    **_pool_kwargs,
)

# ── Session Factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Base Model ────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class TimestampMixin:
    """Adds created_at and updated_at to any model."""
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async DB session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Health Check ──────────────────────────────────────────────────────────────
async def check_database_health() -> bool:
    """Returns True if database is reachable."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return False

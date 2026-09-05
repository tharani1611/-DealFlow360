import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from sqlalchemy import MetaData, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from app.core.config import settings
import logging

logger = logging.getLogger("dealflow360.database")

# PostgreSQL Naming Convention for predictable constraints and indexes
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)


class Base(DeclarativeBase):
    """Declarative Base class with explicit PostgreSQL naming conventions."""
    metadata = metadata


class UUIDMixin:
    """Mixin for models requiring UUID primary keys."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )


class TimestampMixin:
    """Mixin for models requiring timezone-aware created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )


# Create SQLAlchemy Async Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI request dependency providing an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """Verifies PostgreSQL database connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute(func.now())
            return True
    except Exception as exc:
        logger.warning(f"Database connection check failed: {exc}")
        return False


async def dispose_database_engine() -> None:
    """Gracefully disposes of database connection pool on shutdown."""
    await engine.dispose()
    logger.info("Database connection engine disposed.")

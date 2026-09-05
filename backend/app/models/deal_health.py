import uuid
from typing import Optional, List, Any, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.deal import Deal


class DealHealthSnapshot(Base, UUIDMixin, TimestampMixin):
    """Historical snapshot of deterministic deal health calculation."""
    __tablename__ = "deal_health_snapshots"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ATTENTION",
        index=True,
    )  # HEALTHY, ATTENTION, AT_RISK, CRITICAL, UNKNOWN
    positive_drivers: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    negative_drivers: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    metrics_snapshot: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    calculation_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1.0",
        server_default=text("'1.0'"),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    deal: Mapped["Deal"] = relationship("Deal")

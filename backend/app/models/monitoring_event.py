import uuid
from typing import Optional, Any, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class MonitoringEvent(Base, UUIDMixin, TimestampMixin):
    """Event log for detected operational and financial anomalies."""
    __tablename__ = "monitoring_events"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # STALLED_QUOTE, DISCOUNT_ANOMALY, DELIVERY_SLIPPAGE, BACKORDER_DELAY
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="INFO",
        index=True,
    )  # NORMAL, WATCH, ANOMALOUS, CRITICAL
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")

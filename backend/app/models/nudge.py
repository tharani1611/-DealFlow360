import uuid
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class Nudge(Base, UUIDMixin, TimestampMixin):
    """Nudge & Escalation notification item generated deterministically."""
    __tablename__ = "nudges"

    __table_args__ = (
        UniqueConstraint("organization_id", "dedup_hash", name="uq_nudges_org_dedup"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nudge_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # DEAL_STALLED, QUOTE_STALLED, APPROVAL_DELAY, CUSTOMER_FOLLOW_UP, DISCOUNT_ANOMALY, DELIVERY_RISK, BACKORDER_ALERT, PAYMENT_OVERDUE, SUBSCRIPTION_BILLING
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="INFO",
        index=True,
    )  # INFO, WARNING, URGENT, CRITICAL
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # deal, quotation, customer, shipment, invoice, subscription
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    dedup_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
        server_default=text("'OPEN'"),
        index=True,
    )  # CREATED, OPEN, ACKNOWLEDGED, COMPLETED, DISMISSED, ESCALATED
    assigned_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    action_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    assigned_user: Mapped[Optional["User"]] = relationship("User")
    history: Mapped[List["NudgeHistory"]] = relationship(
        "NudgeHistory",
        back_populates="nudge",
        cascade="all, delete-orphan",
        order_by="NudgeHistory.created_at.desc()",
        lazy="selectin",
    )


class NudgeHistory(Base, UUIDMixin, TimestampMixin):
    """Audit log of status transitions for Nudges."""
    __tablename__ = "nudge_history"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nudge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("nudges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    nudge: Mapped["Nudge"] = relationship("Nudge", back_populates="history")

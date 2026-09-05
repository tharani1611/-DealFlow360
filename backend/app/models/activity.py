import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User
    from app.models.customer import Customer
    from app.models.contact import Contact
    from app.models.deal import Deal
    from app.models.quotation import Quotation


class Activity(Base, UUIDMixin, TimestampMixin):
    """Activity model representing CRM activities (tasks, calls, meetings, notes, follow-ups)."""
    __tablename__ = "activities"

    __table_args__ = (
        Index("ix_activities_organization_id_status", "organization_id", "status"),
        Index("ix_activities_organization_id_due_at", "organization_id", "due_at"),
        Index("ix_activities_organization_id_customer_id", "organization_id", "customer_id"),
        Index("ix_activities_organization_id_deal_id", "organization_id", "deal_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", server_default=text("'pending'"))
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="medium", server_default=text("'medium'"))

    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    deal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deals.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    quotation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    assigned_to_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    customer: Mapped[Optional["Customer"]] = relationship("Customer")
    contact: Mapped[Optional["Contact"]] = relationship("Contact")
    deal: Mapped[Optional["Deal"]] = relationship("Deal")
    quotation: Mapped[Optional["Quotation"]] = relationship("Quotation")
    assigned_to_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_user_id])
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])

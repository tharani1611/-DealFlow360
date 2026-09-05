import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, Integer, Date, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.customer import Customer
    from app.models.contact import Contact
    from app.models.quotation import Quotation


class Deal(Base, UUIDMixin, TimestampMixin):
    """Deal model representing a sales deal/opportunity within an Organization."""
    __tablename__ = "deals"

    __table_args__ = (
        UniqueConstraint("organization_id", "deal_number", name="uq_deals_organization_id_deal_number"),
        Index("ix_deals_organization_id_stage", "organization_id", "stage"),
        Index("ix_deals_organization_id_status", "organization_id", "status"),
        Index("ix_deals_organization_id_customer_id", "organization_id", "customer_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    quotation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    deal_number: Mapped[str] = mapped_column(String(50), nullable=False)

    stage: Mapped[str] = mapped_column(String(50), nullable=False, default="new", server_default=text("'new'"))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open", server_default=text("'open'"))

    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00"))
    probability: Mapped[int] = mapped_column(Integer, nullable=False, default=10, server_default=text("10"))

    expected_close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    lost_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    customer: Mapped["Customer"] = relationship("Customer")
    contact: Mapped[Optional["Contact"]] = relationship("Contact")
    quotation: Mapped[Optional["Quotation"]] = relationship("Quotation", foreign_keys=[quotation_id])

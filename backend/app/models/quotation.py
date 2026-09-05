import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, Integer, ForeignKey, UniqueConstraint, CheckConstraint, Index, text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.customer import Customer
    from app.models.contact import Contact
    from app.models.deal import Deal
    from app.models.product import Product
    from app.models.user import User


class Quotation(Base, UUIDMixin, TimestampMixin):
    """Quotation model representing a sales quotation generated for a Customer within an Organization."""
    __tablename__ = "quotations"

    __table_args__ = (
        UniqueConstraint("organization_id", "quotation_number", name="uq_quotations_organization_id_quotation_number"),
        CheckConstraint("subtotal >= 0", name="ck_quotations_subtotal_non_negative"),
        CheckConstraint("discount_amount >= 0", name="ck_quotations_discount_non_negative"),
        CheckConstraint("tax_amount >= 0", name="ck_quotations_tax_non_negative"),
        CheckConstraint("total_amount >= 0", name="ck_quotations_total_non_negative"),
        Index("ix_quotations_org_status", "organization_id", "status"),
        Index("ix_quotations_contact_id", "contact_id"),
        Index("ix_quotations_deal_id", "deal_id"),
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
    deal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deals.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quotation_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", server_default="draft", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", server_default="USD", nullable=False)
    quotation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    updated_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    customer: Mapped["Customer"] = relationship("Customer")
    contact: Mapped[Optional["Contact"]] = relationship("Contact", foreign_keys=[contact_id])
    deal: Mapped[Optional["Deal"]] = relationship("Deal", foreign_keys=[deal_id])
    created_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id])
    items: Mapped[List["QuotationItem"]] = relationship(
        "QuotationItem",
        back_populates="quotation",
        cascade="all, delete-orphan",
        order_by="QuotationItem.sequence, QuotationItem.created_at"
    )


class QuotationItem(Base, UUIDMixin, TimestampMixin):
    """QuotationItem model representing a single line item in a Quotation with price snapshot."""
    __tablename__ = "quotation_items"

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_quotation_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_quotation_items_price_non_negative"),
        CheckConstraint("line_total >= 0", name="ck_quotation_items_line_total_non_negative"),
        CheckConstraint("discount_percent >= 0 AND discount_percent <= 100", name="ck_quotation_items_discount_percent_range"),
        CheckConstraint("discount_amount >= 0", name="ck_quotation_items_discount_amount_non_negative"),
        CheckConstraint("tax_rate >= 0", name="ck_quotation_items_tax_rate_non_negative"),
        CheckConstraint("tax_amount >= 0", name="ck_quotation_items_tax_amount_non_negative"),
        Index("ix_quotation_items_product_variant_id", "product_variant_id"),
    )

    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    product_variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Line-level commercial snapshots for future pricing/discount engines
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)

    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="items")
    product: Mapped["Product"] = relationship("Product")


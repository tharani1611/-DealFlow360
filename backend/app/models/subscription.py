import uuid
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import String, Numeric, ForeignKey, Date, DateTime, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.customer import Customer
    from app.models.quotation import Quotation, QuotationItem
    from app.models.product import Product
    from app.models.warehouses import ProductVariant
    from app.models.invoice import Invoice
    from app.models.user import User


class Subscription(Base, UUIDMixin, TimestampMixin):
    """Subscription model representing a recurring commercial service relationship."""
    __tablename__ = "subscriptions"

    __table_args__ = (
        UniqueConstraint("organization_id", "subscription_number", name="uq_subscriptions_org_sub_number"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    subscription_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quotation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quotation_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotation_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
    )
    plan_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("1.00"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    billing_interval: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MONTHLY",
        server_default=text("'MONTHLY'"),
    )  # MONTHLY, QUARTERLY, YEARLY
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_billing_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
        server_default=text("'ACTIVE'"),
        index=True,
    )  # TRIAL, ACTIVE, PAUSED, CANCELLED, EXPIRED

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    customer: Mapped["Customer"] = relationship("Customer")
    product: Mapped["Product"] = relationship("Product")
    schedules: Mapped[List["BillingSchedule"]] = relationship(
        "BillingSchedule",
        back_populates="subscription",
        cascade="all, delete-orphan",
        order_by="BillingSchedule.billing_period_start",
        lazy="selectin",
    )


class BillingSchedule(Base, UUIDMixin, TimestampMixin):
    """Recurring billing schedule entry for a subscription."""
    __tablename__ = "billing_schedules"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "subscription_id",
            "billing_period_start",
            "billing_period_end",
            name="uq_billing_schedules_period",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    billing_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    billing_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="SCHEDULED",
        server_default=text("'SCHEDULED'"),
        index=True,
    )  # SCHEDULED, DUE, INVOICED, PAID, SKIPPED, CANCELLED
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="schedules")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice")


class SubscriptionProration(Base, UUIDMixin, TimestampMixin):
    """Audit log of subscription proration adjustments for mid-cycle changes."""
    __tablename__ = "subscription_prorations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    new_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    old_unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    new_unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    billing_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_period_days: Mapped[int] = mapped_column(nullable=False)
    remaining_days: Mapped[int] = mapped_column(nullable=False)
    prorated_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class SubscriptionCancellation(Base, UUIDMixin, TimestampMixin):
    """Cancellation audit log for subscriptions."""
    __tablename__ = "subscription_cancellations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cancellation_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="END_OF_PERIOD",
        server_default=text("'END_OF_PERIOD'"),
    )  # IMMEDIATE, END_OF_PERIOD
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    requested_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, Numeric, ForeignKey, Index, DateTime, Date, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.quotation import Quotation, QuotationItem


class WarehouseAllocation(Base, UUIDMixin, TimestampMixin):
    """Smart warehouse allocation mapping quotation items to specific warehouses."""
    __tablename__ = "warehouse_allocations"

    __table_args__ = (
        Index("ix_warehouse_allocations_org_quotation", "organization_id", "quotation_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    quotation_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotation_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    allocated_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    allocation_strategy: Mapped[str] = mapped_column(String(50), default="SINGLE_WAREHOUSE", server_default="SINGLE_WAREHOUSE", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ALLOCATED", server_default="ALLOCATED", nullable=False)  # ALLOCATED, RELEASED, FULFILLED


class FulfillmentOverrideAudit(Base, UUIDMixin, TimestampMixin):
    """Audit log of manual fulfillment overrides by authorized internal users."""
    __tablename__ = "fulfillment_overrides"

    __table_args__ = (
        Index("ix_fulfillment_overrides_org_quotation", "organization_id", "quotation_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    quotation_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotation_items.id", ondelete="CASCADE"),
        nullable=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    actor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_allocation: Mapped[dict] = mapped_column(JSONB, nullable=False)
    new_allocation: Mapped[dict] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class Shipment(Base, UUIDMixin, TimestampMixin):
    """Physical shipment record created from warehouse allocations."""
    __tablename__ = "shipments"

    __table_args__ = (
        Index("ix_shipments_org_number", "organization_id", "shipment_number"),
        Index("ix_shipments_org_quotation", "organization_id", "quotation_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    shipment_number: Mapped[str] = mapped_column(String(100), nullable=False)
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", server_default="DRAFT", nullable=False)  # DRAFT, READY, PACKED, SHIPPED, IN_TRANSIT, DELIVERED, CANCELLED
    carrier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class ShipmentLine(Base, UUIDMixin, TimestampMixin):
    """Line item contained in a physical shipment."""
    __tablename__ = "shipment_lines"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    quotation_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotation_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)


class Backorder(Base, UUIDMixin, TimestampMixin):
    """Backorder entry created for unfulfilled quantity shortfall."""
    __tablename__ = "backorders"

    __table_args__ = (
        Index("ix_backorders_org_customer", "organization_id", "customer_id"),
        Index("ix_backorders_org_quotation", "organization_id", "quotation_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    backorder_number: Mapped[str] = mapped_column(String(100), nullable=False)
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    quotation_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotation_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True
    )
    requested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    fulfilled_quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    remaining_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    warehouse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="SET NULL"),
        nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="OPEN", server_default="OPEN", nullable=False)  # OPEN, PARTIALLY_FULFILLED, FULFILLED, CANCELLED
    promised_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class DeliveryPromise(Base, UUIDMixin, TimestampMixin):
    """Delivery promise tracking record for order fulfillment delivery timelines."""
    __tablename__ = "delivery_promises"

    __table_args__ = (
        Index("ix_delivery_promises_org_quotation", "organization_id", "quotation_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    shipment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shipments.id", ondelete="SET NULL"),
        nullable=True
    )
    backorder_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("backorders.id", ondelete="SET NULL"),
        nullable=True
    )
    promised_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ON_TRACK", server_default="ON_TRACK", nullable=False)  # ON_TRACK, AT_RISK, DELAYED, DELIVERED, UNKNOWN
    slippage_days: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class BillingClassification(Base, UUIDMixin, TimestampMixin):
    """Commercial billing model classification (ONE_TIME, RECURRING, HYBRID) per quotation."""
    __tablename__ = "billing_classifications"

    __table_args__ = (
        Index("ix_billing_classifications_org_quotation", "organization_id", "quotation_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    commercial_model: Mapped[str] = mapped_column(String(50), nullable=False)  # ONE_TIME, RECURRING, HYBRID
    one_time_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    recurring_monthly_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    billing_frequency: Mapped[str] = mapped_column(String(50), default="MONTHLY", server_default="MONTHLY", nullable=False)
    line_classifications: Mapped[dict] = mapped_column(JSONB, nullable=False)

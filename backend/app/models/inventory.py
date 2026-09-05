import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, ForeignKey, UniqueConstraint, CheckConstraint, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.warehouse import Warehouse
    from app.models.product import Product
    from app.models.warehouses import ProductVariant
    from app.models.quotation import Quotation, QuotationItem


class InventoryStock(Base, UUIDMixin, TimestampMixin):
    """Inventory Stock model representing normalized stock levels per warehouse and product/variant."""
    __tablename__ = "inventory_stocks"

    __table_args__ = (
        UniqueConstraint("organization_id", "warehouse_id", "product_id", "variant_id", "location_code", name="uq_inventory_stocks_org_wh_prod_var_loc"),
        CheckConstraint("on_hand_quantity >= 0", name="chk_on_hand_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="chk_reserved_non_negative"),
        CheckConstraint("available_quantity >= 0", name="chk_available_non_negative"),
        Index("ix_inventory_stocks_org_wh_prod", "organization_id", "warehouse_id", "product_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
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
        nullable=True,
        index=True
    )
    location_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default="MAIN")
    on_hand_quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)


class InventoryMovement(Base, UUIDMixin, TimestampMixin):
    """Immutable audit trail of stock transactions."""
    __tablename__ = "inventory_movements"

    __table_args__ = (
        Index("ix_inventory_movements_org_wh_prod", "organization_id", "warehouse_id", "product_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
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
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False)  # RECEIPT, RESERVATION, RELEASE, SHIPMENT, ADJUSTMENT, RETURN, TRANSFER
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # QUOTATION, SHIPMENT, MANUAL
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class InventoryReservation(Base, UUIDMixin, TimestampMixin):
    """Stock reservation record linked to a quotation item."""
    __tablename__ = "inventory_reservations"

    __table_args__ = (
        Index("ix_inventory_reservations_org_quotation", "organization_id", "quotation_id"),
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
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", server_default="ACTIVE", nullable=False)  # ACTIVE, RELEASED, CONSUMED, CANCELLED
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

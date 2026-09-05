import uuid
from decimal import Decimal
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import String, Text, Numeric, Boolean, ForeignKey, UniqueConstraint, CheckConstraint, Index, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.product import Product


class Warehouse(Base, UUIDMixin, TimestampMixin):
    """Warehouse master data representing a physical fulfillment location."""
    __tablename__ = "warehouses"

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_warehouses_organization_code"),
        Index("ix_warehouses_org_code", "organization_id", "code"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")


class ProductVariant(Base, UUIDMixin, TimestampMixin):
    """Product variant model for SKU-level inventory tracking."""
    __tablename__ = "product_variants"

    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_product_variants_org_sku"),
        CheckConstraint("unit_price_override IS NULL OR unit_price_override >= 0", name="chk_variant_price_positive"),
        Index("ix_product_variants_org_sku", "organization_id", "sku"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_price_override: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship("Product")

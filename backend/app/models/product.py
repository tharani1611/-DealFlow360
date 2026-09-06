import uuid
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, Boolean, ForeignKey, UniqueConstraint, CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class Product(Base, UUIDMixin, TimestampMixin):
    """Product model representing a product/service available for sale in an Organization."""
    __tablename__ = "products"

    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_products_organization_id_sku"),
        CheckConstraint("unit_price >= 0", name="unit_price_non_negative"),
        CheckConstraint("unit_cost >= 0", name="unit_cost_non_negative"),
        Index("ix_products_organization_id_sku", "organization_id", "sku"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR", nullable=False)
    hsn_sac_code: Mapped[Optional[str]] = mapped_column(String(10), default="8471", server_default="8471", nullable=True)
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("18.00"), server_default="18.00", nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="products")

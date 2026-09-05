import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, Integer, Boolean, ForeignKey, CheckConstraint, Index, text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.product import Product
    from app.models.customer import Customer


class PricingRule(Base, UUIDMixin, TimestampMixin):
    """Pricing Rule model for Quotation Pricing Engine."""
    __tablename__ = "pricing_rules"

    __table_args__ = (
        CheckConstraint("min_quantity > 0", name="ck_pricing_rules_min_quantity_positive"),
        CheckConstraint("value >= 0", name="ck_pricing_rules_value_non_negative"),
        CheckConstraint("priority > 0", name="ck_pricing_rules_priority_positive"),
        CheckConstraint("rule_type IN ('contract', 'customer', 'volume', 'promotion')", name="ck_pricing_rules_rule_type_valid"),
        CheckConstraint("price_type IN ('override_price', 'percentage_discount', 'fixed_discount')", name="ck_pricing_rules_price_type_valid"),
        Index("ix_pricing_rules_org_product", "organization_id", "product_id"),
        Index("ix_pricing_rules_org_customer", "organization_id", "customer_id"),
        Index("ix_pricing_rules_org_active", "organization_id", "is_active"),
        Index("ix_pricing_rules_lookup", "organization_id", "product_id", "is_active", "priority"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'contract', 'customer', 'volume', 'promotion'
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    min_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1.00"), server_default="1.00", nullable=False)
    max_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    price_type: Mapped[str] = mapped_column(String(50), default="override_price", server_default="override_price", nullable=False)  # 'override_price', 'percentage_discount', 'fixed_discount'
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, server_default="100", nullable=False)  # 1 = Highest
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    product: Mapped["Product"] = relationship("Product")
    customer: Mapped[Optional["Customer"]] = relationship("Customer")

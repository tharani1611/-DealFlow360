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
    from app.models.user import User


class DiscountPolicy(Base, UUIDMixin, TimestampMixin):
    """DiscountPolicy model for deterministic discount governance rules."""
    __tablename__ = "discount_policies"

    __table_args__ = (
        CheckConstraint("priority > 0", name="ck_discount_policies_priority_positive"),
        CheckConstraint("scope IN ('user', 'customer', 'product', 'role', 'organization')", name="ck_discount_policies_scope_valid"),
        CheckConstraint("max_discount_percent IS NULL OR (max_discount_percent >= 0 AND max_discount_percent <= 100)", name="ck_discount_policies_max_disc_pct_valid"),
        CheckConstraint("max_discount_amount IS NULL OR max_discount_amount >= 0", name="ck_discount_policies_max_disc_amt_valid"),
        CheckConstraint("minimum_unit_price IS NULL OR minimum_unit_price >= 0", name="ck_discount_policies_min_price_valid"),
        Index("ix_discount_policies_org_scope", "organization_id", "scope"),
        Index("ix_discount_policies_org_active", "organization_id", "is_active"),
        Index("ix_discount_policies_lookup", "organization_id", "is_active", "priority"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, server_default="100", nullable=False)  # 1 = Highest

    scope: Mapped[str] = mapped_column(String(50), default="organization", server_default="organization", nullable=False)  # 'user', 'customer', 'product', 'role', 'organization'

    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'admin', 'user'

    max_discount_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    max_discount_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    minimum_unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    minimum_margin_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    product: Mapped[Optional["Product"]] = relationship("Product")
    customer: Mapped[Optional["Customer"]] = relationship("Customer")
    user: Mapped[Optional["User"]] = relationship("User")

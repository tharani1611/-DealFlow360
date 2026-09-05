import uuid
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, Integer, Boolean, ForeignKey, UniqueConstraint, CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.product import Product


class ProductRecommendationRule(Base, UUIDMixin, TimestampMixin):
    """Product Recommendation Rule for Upsell and Cross-sell intelligence."""
    __tablename__ = "product_recommendation_rules"

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "source_product_id", "target_product_id", "rule_type",
            name="uq_product_rec_rules_org_src_tgt_type"
        ),
        CheckConstraint("source_product_id != target_product_id", name="check_source_ne_target"),
        CheckConstraint("rule_type IN ('upsell', 'cross_sell')", name="check_valid_rule_type"),
        CheckConstraint("priority > 0", name="check_priority_positive"),
        Index("ix_product_rec_rules_org_src", "organization_id", "source_product_id"),
        Index("ix_product_rec_rules_org_active", "organization_id", "is_active"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    source_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    target_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'upsell', 'cross_sell'
    priority: Mapped[int] = mapped_column(Integer, default=5, server_default=text("5"), nullable=False)  # 1 = Highest
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)

    min_customer_deal_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_customer_pipeline_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    min_customer_activity_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    source_product: Mapped["Product"] = relationship("Product", foreign_keys=[source_product_id])
    target_product: Mapped["Product"] = relationship("Product", foreign_keys=[target_product_id])

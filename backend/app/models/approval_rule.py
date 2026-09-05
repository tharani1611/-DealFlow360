import uuid
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, Integer, Boolean, ForeignKey, CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class ApprovalRule(Base, UUIDMixin, TimestampMixin):
    """ApprovalRule model defining commercial rules triggering authorization requirements."""
    __tablename__ = "approval_rules"

    __table_args__ = (
        CheckConstraint("priority > 0", name="ck_approval_rules_priority_positive"),
        CheckConstraint("approval_level > 0", name="ck_approval_rules_level_positive"),
        CheckConstraint("min_discount_percent IS NULL OR (min_discount_percent >= 0 AND min_discount_percent <= 100)", name="ck_approval_rules_min_disc_valid"),
        CheckConstraint("max_discount_percent IS NULL OR (max_discount_percent >= 0 AND max_discount_percent <= 100)", name="ck_approval_rules_max_disc_valid"),
        CheckConstraint("quotation_value_threshold IS NULL OR quotation_value_threshold >= 0", name="ck_approval_rules_val_thresh_valid"),
        Index("ix_approval_rules_org_active", "organization_id", "is_active"),
        Index("ix_approval_rules_lookup", "organization_id", "is_active", "priority"),
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

    min_discount_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    max_discount_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    min_margin_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    quotation_value_threshold: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    approval_level: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    required_role: Mapped[str] = mapped_column(String(50), default="admin", server_default="admin", nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")

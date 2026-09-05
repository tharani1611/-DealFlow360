import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.quotation import Quotation
    from app.models.approval_rule import ApprovalRule
    from app.models.user import User


class QuotationApproval(Base, UUIDMixin, TimestampMixin):
    """QuotationApproval model for tracking approval requests and decisions on quotations."""
    __tablename__ = "quotation_approvals"

    __table_args__ = (
        Index("ix_quotation_approvals_org_quotation", "organization_id", "quotation_id"),
        Index("ix_quotation_approvals_status", "status"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    approval_rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approval_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    approved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Status: 'NOT_REQUIRED', 'PENDING', 'APPROVED', 'REJECTED', 'INVALIDATED'
    status: Mapped[str] = mapped_column(String(30), default="PENDING", server_default="PENDING", nullable=False)
    approval_level: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    reasons: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Detailed rules or reasons triggering approval
    decision_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="approvals")
    approval_rule: Mapped[Optional["ApprovalRule"]] = relationship("ApprovalRule")
    requested_by_user: Mapped["User"] = relationship("User", foreign_keys=[requested_by_user_id])
    approved_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_user_id])

import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, ForeignKey, text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.quotation import Quotation
    from app.models.quotation_approval import QuotationApproval
    from app.models.user import User
    from app.models.approval_rule import ApprovalRule


class ApprovalAuditLog(Base, UUIDMixin):
    """Append-only audit trail log for quotation approval workflow actions and status transitions."""
    __tablename__ = "approval_audit_logs"

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
    approval_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotation_approvals.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    actor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    previous_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approval_rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approval_rules.id", ondelete="SET NULL"),
        nullable=True
    )
    approval_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()")
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    quotation: Mapped["Quotation"] = relationship("Quotation")
    approval: Mapped[Optional["QuotationApproval"]] = relationship("QuotationApproval")
    actor_user: Mapped[Optional["User"]] = relationship("User")
    approval_rule: Mapped[Optional["ApprovalRule"]] = relationship("ApprovalRule")

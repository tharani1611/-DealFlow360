import uuid
from typing import Optional, Any, Dict, List, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User
    from app.models.automation_execution import AutomationExecution


class AutomationRule(Base, UUIDMixin, TimestampMixin):
    """AutomationRule model defining trigger types, conditions, actions, and priority."""
    __tablename__ = "automation_rules"

    __table_args__ = (
        Index("ix_automation_rules_org_status", "organization_id", "status"),
        Index("ix_automation_rules_org_trigger", "organization_id", "trigger_type"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="DRAFT",
        server_default="DRAFT",
        nullable=False,
        index=True
    )  # 'DRAFT', 'ACTIVE', 'PAUSED', 'ARCHIVED'

    priority: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    conditions: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)
    actions: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list, server_default="[]", nullable=False)

    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    updated_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    created_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id])
    executions: Mapped[List["AutomationExecution"]] = relationship("AutomationExecution", back_populates="rule", cascade="all, delete-orphan")

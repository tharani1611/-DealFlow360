import uuid
from datetime import datetime
from typing import Optional, Any, Dict, List, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, Index, text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.automation_rule import AutomationRule


class AutomationExecution(Base, UUIDMixin):
    """AutomationExecution model tracking workflow triggers, matched conditions, actions, and audit statuses."""
    __tablename__ = "automation_executions"

    __table_args__ = (
        Index("ix_automation_executions_org_rule", "organization_id", "rule_id"),
        Index("ix_automation_executions_org_status", "organization_id", "status"),
        Index("ix_automation_executions_idempotency", "organization_id", "idempotency_key"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automation_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        server_default="PENDING",
        nullable=False,
        index=True
    )  # 'PENDING', 'RUNNING', 'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'SKIPPED', 'CANCELLED'

    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    conditions_matched: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    actions_total: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    actions_succeeded: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    actions_failed: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    trigger_context: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    rule: Mapped["AutomationRule"] = relationship("AutomationRule", back_populates="executions")
    actions: Mapped[List["AutomationExecutionAction"]] = relationship("AutomationExecutionAction", back_populates="execution", cascade="all, delete-orphan")


class AutomationExecutionAction(Base, UUIDMixin):
    """AutomationExecutionAction model tracking individual action outcomes within a workflow execution."""
    __tablename__ = "automation_execution_actions"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automation_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="SUCCESS", server_default="SUCCESS", nullable=False)  # 'SUCCESS', 'FAILED', 'SKIPPED'
    result_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    # Relationships
    execution: Mapped["AutomationExecution"] = relationship("AutomationExecution", back_populates="actions")

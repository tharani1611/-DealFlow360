import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class AutomationCondition(BaseModel):
    """Single condition evaluation unit."""
    field: str = Field(..., description="Entity or context attribute e.g. 'deal.value', 'deal.stage', 'customer.segment'")
    operator: str = Field(..., description="Operator: 'equals', 'not_equals', 'greater_than', 'greater_than_or_equal', 'less_than', 'less_than_or_equal', 'contains', 'not_contains', 'in', 'not_in', 'is_empty', 'is_not_empty'")
    value: Optional[Any] = Field(None, description="Target comparison value")


class AutomationConditionGroup(BaseModel):
    """Logical grouping of conditions with AND/OR support."""
    logical_operator: str = Field("AND", description="'AND' or 'OR'")
    conditions: List[AutomationCondition] = Field(default_factory=list)
    groups: List["AutomationConditionGroup"] = Field(default_factory=list)


class AutomationAction(BaseModel):
    """Workflow action definition."""
    action_type: str = Field(..., description="e.g. 'CREATE_ACTIVITY', 'CREATE_TASK', 'ASSIGN_DEAL', 'ASSIGN_CUSTOMER', 'ADD_NOTE', 'SEND_NOTIFICATION', 'UPDATE_DEAL_FIELD'")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters e.g. title, priority, assigned_to_user_id, status")


class AutomationRuleCreate(BaseModel):
    """Automation Rule Creation Payload."""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    trigger_type: str = Field(..., description="e.g. 'DEAL_STAGE_CHANGED', 'QUOTATION_EXPIRED', 'ACTIVITY_OVERDUE', 'DEAL_CREATED'")
    priority: int = Field(0, ge=0, le=1000)
    conditions: AutomationConditionGroup = Field(default_factory=AutomationConditionGroup)
    actions: List[AutomationAction] = Field(..., min_length=1)


class AutomationRuleUpdate(BaseModel):
    """Automation Rule Update Payload."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    trigger_type: Optional[str] = None
    priority: Optional[int] = Field(None, ge=0, le=1000)
    status: Optional[str] = Field(None, description="'DRAFT', 'ACTIVE', 'PAUSED', 'ARCHIVED'")
    conditions: Optional[AutomationConditionGroup] = None
    actions: Optional[List[AutomationAction]] = None


class AutomationRuleResponse(BaseModel):
    """Automation Rule Full Response."""
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: str
    priority: int
    trigger_type: str
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    created_by_user_id: Optional[uuid.UUID] = None
    updated_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class EventContext(BaseModel):
    """Standardized event context payload passed into trigger evaluation."""
    organization_id: uuid.UUID
    event_type: str
    entity_type: str
    entity_id: uuid.UUID
    actor_user_id: Optional[uuid.UUID] = None
    previous_state: Optional[Dict[str, Any]] = None
    current_state: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
    event_id: Optional[str] = None


class AutomationExecutionActionResponse(BaseModel):
    """Action outcome log response."""
    id: uuid.UUID
    execution_id: uuid.UUID
    action_type: str
    status: str
    result_payload: Dict[str, Any]
    error_message: Optional[str] = None
    executed_at: datetime


class AutomationExecutionResponse(BaseModel):
    """Workflow execution audit response."""
    id: uuid.UUID
    organization_id: uuid.UUID
    rule_id: uuid.UUID
    rule_name: Optional[str] = None
    event_type: str
    entity_type: str
    entity_id: uuid.UUID
    status: str
    idempotency_key: str
    conditions_matched: bool
    actions_total: int
    actions_succeeded: int
    actions_failed: int
    error_message: Optional[str] = None
    retry_count: int
    trigger_context: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    actions: List[AutomationExecutionActionResponse] = Field(default_factory=list)


class AutomationAnalyticsSummary(BaseModel):
    """Automation Engine Executive Operational Analytics Summary."""
    total_rules: int
    active_rules: int
    paused_rules: int
    draft_rules: int
    executions_today: int
    successful_executions: int
    failed_executions: int
    skipped_executions: int
    success_rate_percent: float


class AIRuleRecommendation(BaseModel):
    """AI Recommended Automation Rule based on CRM patterns."""
    rule_name: str
    description: str
    trigger_type: str
    reason: str
    recommended_conditions: AutomationConditionGroup
    recommended_actions: List[AutomationAction]

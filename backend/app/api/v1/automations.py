import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.automation_rule import AutomationRule
from app.models.automation_execution import AutomationExecution
from app.core.exceptions import NotFoundException
from app.schemas.automation import (
    AutomationRuleCreate,
    AutomationRuleUpdate,
    AutomationRuleResponse,
    AutomationExecutionResponse,
    AutomationExecutionActionResponse,
    AutomationAnalyticsSummary,
    AIRuleRecommendation
)
from app.services import automation_engine

router = APIRouter()


@router.post(
    "",
    response_model=AutomationRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Automation Rule",
    description="Creates a new tenant-isolated automation rule in DRAFT status."
)
async def create_rule(
    payload: AutomationRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AutomationRuleResponse:
    """Creates a new automation rule."""
    rule = await automation_engine.create_automation_rule(
        db, current_user.organization_id, current_user.id, payload
    )
    return rule


@router.get(
    "",
    response_model=List[AutomationRuleResponse],
    status_code=status.HTTP_200_OK,
    summary="List Automation Rules",
    description="Retrieves list of automation rules for the tenant."
)
async def list_rules(
    status_filter: Optional[str] = Query(None, alias="status"),
    trigger_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[AutomationRuleResponse]:
    """Lists automation rules for the current tenant."""
    conditions = [AutomationRule.organization_id == current_user.organization_id]
    if status_filter:
        conditions.append(AutomationRule.status == status_filter)
    if trigger_type:
        conditions.append(AutomationRule.trigger_type == trigger_type)

    stmt = select(AutomationRule).where(and_(*conditions)).order_by(AutomationRule.priority.desc(), AutomationRule.created_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get(
    "/analytics/summary",
    response_model=AutomationAnalyticsSummary,
    status_code=status.HTTP_200_OK,
    summary="Get Automation Analytics Summary",
    description="Calculates operational KPIs and execution metrics for tenant workflows."
)
async def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AutomationAnalyticsSummary:
    """Retrieves operational analytics summary for tenant automations."""
    return await automation_engine.get_automation_analytics_summary(db, current_user.organization_id)


@router.get(
    "/ai-recommendations",
    response_model=List[AIRuleRecommendation],
    status_code=status.HTTP_200_OK,
    summary="Get AI Rule Recommendations",
    description="Generates AI recommendations for automation rules based on CRM patterns."
)
async def get_ai_rule_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[AIRuleRecommendation]:
    """Retrieves AI recommended automation rules."""
    return await automation_engine.generate_ai_rule_recommendations(db, current_user.organization_id)


@router.get(
    "/executions",
    response_model=List[AutomationExecutionResponse],
    status_code=status.HTTP_200_OK,
    summary="List Workflow Executions History",
    description="Retrieves execution audit logs for tenant workflows."
)
async def list_executions(
    rule_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    event_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[AutomationExecutionResponse]:
    """Lists workflow execution audit history."""
    conditions = [AutomationExecution.organization_id == current_user.organization_id]
    if rule_id:
        conditions.append(AutomationExecution.rule_id == rule_id)
    if status_filter:
        conditions.append(AutomationExecution.status == status_filter)
    if event_type:
        conditions.append(AutomationExecution.event_type == event_type)

    stmt = (
        select(AutomationExecution)
        .options(selectinload(AutomationExecution.rule), selectinload(AutomationExecution.actions))
        .where(and_(*conditions))
        .order_by(desc(AutomationExecution.started_at))
        .limit(100)
    )
    res = await db.execute(stmt)
    execs = list(res.scalars().all())

    out: List[AutomationExecutionResponse] = []
    for e in execs:
        action_responses = [
            AutomationExecutionActionResponse(
                id=a.id,
                execution_id=a.execution_id,
                action_type=a.action_type,
                status=a.status,
                result_payload=a.result_payload,
                error_message=a.error_message,
                executed_at=a.executed_at
            ) for a in e.actions
        ]

        out.append(AutomationExecutionResponse(
            id=e.id,
            organization_id=e.organization_id,
            rule_id=e.rule_id,
            rule_name=e.rule.name if e.rule else "Deleted Rule",
            event_type=e.event_type,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            status=e.status,
            idempotency_key=e.idempotency_key,
            conditions_matched=e.conditions_matched,
            actions_total=e.actions_total,
            actions_succeeded=e.actions_succeeded,
            actions_failed=e.actions_failed,
            error_message=e.error_message,
            retry_count=e.retry_count,
            trigger_context=e.trigger_context,
            started_at=e.started_at,
            completed_at=e.completed_at,
            actions=action_responses
        ))

    return out


@router.get(
    "/executions/{execution_id}",
    response_model=AutomationExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Workflow Execution Audit Detail",
    description="Retrieves detailed execution trace for a single workflow execution."
)
async def get_execution_detail(
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AutomationExecutionResponse:
    """Retrieves detailed execution trace."""
    stmt = (
        select(AutomationExecution)
        .options(selectinload(AutomationExecution.rule), selectinload(AutomationExecution.actions))
        .where(
            and_(
                AutomationExecution.id == execution_id,
                AutomationExecution.organization_id == current_user.organization_id
            )
        )
    )
    res = await db.execute(stmt)
    e = res.scalar_one_or_none()
    if not e:
        raise NotFoundException(f"Automation Execution with ID {execution_id} was not found.")

    action_responses = [
        AutomationExecutionActionResponse(
            id=a.id,
            execution_id=a.execution_id,
            action_type=a.action_type,
            status=a.status,
            result_payload=a.result_payload,
            error_message=a.error_message,
            executed_at=a.executed_at
        ) for a in e.actions
    ]

    return AutomationExecutionResponse(
        id=e.id,
        organization_id=e.organization_id,
        rule_id=e.rule_id,
        rule_name=e.rule.name if e.rule else "Deleted Rule",
        event_type=e.event_type,
        entity_type=e.entity_type,
        entity_id=e.entity_id,
        status=e.status,
        idempotency_key=e.idempotency_key,
        conditions_matched=e.conditions_matched,
        actions_total=e.actions_total,
        actions_succeeded=e.actions_succeeded,
        actions_failed=e.actions_failed,
        error_message=e.error_message,
        retry_count=e.retry_count,
        trigger_context=e.trigger_context,
        started_at=e.started_at,
        completed_at=e.completed_at,
        actions=action_responses
    )


@router.post(
    "/executions/{execution_id}/retry",
    response_model=AutomationExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retry Workflow Execution",
    description="Retries a failed or partial success execution."
)
async def retry_execution(
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AutomationExecutionResponse:
    """Retries workflow execution."""
    e = await automation_engine.retry_automation_execution(db, current_user.organization_id, execution_id)
    return await get_execution_detail(execution_id, current_user, db)


@router.get(
    "/{rule_id}",
    response_model=AutomationRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Automation Rule Detail",
    description="Retrieves a single automation rule by ID."
)
async def get_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AutomationRuleResponse:
    """Gets automation rule detail."""
    stmt = select(AutomationRule).where(
        and_(AutomationRule.id == rule_id, AutomationRule.organization_id == current_user.organization_id)
    )
    res = await db.execute(stmt)
    rule = res.scalar_one_or_none()
    if not rule:
        raise NotFoundException(f"Automation Rule with ID {rule_id} was not found.")
    return rule


@router.put(
    "/{rule_id}",
    response_model=AutomationRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Automation Rule",
    description="Updates automation rule fields."
)
async def update_rule(
    rule_id: uuid.UUID,
    payload: AutomationRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AutomationRuleResponse:
    """Updates automation rule."""
    return await automation_engine.update_automation_rule(
        db, current_user.organization_id, current_user.id, rule_id, payload
    )


@router.post(
    "/{rule_id}/activate",
    response_model=AutomationRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate Automation Rule",
    description="Activates an automation rule after verifying pre-activation conditions."
)
async def activate_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AutomationRuleResponse:
    """Activates automation rule."""
    return await automation_engine.set_rule_status(
        db, current_user.organization_id, current_user.id, rule_id, "ACTIVE"
    )


@router.post(
    "/{rule_id}/pause",
    response_model=AutomationRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Pause Automation Rule",
    description="Pauses an active automation rule."
)
async def pause_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AutomationRuleResponse:
    """Pauses automation rule."""
    return await automation_engine.set_rule_status(
        db, current_user.organization_id, current_user.id, rule_id, "PAUSED"
    )


@router.post(
    "/{rule_id}/archive",
    response_model=AutomationRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive Automation Rule",
    description="Archives an automation rule."
)
async def archive_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AutomationRuleResponse:
    """Archives automation rule."""
    return await automation_engine.set_rule_status(
        db, current_user.organization_id, current_user.id, rule_id, "ARCHIVED"
    )


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Automation Rule",
    description="Deletes an automation rule."
)
async def delete_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes automation rule."""
    stmt = select(AutomationRule).where(
        and_(AutomationRule.id == rule_id, AutomationRule.organization_id == current_user.organization_id)
    )
    res = await db.execute(stmt)
    rule = res.scalar_one_or_none()
    if not rule:
        raise NotFoundException(f"Automation Rule with ID {rule_id} was not found.")

    await db.delete(rule)
    await db.flush()

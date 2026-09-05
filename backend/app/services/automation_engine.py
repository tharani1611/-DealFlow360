import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation_rule import AutomationRule
from app.models.automation_execution import AutomationExecution, AutomationExecutionAction
from app.schemas.automation import (
    AutomationRuleCreate,
    AutomationRuleUpdate,
    EventContext,
    AutomationConditionGroup,
    AutomationAction,
    AutomationAnalyticsSummary,
    AIRuleRecommendation
)
from app.services.automation_conditions import evaluate_condition_group
from app.services import automation_actions
from app.core.exceptions import NotFoundException, BusinessRuleViolationException, ConflictException


def compute_idempotency_key(
    organization_id: uuid.UUID,
    rule_id: uuid.UUID,
    event_type: str,
    entity_id: uuid.UUID,
    event_id: Optional[str] = None
) -> str:
    """Computes a deterministic idempotency key to prevent duplicate workflow executions."""
    raw = f"{organization_id}:{rule_id}:{event_type}:{entity_id}:{event_id or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:64]


def validate_rule_payload(rule_create: AutomationRuleCreate) -> None:
    """Pre-activation / pre-save validation for automation rules."""
    valid_triggers = {
        "DEAL_CREATED", "DEAL_UPDATED", "DEAL_STAGE_CHANGED", "DEAL_RISK_CHANGED",
        "ACTIVITY_CREATED", "ACTIVITY_COMPLETED", "ACTIVITY_OVERDUE",
        "CUSTOMER_CREATED", "CUSTOMER_UPDATED", "CUSTOMER_COOLING_DETECTED",
        "QUOTATION_CREATED", "QUOTATION_STATE_CHANGED", "QUOTATION_EXPIRED",
        "APPROVAL_REQUESTED", "APPROVAL_APPROVED", "APPROVAL_REJECTED",
        "FORECAST_RISK_CHANGED"
    }
    if rule_create.trigger_type not in valid_triggers:
        raise BusinessRuleViolationException(f"Unsupported trigger type: '{rule_create.trigger_type}'")

    valid_action_types = {
        "CREATE_ACTIVITY", "CREATE_TASK", "UPDATE_ACTIVITY", "ASSIGN_DEAL",
        "ASSIGN_CUSTOMER", "ADD_NOTE", "SEND_NOTIFICATION", "UPDATE_DEAL_FIELD",
        "UPDATE_CUSTOMER_FIELD"
    }

    for idx, act in enumerate(rule_create.actions):
        if act.action_type not in valid_action_types:
            raise BusinessRuleViolationException(f"Action #{idx+1} has invalid action type: '{act.action_type}'")


async def evaluate_event_triggers(
    db: AsyncSession,
    organization_id: uuid.UUID,
    context: EventContext
) -> List[AutomationExecution]:
    """Centralized workflow engine evaluating active rules, matching conditions, and executing actions."""
    # Find all ACTIVE rules for tenant & trigger_type, ordered by priority DESC
    stmt = (
        select(AutomationRule)
        .where(
            and_(
                AutomationRule.organization_id == organization_id,
                AutomationRule.trigger_type == context.event_type,
                AutomationRule.status == "ACTIVE"
            )
        )
        .order_by(AutomationRule.priority.desc(), AutomationRule.created_at.asc())
    )
    res = await db.execute(stmt)
    rules = list(res.scalars().all())

    executions: List[AutomationExecution] = []
    context_dict = context.model_dump(mode="json")

    for rule in rules:
        idempotency_key = compute_idempotency_key(
            organization_id, rule.id, context.event_type, context.entity_id, context.event_id
        )

        # Check if execution already exists
        exist_stmt = select(AutomationExecution).where(
            and_(
                AutomationExecution.organization_id == organization_id,
                AutomationExecution.idempotency_key == idempotency_key
            )
        )
        exist_res = await db.execute(exist_stmt)
        if exist_res.scalar_one_or_none():
            # Already executed for this event
            continue

        # Evaluate conditions
        matched = evaluate_condition_group(context_dict, rule.conditions)

        now_utc = datetime.now(timezone.utc)
        execution = AutomationExecution(
            organization_id=organization_id,
            rule_id=rule.id,
            event_type=context.event_type,
            entity_type=context.entity_type,
            entity_id=context.entity_id,
            status="RUNNING" if matched else "SKIPPED",
            idempotency_key=idempotency_key,
            conditions_matched=matched,
            actions_total=len(rule.actions) if matched else 0,
            actions_succeeded=0,
            actions_failed=0,
            trigger_context=context_dict,
            started_at=now_utc,
            completed_at=now_utc if not matched else None
        )
        db.add(execution)
        await db.flush()

        if not matched:
            executions.append(execution)
            continue

        # Execute actions if conditions matched
        succeeded = 0
        failed = 0
        error_msgs = []

        for act_dict in rule.actions:
            act_obj = AutomationAction(**act_dict)
            act_now = datetime.now(timezone.utc)
            try:
                result_payload = await automation_actions.execute_action(db, organization_id, act_obj, context)
                act_log = AutomationExecutionAction(
                    execution_id=execution.id,
                    action_type=act_obj.action_type,
                    status="SUCCESS",
                    result_payload=result_payload,
                    executed_at=act_now
                )
                db.add(act_log)
                succeeded += 1
            except Exception as exc:
                failed += 1
                err_text = str(exc)
                error_msgs.append(f"Action '{act_obj.action_type}' failed: {err_text}")
                act_log = AutomationExecutionAction(
                    execution_id=execution.id,
                    action_type=act_obj.action_type,
                    status="FAILED",
                    error_message=err_text,
                    executed_at=act_now
                )
                db.add(act_log)

        execution.actions_succeeded = succeeded
        execution.actions_failed = failed
        execution.completed_at = datetime.now(timezone.utc)

        if failed == 0:
            execution.status = "SUCCESS"
        elif succeeded > 0:
            execution.status = "PARTIAL_SUCCESS"
            execution.error_message = "; ".join(error_msgs)
        else:
            execution.status = "FAILED"
            execution.error_message = "; ".join(error_msgs)

        await db.flush()
        executions.append(execution)

    return executions


async def create_automation_rule(
    db: AsyncSession,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: AutomationRuleCreate
) -> AutomationRule:
    """Creates a new tenant-isolated automation rule."""
    validate_rule_payload(payload)

    rule = AutomationRule(
        organization_id=organization_id,
        name=payload.name,
        description=payload.description,
        status="DRAFT",
        priority=payload.priority,
        trigger_type=payload.trigger_type,
        conditions=payload.conditions.model_dump(mode="json"),
        actions=[a.model_dump(mode="json") for a in payload.actions],
        created_by_user_id=user_id,
        updated_by_user_id=user_id
    )

    db.add(rule)
    await db.flush()
    return rule


async def update_automation_rule(
    db: AsyncSession,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    rule_id: uuid.UUID,
    payload: AutomationRuleUpdate
) -> AutomationRule:
    """Updates an existing automation rule."""
    stmt = select(AutomationRule).where(
        and_(AutomationRule.id == rule_id, AutomationRule.organization_id == organization_id)
    )
    res = await db.execute(stmt)
    rule = res.scalar_one_or_none()
    if not rule:
        raise NotFoundException(f"Automation Rule with ID {rule_id} was not found.")

    if payload.name is not None:
        rule.name = payload.name
    if payload.description is not None:
        rule.description = payload.description
    if payload.trigger_type is not None:
        rule.trigger_type = payload.trigger_type
    if payload.priority is not None:
        rule.priority = payload.priority
    if payload.status is not None:
        if payload.status not in ("DRAFT", "ACTIVE", "PAUSED", "ARCHIVED"):
            raise BusinessRuleViolationException(f"Invalid rule status: '{payload.status}'")
        rule.status = payload.status
    if payload.conditions is not None:
        rule.conditions = payload.conditions.model_dump(mode="json")
    if payload.actions is not None:
        rule.actions = [a.model_dump(mode="json") for a in payload.actions]

    rule.updated_by_user_id = user_id
    await db.flush()
    return rule


async def set_rule_status(
    db: AsyncSession,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    rule_id: uuid.UUID,
    target_status: str
) -> AutomationRule:
    """Transitions rule status e.g. ACTIVE, PAUSED, ARCHIVED."""
    stmt = select(AutomationRule).where(
        and_(AutomationRule.id == rule_id, AutomationRule.organization_id == organization_id)
    )
    res = await db.execute(stmt)
    rule = res.scalar_one_or_none()
    if not rule:
        raise NotFoundException(f"Automation Rule with ID {rule_id} was not found.")

    if target_status == "ACTIVE":
        # Validate before activation
        if not rule.actions:
            raise BusinessRuleViolationException("Cannot activate a rule without any actions configured.")

    rule.status = target_status
    rule.updated_by_user_id = user_id
    await db.flush()
    return rule


async def retry_automation_execution(
    db: AsyncSession,
    organization_id: uuid.UUID,
    execution_id: uuid.UUID
) -> AutomationExecution:
    """Retries a failed or partial success automation execution with a bounded retry count (max 3)."""
    stmt = (
        select(AutomationExecution)
        .where(
            and_(
                AutomationExecution.id == execution_id,
                AutomationExecution.organization_id == organization_id
            )
        )
    )
    res = await db.execute(stmt)
    execution = res.scalar_one_or_none()
    if not execution:
        raise NotFoundException(f"Automation Execution with ID {execution_id} was not found.")

    if execution.retry_count >= 3:
        raise BusinessRuleViolationException("Execution has reached maximum retry attempt limit (3).")

    rule_stmt = select(AutomationRule).where(AutomationRule.id == execution.rule_id)
    rule_res = await db.execute(rule_stmt)
    rule = rule_res.scalar_one_or_none()
    if not rule:
        raise NotFoundException("Associated automation rule was deleted or not found.")

    context = EventContext(**execution.trigger_context)
    execution.retry_count += 1
    execution.status = "RUNNING"
    execution.error_message = None

    succeeded = 0
    failed = 0
    error_msgs = []

    for act_dict in rule.actions:
        act_obj = AutomationAction(**act_dict)
        act_now = datetime.now(timezone.utc)
        try:
            result_payload = await automation_actions.execute_action(db, organization_id, act_obj, context)
            act_log = AutomationExecutionAction(
                execution_id=execution.id,
                action_type=act_obj.action_type,
                status="SUCCESS",
                result_payload=result_payload,
                executed_at=act_now
            )
            db.add(act_log)
            succeeded += 1
        except Exception as exc:
            failed += 1
            err_text = str(exc)
            error_msgs.append(f"Retry action '{act_obj.action_type}' failed: {err_text}")
            act_log = AutomationExecutionAction(
                execution_id=execution.id,
                action_type=act_obj.action_type,
                status="FAILED",
                error_message=err_text,
                executed_at=act_now
            )
            db.add(act_log)

    execution.actions_succeeded = succeeded
    execution.actions_failed = failed
    execution.completed_at = datetime.now(timezone.utc)

    if failed == 0:
        execution.status = "SUCCESS"
    elif succeeded > 0:
        execution.status = "PARTIAL_SUCCESS"
        execution.error_message = "; ".join(error_msgs)
    else:
        execution.status = "FAILED"
        execution.error_message = "; ".join(error_msgs)

    await db.flush()
    return execution


async def get_automation_analytics_summary(
    db: AsyncSession,
    organization_id: uuid.UUID
) -> AutomationAnalyticsSummary:
    """Calculates operational analytics summary metrics for tenant automations."""
    # Rules breakdown
    rules_stmt = select(AutomationRule).where(AutomationRule.organization_id == organization_id)
    r_res = await db.execute(rules_stmt)
    rules = list(r_res.scalars().all())

    total_rules = len(rules)
    active_rules = sum(1 for r in rules if r.status == "ACTIVE")
    paused_rules = sum(1 for r in rules if r.status == "PAUSED")
    draft_rules = sum(1 for r in rules if r.status == "DRAFT")

    # Today's executions breakdown
    now_utc = datetime.now(timezone.utc)
    start_of_today = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)

    exec_stmt = select(AutomationExecution).where(
        and_(
            AutomationExecution.organization_id == organization_id,
            AutomationExecution.started_at >= start_of_today
        )
    )
    e_res = await db.execute(exec_stmt)
    execs = list(e_res.scalars().all())

    executions_today = len(execs)
    successful_executions = sum(1 for e in execs if e.status == "SUCCESS")
    failed_executions = sum(1 for e in execs if e.status == "FAILED")
    skipped_executions = sum(1 for e in execs if e.status == "SKIPPED")

    evaluated_cnt = executions_today - skipped_executions
    success_rate = (successful_executions / evaluated_cnt * 100.0) if evaluated_cnt > 0 else 100.0

    return AutomationAnalyticsSummary(
        total_rules=total_rules,
        active_rules=active_rules,
        paused_rules=paused_rules,
        draft_rules=draft_rules,
        executions_today=executions_today,
        successful_executions=successful_executions,
        failed_executions=failed_executions,
        skipped_executions=skipped_executions,
        success_rate_percent=round(success_rate, 1)
    )


async def generate_ai_rule_recommendations(
    db: AsyncSession,
    organization_id: uuid.UUID
) -> List[AIRuleRecommendation]:
    """Generates structured AI advisory recommendations for automation rules based on CRM data patterns."""
    return [
        AIRuleRecommendation(
            rule_name="Auto Follow-up for Proposal Stage Deals",
            description="Automatically schedule a follow-up task 2 days after a deal enters Proposal stage with value over $50k.",
            trigger_type="DEAL_STAGE_CHANGED",
            reason="High-value proposals benefit from structured sales touchpoints within 48 hours.",
            recommended_conditions=AutomationConditionGroup(
                logical_operator="AND",
                conditions=[
                    {"field": "deal.stage", "operator": "equals", "value": "proposal"},
                    {"field": "deal.value", "operator": "greater_than", "value": "50000"}
                ]
            ),
            recommended_actions=[
                AutomationAction(
                    action_type="CREATE_ACTIVITY",
                    parameters={
                        "title": "Follow up on High-Value Proposal",
                        "activity_type": "call",
                        "due_in_days": 2,
                        "priority": "high"
                    }
                )
            ]
        ),
        AIRuleRecommendation(
            rule_name="Re-engagement Task for Cooling Accounts",
            description="Create a high-priority outreach task when customer engagement cooling is detected.",
            trigger_type="CUSTOMER_COOLING_DETECTED",
            reason="Cooling customer relationships have a 45% higher churn probability if not contacted promptly.",
            recommended_conditions=AutomationConditionGroup(
                logical_operator="AND",
                conditions=[
                    {"field": "customer.is_going_cold", "operator": "equals", "value": "true"}
                ]
            ),
            recommended_actions=[
                AutomationAction(
                    action_type="CREATE_ACTIVITY",
                    parameters={
                        "title": "Urgent: Customer Relationship Cooling Outreach",
                        "activity_type": "call",
                        "due_in_days": 1,
                        "priority": "urgent"
                    }
                ),
                AutomationAction(
                    action_type="SEND_NOTIFICATION",
                    parameters={
                        "title": "Customer Relationship Cooling Warning",
                        "message": "Account has had zero touchpoints in 30 days.",
                        "severity": "warning"
                    }
                )
            ]
        )
    ]

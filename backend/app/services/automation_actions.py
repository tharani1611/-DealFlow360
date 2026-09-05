import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.deal import Deal
from app.models.customer import Customer
from app.models.user import User
from app.schemas.automation import AutomationAction, EventContext
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


async def _get_fallback_user_id(db: AsyncSession, organization_id: uuid.UUID, actor_user_id: Optional[uuid.UUID]) -> uuid.UUID:
    if actor_user_id:
        return actor_user_id
    u_res = await db.execute(select(User.id).where(User.organization_id == organization_id))
    u_id = u_res.scalars().first()
    if u_id:
        return u_id
    raise BusinessRuleViolationException("No active user found in organization for workflow action.")


async def execute_action(
    db: AsyncSession,
    organization_id: uuid.UUID,
    action: AutomationAction,
    context: EventContext
) -> Dict[str, Any]:
    """Executes a single deterministic workflow action in a safe, tenant-isolated manner."""
    action_type = action.action_type.upper()
    params = action.parameters or {}

    if action_type in ("CREATE_ACTIVITY", "CREATE_TASK"):
        return await _execute_create_activity(db, organization_id, action_type, params, context)
    elif action_type == "UPDATE_ACTIVITY":
        return await _execute_update_activity(db, organization_id, params, context)
    elif action_type == "ASSIGN_DEAL":
        return await _execute_assign_deal(db, organization_id, params, context)
    elif action_type == "ASSIGN_CUSTOMER":
        return await _execute_assign_customer(db, organization_id, params, context)
    elif action_type == "ADD_NOTE":
        return await _execute_add_note(db, organization_id, params, context)
    elif action_type == "SEND_NOTIFICATION":
        return await _execute_send_notification(db, organization_id, params, context)
    elif action_type == "UPDATE_DEAL_FIELD":
        return await _execute_update_deal_field(db, organization_id, params, context)
    elif action_type == "UPDATE_CUSTOMER_FIELD":
        return await _execute_update_customer_field(db, organization_id, params, context)
    else:
        raise BusinessRuleViolationException(f"Unsupported automation action type: '{action_type}'")


async def _execute_create_activity(
    db: AsyncSession,
    organization_id: uuid.UUID,
    action_type: str,
    params: Dict[str, Any],
    context: EventContext
) -> Dict[str, Any]:
    act_type = params.get("activity_type", "task" if action_type == "CREATE_TASK" else "follow_up")
    title = params.get("title", f"Automated Task: {context.event_type.replace('_', ' ').title()}")
    desc = params.get("description", f"Generated automatically by DealFlow360 Workflow Rule for {context.entity_type} {context.entity_id}")
    priority = params.get("priority", "medium")

    # Target entity linking
    deal_id = uuid.UUID(str(params["deal_id"])) if "deal_id" in params and params["deal_id"] else (context.entity_id if context.entity_type == "deal" else None)
    customer_id = uuid.UUID(str(params["customer_id"])) if "customer_id" in params and params["customer_id"] else (context.entity_id if context.entity_type == "customer" else None)
    quotation_id = uuid.UUID(str(params["quotation_id"])) if "quotation_id" in params and params["quotation_id"] else (context.entity_id if context.entity_type == "quotation" else None)

    # Derive customer_id from deal if available
    if deal_id and not customer_id:
        d_res = await db.execute(select(Deal).where(Deal.id == deal_id, Deal.organization_id == organization_id))
        d_obj = d_res.scalar_one_or_none()
        if d_obj:
            customer_id = d_obj.customer_id

    # Due date calculation
    due_days = int(params.get("due_in_days", 1))
    due_at = datetime.now(timezone.utc) + timedelta(days=due_days)

    creator_user_id = await _get_fallback_user_id(db, organization_id, context.actor_user_id)

    activity = Activity(
        organization_id=organization_id,
        activity_type=act_type,
        title=title,
        description=desc,
        status="pending",
        priority=priority,
        customer_id=customer_id,
        deal_id=deal_id,
        quotation_id=quotation_id,
        assigned_to_user_id=uuid.UUID(str(params["assigned_to_user_id"])) if params.get("assigned_to_user_id") else creator_user_id,
        created_by_user_id=creator_user_id,
        due_at=due_at
    )

    db.add(activity)
    await db.flush()

    return {
        "created_activity_id": str(activity.id),
        "title": activity.title,
        "activity_type": activity.activity_type,
        "due_at": activity.due_at.isoformat() if activity.due_at else None
    }


async def _execute_update_activity(
    db: AsyncSession,
    organization_id: uuid.UUID,
    params: Dict[str, Any],
    context: EventContext
) -> Dict[str, Any]:
    act_id = uuid.UUID(str(params.get("activity_id", context.entity_id)))
    res = await db.execute(select(Activity).where(Activity.id == act_id, Activity.organization_id == organization_id))
    act = res.scalar_one_or_none()
    if not act:
        raise NotFoundException(f"Activity with ID {act_id} was not found for update.")

    if "status" in params:
        act.status = params["status"]
        if params["status"] == "completed":
            act.completed_at = datetime.now(timezone.utc)
    if "priority" in params:
        act.priority = params["priority"]

    await db.flush()
    return {"updated_activity_id": str(act.id), "status": act.status, "priority": act.priority}


async def _execute_assign_deal(
    db: AsyncSession,
    organization_id: uuid.UUID,
    params: Dict[str, Any],
    context: EventContext
) -> Dict[str, Any]:
    deal_id = uuid.UUID(str(params.get("deal_id", context.entity_id)))
    res = await db.execute(select(Deal).where(Deal.id == deal_id, Deal.organization_id == organization_id))
    deal = res.scalar_one_or_none()
    if not deal:
        raise NotFoundException(f"Deal with ID {deal_id} was not found.")

    new_notes = f"[Workflow Reassigned]: {params.get('note', 'Reassigned by workflow rule')}"
    deal.notes = f"{deal.notes}\n{new_notes}" if deal.notes else new_notes
    await db.flush()

    return {"deal_id": str(deal.id), "assigned": True, "note": new_notes}


async def _execute_assign_customer(
    db: AsyncSession,
    organization_id: uuid.UUID,
    params: Dict[str, Any],
    context: EventContext
) -> Dict[str, Any]:
    customer_id = uuid.UUID(str(params.get("customer_id", context.entity_id)))
    res = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.organization_id == organization_id))
    customer = res.scalar_one_or_none()
    if not customer:
        raise NotFoundException(f"Customer with ID {customer_id} was not found.")

    return {"customer_id": str(customer.id), "assigned": True}


async def _execute_add_note(
    db: AsyncSession,
    organization_id: uuid.UUID,
    params: Dict[str, Any],
    context: EventContext
) -> Dict[str, Any]:
    note_text = params.get("note", "Workflow execution note created.")
    creator_user_id = await _get_fallback_user_id(db, organization_id, context.actor_user_id)

    # Create note activity for audit
    activity = Activity(
        organization_id=organization_id,
        activity_type="note",
        title="Workflow Execution Note",
        description=note_text,
        status="completed",
        priority="medium",
        deal_id=context.entity_id if context.entity_type == "deal" else None,
        customer_id=context.entity_id if context.entity_type == "customer" else None,
        quotation_id=context.entity_id if context.entity_type == "quotation" else None,
        created_by_user_id=creator_user_id,
        completed_at=datetime.now(timezone.utc)
    )
    db.add(activity)
    await db.flush()

    return {"note_activity_id": str(activity.id), "note": note_text}


async def _execute_send_notification(
    db: AsyncSession,
    organization_id: uuid.UUID,
    params: Dict[str, Any],
    context: EventContext
) -> Dict[str, Any]:
    title = params.get("title", f"Workflow Alert: {context.event_type}")
    message = params.get("message", f"Event {context.event_type} occurred on {context.entity_type} {context.entity_id}")
    severity = params.get("severity", "info")
    creator_user_id = await _get_fallback_user_id(db, organization_id, context.actor_user_id)

    # In-app notification creation via system activity note / alert feed
    activity = Activity(
        organization_id=organization_id,
        activity_type="task",
        title=f"🔔 {title}",
        description=f"[{severity.upper()}] {message}",
        status="pending",
        priority="high" if severity in ("warning", "critical") else "medium",
        deal_id=context.entity_id if context.entity_type == "deal" else None,
        customer_id=context.entity_id if context.entity_type == "customer" else None,
        quotation_id=context.entity_id if context.entity_type == "quotation" else None,
        created_by_user_id=creator_user_id
    )
    db.add(activity)
    await db.flush()

    return {"notification_sent": True, "title": title, "severity": severity}


async def _execute_update_deal_field(
    db: AsyncSession,
    organization_id: uuid.UUID,
    params: Dict[str, Any],
    context: EventContext
) -> Dict[str, Any]:
    deal_id = uuid.UUID(str(params.get("deal_id", context.entity_id)))
    res = await db.execute(select(Deal).where(Deal.id == deal_id, Deal.organization_id == organization_id))
    deal = res.scalar_one_or_none()
    if not deal:
        raise NotFoundException(f"Deal with ID {deal_id} was not found.")

    # Guard commercial field rules (pricing/margins/won/lost reasons must use dedicated state machine)
    updated_fields = []
    if "stage" in params and deal.status == "open":
        deal.stage = params["stage"]
        updated_fields.append("stage")
    if "probability" in params and deal.status == "open":
        deal.probability = int(params["probability"])
        updated_fields.append("probability")
    if "description" in params:
        deal.description = params["description"]
        updated_fields.append("description")

    await db.flush()
    return {"deal_id": str(deal.id), "updated_fields": updated_fields}


async def _execute_update_customer_field(
    db: AsyncSession,
    organization_id: uuid.UUID,
    params: Dict[str, Any],
    context: EventContext
) -> Dict[str, Any]:
    customer_id = uuid.UUID(str(params.get("customer_id", context.entity_id)))
    res = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.organization_id == organization_id))
    customer = res.scalar_one_or_none()
    if not customer:
        raise NotFoundException(f"Customer with ID {customer_id} was not found.")

    updated_fields = []
    if "city" in params:
        customer.city = params["city"]
        updated_fields.append("city")
    if "state" in params:
        customer.state = params["state"]
        updated_fields.append("state")

    await db.flush()
    return {"customer_id": str(customer.id), "updated_fields": updated_fields}

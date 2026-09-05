import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import logging

from app.models.activity import Activity
from app.models.customer import Customer
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.quotation import Quotation
from app.models.user import User
from app.schemas.activity import ActivityCreate, ActivityUpdate
from app.core.exceptions import NotFoundException, ConflictException, BusinessRuleViolationException

logger = logging.getLogger("dealflow360.activities_service")


async def verify_activity_relationships(
    db: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: Optional[uuid.UUID] = None,
    contact_id: Optional[uuid.UUID] = None,
    deal_id: Optional[uuid.UUID] = None,
    quotation_id: Optional[uuid.UUID] = None,
    assigned_to_user_id: Optional[uuid.UUID] = None
) -> None:
    """Verifies that all referenced entities exist within the tenant and match the customer if supplied."""

    # 1. Customer validation
    target_customer_id = customer_id
    if customer_id:
        c_stmt = select(Customer).where(Customer.id == customer_id, Customer.organization_id == organization_id)
        cust_res = await db.execute(c_stmt)
        if not cust_res.scalar_one_or_none():
            raise NotFoundException("Target customer requested was not found")

    # 2. Contact validation
    if contact_id:
        ct_stmt = select(Contact).where(Contact.id == contact_id, Contact.organization_id == organization_id)
        ct_res = await db.execute(ct_stmt)
        contact = ct_res.scalar_one_or_none()
        if not contact:
            raise NotFoundException("Target contact requested was not found")
        if target_customer_id and contact.customer_id != target_customer_id:
            raise NotFoundException("Target contact does not belong to the specified customer")

    # 3. Deal validation
    if deal_id:
        d_stmt = select(Deal).where(Deal.id == deal_id, Deal.organization_id == organization_id)
        d_res = await db.execute(d_stmt)
        deal = d_res.scalar_one_or_none()
        if not deal:
            raise NotFoundException("Target deal requested was not found")
        if target_customer_id and deal.customer_id != target_customer_id:
            raise NotFoundException("Target deal does not belong to the specified customer")

    # 4. Quotation validation
    if quotation_id:
        q_stmt = select(Quotation).where(Quotation.id == quotation_id, Quotation.organization_id == organization_id)
        q_res = await db.execute(q_stmt)
        quotation = q_res.scalar_one_or_none()
        if not quotation:
            raise NotFoundException("Target quotation requested was not found")
        if target_customer_id and quotation.customer_id != target_customer_id:
            raise NotFoundException("Target quotation does not belong to the specified customer")

    # 5. Assigned User validation
    if assigned_to_user_id:
        u_stmt = select(User).where(User.id == assigned_to_user_id, User.organization_id == organization_id)
        u_res = await db.execute(u_stmt)
        user = u_res.scalar_one_or_none()
        if not user or not user.is_active:
            raise NotFoundException("Target assigned user was not found or is inactive")


async def create_activity(
    db: AsyncSession,
    organization_id: uuid.UUID,
    current_user_id: uuid.UUID,
    payload: ActivityCreate
) -> Activity:
    """Creates a new Activity record within tenant scope."""
    await verify_activity_relationships(
        db,
        organization_id,
        payload.customer_id,
        payload.contact_id,
        payload.deal_id,
        payload.quotation_id,
        payload.assigned_to_user_id
    )

    activity = Activity(
        organization_id=organization_id,
        activity_type=payload.activity_type.strip().lower(),
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        status="pending",
        priority=payload.priority.strip().lower() if payload.priority else "medium",
        customer_id=payload.customer_id,
        contact_id=payload.contact_id,
        deal_id=payload.deal_id,
        quotation_id=payload.quotation_id,
        assigned_to_user_id=payload.assigned_to_user_id,
        created_by_user_id=current_user_id,
        due_at=payload.due_at,
        completed_at=None
    )

    try:
        db.add(activity)
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise BusinessRuleViolationException("Activity creation failed due to a database constraint violation.")

    return await get_activity_by_id(db, organization_id, activity.id)


async def list_activities(
    db: AsyncSession,
    organization_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    customer_id: Optional[uuid.UUID] = None,
    contact_id: Optional[uuid.UUID] = None,
    deal_id: Optional[uuid.UUID] = None,
    quotation_id: Optional[uuid.UUID] = None,
    activity_type: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to_user_id: Optional[uuid.UUID] = None,
    overdue: Optional[bool] = None,
    upcoming: Optional[bool] = None,
    search: Optional[str] = None
) -> List[Activity]:
    """Retrieves activities strictly scoped to organization with optional filtering."""
    stmt = select(Activity).where(Activity.organization_id == organization_id)

    if customer_id:
        stmt = stmt.where(Activity.customer_id == customer_id)
    if contact_id:
        stmt = stmt.where(Activity.contact_id == contact_id)
    if deal_id:
        stmt = stmt.where(Activity.deal_id == deal_id)
    if quotation_id:
        stmt = stmt.where(Activity.quotation_id == quotation_id)
    if activity_type:
        stmt = stmt.where(Activity.activity_type == activity_type.strip().lower())
    if status:
        stmt = stmt.where(Activity.status == status.strip().lower())
    if priority:
        stmt = stmt.where(Activity.priority == priority.strip().lower())
    if assigned_to_user_id:
        stmt = stmt.where(Activity.assigned_to_user_id == assigned_to_user_id)

    now_utc = datetime.now(timezone.utc)
    if overdue is True:
        stmt = stmt.where(
            Activity.status == "pending",
            Activity.due_at.isnot(None),
            Activity.due_at < now_utc
        )
    elif upcoming is True:
        stmt = stmt.where(
            Activity.status == "pending",
            Activity.due_at.isnot(None),
            Activity.due_at >= now_utc
        )

    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(or_(Activity.title.ilike(pattern), Activity.description.ilike(pattern)))

    stmt = stmt.order_by(Activity.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_customer_activities(
    db: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Activity]:
    """Retrieves customer activity timeline (newest first)."""
    # Verify customer exists in tenant
    c_stmt = select(Customer).where(Customer.id == customer_id, Customer.organization_id == organization_id)
    cust_res = await db.execute(c_stmt)
    if not cust_res.scalar_one_or_none():
        raise NotFoundException("Target customer requested was not found")

    stmt = (
        select(Activity)
        .where(
            Activity.organization_id == organization_id,
            Activity.customer_id == customer_id
        )
        .order_by(Activity.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_deal_activities(
    db: AsyncSession,
    organization_id: uuid.UUID,
    deal_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Activity]:
    """Retrieves deal activity timeline (newest first)."""
    # Verify deal exists in tenant
    d_stmt = select(Deal).where(Deal.id == deal_id, Deal.organization_id == organization_id)
    deal_res = await db.execute(d_stmt)
    if not deal_res.scalar_one_or_none():
        raise NotFoundException("Target deal requested was not found")

    stmt = (
        select(Activity)
        .where(
            Activity.organization_id == organization_id,
            Activity.deal_id == deal_id
        )
        .order_by(Activity.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_activity_by_id(
    db: AsyncSession,
    organization_id: uuid.UUID,
    activity_id: uuid.UUID
) -> Activity:
    """Fetches activity by ID within tenant scope."""
    stmt = select(Activity).where(
        Activity.id == activity_id,
        Activity.organization_id == organization_id
    )
    result = await db.execute(stmt)
    activity = result.scalar_one_or_none()
    if not activity:
        raise NotFoundException("Activity requested was not found")
    return activity


async def update_activity(
    db: AsyncSession,
    organization_id: uuid.UUID,
    activity_id: uuid.UUID,
    payload: ActivityUpdate
) -> Activity:
    """Updates an existing activity record within tenant scope."""
    activity = await get_activity_by_id(db, organization_id, activity_id)

    if activity.status in {"completed", "cancelled"}:
        raise BusinessRuleViolationException(f"Finalized activity with status '{activity.status}' cannot be modified.")

    update_data = payload.model_dump(exclude_unset=True)

    # Re-verify relationships if updated
    target_cust = update_data.get("customer_id", activity.customer_id)
    target_contact = update_data.get("contact_id", activity.contact_id)
    target_deal = update_data.get("deal_id", activity.deal_id)
    target_quotation = update_data.get("quotation_id", activity.quotation_id)
    target_assigned = update_data.get("assigned_to_user_id", activity.assigned_to_user_id)

    await verify_activity_relationships(
        db,
        organization_id,
        target_cust,
        target_contact,
        target_deal,
        target_quotation,
        target_assigned
    )

    if "activity_type" in update_data and update_data["activity_type"] is not None:
        activity.activity_type = update_data["activity_type"].strip().lower()
    if "title" in update_data and update_data["title"] is not None:
        activity.title = update_data["title"].strip()
    if "description" in update_data:
        activity.description = update_data["description"].strip() if update_data["description"] else None
    if "priority" in update_data and update_data["priority"] is not None:
        activity.priority = update_data["priority"].strip().lower()

    activity.customer_id = target_cust
    activity.contact_id = target_contact
    activity.deal_id = target_deal
    activity.quotation_id = target_quotation
    activity.assigned_to_user_id = target_assigned

    if "due_at" in update_data:
        activity.due_at = update_data["due_at"]

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise BusinessRuleViolationException("Activity update failed due to a database constraint violation.")

    return await get_activity_by_id(db, organization_id, activity.id)


async def complete_activity(
    db: AsyncSession,
    organization_id: uuid.UUID,
    activity_id: uuid.UUID
) -> Activity:
    """Marks a pending activity as completed and sets server-side completion timestamp."""
    activity = await get_activity_by_id(db, organization_id, activity_id)
    if activity.status != "pending":
        raise BusinessRuleViolationException(f"Activity with status '{activity.status}' cannot be completed.")

    activity.status = "completed"
    activity.completed_at = datetime.now(timezone.utc)
    await db.flush()
    return await get_activity_by_id(db, organization_id, activity.id)


async def cancel_activity(
    db: AsyncSession,
    organization_id: uuid.UUID,
    activity_id: uuid.UUID
) -> Activity:
    """Marks a pending activity as cancelled."""
    activity = await get_activity_by_id(db, organization_id, activity_id)
    if activity.status != "pending":
        raise BusinessRuleViolationException(f"Activity with status '{activity.status}' cannot be cancelled.")

    activity.status = "cancelled"
    await db.flush()
    return await get_activity_by_id(db, organization_id, activity.id)


async def delete_activity(
    db: AsyncSession,
    organization_id: uuid.UUID,
    activity_id: uuid.UUID
) -> None:
    """Deletes an activity within tenant scope."""
    activity = await get_activity_by_id(db, organization_id, activity_id)
    await db.delete(activity)
    await db.flush()

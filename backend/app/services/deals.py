import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timezone
from typing import List, Optional, Dict
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import logging

from app.models.deal import Deal
from app.models.customer import Customer
from app.models.contact import Contact
from app.models.quotation import Quotation
from app.schemas.deal import DealCreate, DealUpdate
from app.core.exceptions import NotFoundException, ConflictException, BusinessRuleViolationException

logger = logging.getLogger("dealflow360.deals_service")

TWO_DECIMALS = Decimal("0.01")
STAGE_PROBABILITIES = {
    "new": 10,
    "qualified": 25,
    "proposal": 50,
    "negotiation": 75,
    "won": 100,
    "lost": 0
}


def round_decimal(val: Decimal) -> Decimal:
    """Rounds monetary decimal values consistently to two decimal places."""
    return val.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


async def generate_deal_number(db: AsyncSession, organization_id: uuid.UUID) -> str:
    """Generates the next sequential deal number for the organization (e.g. DEAL-000001)."""
    stmt = (
        select(Deal.deal_number)
        .where(
            Deal.organization_id == organization_id,
            Deal.deal_number.like("DEAL-%")
        )
        .order_by(Deal.created_at.desc())
    )
    result = await db.execute(stmt)
    numbers = result.scalars().all()

    max_num = 0
    for num_str in numbers:
        try:
            num_part = int(num_str.replace("DEAL-", ""))
            if num_part > max_num:
                max_num = num_part
        except ValueError:
            continue

    next_num = max_num + 1
    return f"DEAL-{next_num:06d}"


def validate_stage_transition(current_stage: str, new_stage: str) -> None:
    """Validates allowed pipeline stage transitions for Deals."""
    if current_stage == new_stage:
        return

    finalized_stages = {"won", "lost"}
    if current_stage in finalized_stages:
        raise BusinessRuleViolationException(
            f"Finalized deal in stage '{current_stage}' cannot be transitioned to '{new_stage}'."
        )

    allowed_transitions = {
        "new": {"qualified", "proposal", "negotiation", "won", "lost"},
        "qualified": {"proposal", "negotiation", "won", "lost"},
        "proposal": {"negotiation", "won", "lost"},
        "negotiation": {"won", "lost"},
    }

    valid_targets = allowed_transitions.get(current_stage, set())
    if new_stage not in valid_targets:
        raise BusinessRuleViolationException(
            f"Invalid deal stage transition from '{current_stage}' to '{new_stage}'."
        )


async def verify_customer_in_tenant(db: AsyncSession, organization_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
    """Verifies target customer exists within the user's organization."""
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.organization_id == organization_id
    )
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundException("Target customer requested was not found")
    return customer


async def verify_contact_for_deal(
    db: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID,
    contact_id: Optional[uuid.UUID]
) -> Optional[Contact]:
    """Verifies target contact exists within tenant AND belongs to specified customer."""
    if not contact_id:
        return None
    stmt = select(Contact).where(
        Contact.id == contact_id,
        Contact.organization_id == organization_id
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if not contact or contact.customer_id != customer_id:
        raise NotFoundException("Target contact requested was not found or does not belong to the selected customer")
    return contact


async def verify_quotation_for_deal(
    db: AsyncSession,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID,
    quotation_id: Optional[uuid.UUID]
) -> Optional[Quotation]:
    """Verifies target quotation exists within tenant AND belongs to specified customer."""
    if not quotation_id:
        return None
    stmt = select(Quotation).where(
        Quotation.id == quotation_id,
        Quotation.organization_id == organization_id
    )
    result = await db.execute(stmt)
    quotation = result.scalar_one_or_none()
    if not quotation or quotation.customer_id != customer_id:
        raise NotFoundException("Target quotation requested was not found or does not belong to the selected customer")
    return quotation


async def create_deal(
    db: AsyncSession,
    organization_id: uuid.UUID,
    payload: DealCreate
) -> Deal:
    """Atomically creates a new Deal within organization scope."""
    # 1. Tenant & relationship validations
    await verify_customer_in_tenant(db, organization_id, payload.customer_id)
    await verify_contact_for_deal(db, organization_id, payload.customer_id, payload.contact_id)
    await verify_quotation_for_deal(db, organization_id, payload.customer_id, payload.quotation_id)

    stage = payload.stage.strip().lower() if payload.stage else "new"

    # 2. Status & Probability determination
    if stage == "won":
        status = "won"
        probability = 100
    elif stage == "lost":
        status = "lost"
        probability = 0
        if not payload.lost_reason or not payload.lost_reason.strip():
            raise BusinessRuleViolationException("A non-empty lost_reason is required when creating a deal in 'lost' stage.")
    else:
        status = "open"
        probability = payload.probability if payload.probability is not None else STAGE_PROBABILITIES.get(stage, 10)

    lost_reason = payload.lost_reason.strip() if payload.lost_reason and stage == "lost" else None

    # 3. Generate tenant-scoped deal number
    deal_number = await generate_deal_number(db, organization_id)

    deal = Deal(
        organization_id=organization_id,
        customer_id=payload.customer_id,
        contact_id=payload.contact_id,
        quotation_id=payload.quotation_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        deal_number=deal_number,
        stage=stage,
        status=status,
        value=round_decimal(payload.value),
        probability=probability,
        expected_close_date=payload.expected_close_date,
        lost_reason=lost_reason,
        notes=payload.notes.strip() if payload.notes else None
    )

    try:
        db.add(deal)
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        error_msg = str(exc)
        logger.warning(f"Deal creation failed: {error_msg}")
        if "uq_deals_organization_id_deal_number" in error_msg:
            raise ConflictException("Deal number collision occurred; please retry.")
        raise BusinessRuleViolationException("Deal creation failed due to a database constraint violation.")

    return await get_deal_by_id(db, organization_id, deal.id)


async def list_deals(
    db: AsyncSession,
    organization_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    stage: Optional[str] = None,
    status: Optional[str] = None,
    customer_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    expected_close_date: Optional[date] = None
) -> List[Deal]:
    """Retrieves deals scoped strictly to the specified organization."""
    stmt = select(Deal).where(Deal.organization_id == organization_id)

    if stage:
        stmt = stmt.where(Deal.stage == stage.strip().lower())
    if status:
        stmt = stmt.where(Deal.status == status.strip().lower())
    if customer_id:
        stmt = stmt.where(Deal.customer_id == customer_id)
    if expected_close_date:
        stmt = stmt.where(Deal.expected_close_date == expected_close_date)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(or_(Deal.title.ilike(pattern), Deal.deal_number.ilike(pattern)))

    stmt = stmt.order_by(Deal.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_deals_pipeline(
    db: AsyncSession,
    organization_id: uuid.UUID
) -> Dict[str, List[Deal]]:
    """Retrieves all organization deals grouped by pipeline stage for Kanban views."""
    stages = ["new", "qualified", "proposal", "negotiation", "won", "lost"]
    pipeline: Dict[str, List[Deal]] = {st: [] for st in stages}

    stmt = (
        select(Deal)
        .where(Deal.organization_id == organization_id)
        .order_by(Deal.created_at.desc())
    )
    result = await db.execute(stmt)
    deals = result.scalars().all()

    for deal in deals:
        if deal.stage in pipeline:
            pipeline[deal.stage].append(deal)
        else:
            pipeline.setdefault(deal.stage, []).append(deal)

    return pipeline


async def get_deal_by_id(
    db: AsyncSession,
    organization_id: uuid.UUID,
    deal_id: uuid.UUID
) -> Deal:
    """Fetches a deal by ID within tenant scope (raises 404 if missing or cross-tenant)."""
    stmt = select(Deal).where(
        Deal.id == deal_id,
        Deal.organization_id == organization_id
    )
    result = await db.execute(stmt)
    deal = result.scalar_one_or_none()
    if not deal:
        raise NotFoundException("Deal requested was not found")
    return deal


async def update_deal(
    db: AsyncSession,
    organization_id: uuid.UUID,
    deal_id: uuid.UUID,
    payload: DealUpdate
) -> Deal:
    """Updates an existing deal within tenant scope."""
    deal = await get_deal_by_id(db, organization_id, deal_id)
    finalized_stages = {"won", "lost"}

    update_data = payload.model_dump(exclude_unset=True)

    # 1. Finalized deal immutability check
    if deal.stage in finalized_stages:
        # Check if client tries to alter any field
        if update_data:
            # If trying to set stage/status to same value, allow, else block
            new_stage = update_data.get("stage")
            if new_stage and new_stage.strip().lower() != deal.stage:
                raise BusinessRuleViolationException(f"Finalized deal in stage '{deal.stage}' cannot be transitioned to '{new_stage}'.")
            
            non_stage_changes = set(update_data.keys()) - {"stage", "status"}
            if non_stage_changes:
                raise BusinessRuleViolationException(
                    f"Finalized deal with stage '{deal.stage}' cannot be modified."
                )

    # 2. Customer, Contact, Quotation relationship re-validation
    target_customer_id = update_data.get("customer_id", deal.customer_id)
    if "customer_id" in update_data and update_data["customer_id"] is not None:
        await verify_customer_in_tenant(db, organization_id, target_customer_id)
        deal.customer_id = target_customer_id

    if "contact_id" in update_data:
        new_contact_id = update_data["contact_id"]
        if new_contact_id is not None:
            await verify_contact_for_deal(db, organization_id, target_customer_id, new_contact_id)
        deal.contact_id = new_contact_id
    elif "customer_id" in update_data and deal.contact_id is not None:
        # If customer changed, re-verify existing contact
        await verify_contact_for_deal(db, organization_id, target_customer_id, deal.contact_id)

    if "quotation_id" in update_data:
        new_quot_id = update_data["quotation_id"]
        if new_quot_id is not None:
            await verify_quotation_for_deal(db, organization_id, target_customer_id, new_quot_id)
        deal.quotation_id = new_quot_id
    elif "customer_id" in update_data and deal.quotation_id is not None:
        # If customer changed, re-verify existing quotation
        await verify_quotation_for_deal(db, organization_id, target_customer_id, deal.quotation_id)

    # 3. Stage & Status updates
    if "stage" in update_data and update_data["stage"] is not None:
        new_stage = update_data["stage"].strip().lower()
        validate_stage_transition(deal.stage, new_stage)
        deal.stage = new_stage

        if new_stage == "won":
            deal.status = "won"
            deal.probability = 100
        elif new_stage == "lost":
            deal.status = "lost"
            deal.probability = 0
            reason = update_data.get("lost_reason", deal.lost_reason)
            if not reason or not reason.strip():
                raise BusinessRuleViolationException("A non-empty lost_reason is required when transitioning to 'lost' stage.")
            deal.lost_reason = reason.strip()
        else:
            deal.status = "open"
            if "probability" not in update_data or update_data["probability"] is None:
                deal.probability = STAGE_PROBABILITIES.get(new_stage, 10)

    if "status" in update_data and update_data["status"] is not None and "stage" not in update_data:
        new_status = update_data["status"].strip().lower()
        if new_status == "won" and deal.stage != "won":
            validate_stage_transition(deal.stage, "won")
            deal.stage = "won"
            deal.status = "won"
            deal.probability = 100
        elif new_status == "lost" and deal.stage != "lost":
            validate_stage_transition(deal.stage, "lost")
            reason = update_data.get("lost_reason", deal.lost_reason)
            if not reason or not reason.strip():
                raise BusinessRuleViolationException("A non-empty lost_reason is required when setting status to 'lost'.")
            deal.stage = "lost"
            deal.status = "lost"
            deal.probability = 0
            deal.lost_reason = reason.strip()

    # 4. Standard Field Updates
    if "title" in update_data and update_data["title"] is not None:
        deal.title = update_data["title"].strip()
    if "description" in update_data:
        deal.description = update_data["description"].strip() if update_data["description"] else None
    if "value" in update_data and update_data["value"] is not None:
        deal.value = round_decimal(update_data["value"])
    if "probability" in update_data and update_data["probability"] is not None and deal.stage not in finalized_stages:
        deal.probability = update_data["probability"]
    if "expected_close_date" in update_data:
        deal.expected_close_date = update_data["expected_close_date"]
    if "lost_reason" in update_data and deal.stage == "lost":
        deal.lost_reason = update_data["lost_reason"].strip() if update_data["lost_reason"] else None
    if "notes" in update_data:
        deal.notes = update_data["notes"].strip() if update_data["notes"] else None

    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise BusinessRuleViolationException("Deal update failed due to a database constraint violation.")

    return await get_deal_by_id(db, organization_id, deal.id)


async def delete_deal(
    db: AsyncSession,
    organization_id: uuid.UUID,
    deal_id: uuid.UUID
) -> None:
    """Deletes a deal within tenant scope."""
    deal = await get_deal_by_id(db, organization_id, deal_id)
    await db.delete(deal)
    await db.flush()

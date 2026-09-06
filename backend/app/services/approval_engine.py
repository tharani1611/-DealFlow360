import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import logging

from app.models.approval_rule import ApprovalRule
from app.models.quotation_approval import QuotationApproval
from app.models.approval_audit_log import ApprovalAuditLog
from app.models.quotation import Quotation
from app.models.user import User
from app.schemas.approval_engine import (
    ApprovalRuleCreate, ApprovalRuleUpdate, QuotationApprovalResponse
)
from app.schemas.discount_governance import GovernanceEvaluationResult
from app.schemas.discount_risk import RiskEvaluationResult
from app.schemas.margin import QuotationMarginResponse
from app.services import quotations as quotation_service
from app.core.exceptions import NotFoundException, BusinessRuleViolationException, ForbiddenException

logger = logging.getLogger("dealflow360.approval_engine_service")

TWO_DECIMALS = Decimal("0.01")


def round_decimal(val: Decimal) -> Decimal:
    """Rounds monetary decimal values consistently to two decimal places."""
    return val.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


async def create_approval_audit_log(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    event_type: str,
    new_status: str,
    actor_user_id: Optional[uuid.UUID] = None,
    actor_name: Optional[str] = None,
    previous_status: Optional[str] = None,
    reason: Optional[str] = None,
    notes: Optional[str] = None,
    approval_rule_id: Optional[uuid.UUID] = None,
    approval_level: int = 1,
    approval_id: Optional[uuid.UUID] = None,
) -> ApprovalAuditLog:
    """Appends an immutable audit log record for an approval event."""
    log_entry = ApprovalAuditLog(
        organization_id=organization_id,
        quotation_id=quotation_id,
        approval_id=approval_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_name=actor_name,
        previous_status=previous_status,
        new_status=new_status,
        reason=reason,
        notes=notes,
        approval_rule_id=approval_rule_id,
        approval_level=approval_level,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log_entry)
    await db.flush()
    return log_entry


async def get_approval_audit_logs(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID
) -> List[ApprovalAuditLog]:
    """Lists append-only approval audit logs for a quotation."""
    stmt = (
        select(ApprovalAuditLog)
        .where(
            ApprovalAuditLog.organization_id == organization_id,
            ApprovalAuditLog.quotation_id == quotation_id
        )
        .order_by(ApprovalAuditLog.created_at.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_approval_rule(
    db: AsyncSession,
    organization_id: uuid.UUID,
    payload: ApprovalRuleCreate
) -> ApprovalRule:
    """Creates a new approval rule."""
    rule = ApprovalRule(
        organization_id=organization_id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        is_active=payload.is_active,
        priority=payload.priority,
        min_discount_percent=round_decimal(payload.min_discount_percent) if payload.min_discount_percent is not None else None,
        max_discount_percent=round_decimal(payload.max_discount_percent) if payload.max_discount_percent is not None else None,
        min_margin_percent=round_decimal(payload.min_margin_percent) if payload.min_margin_percent is not None else None,
        risk_level=payload.risk_level.strip().upper() if payload.risk_level else None,
        quotation_value_threshold=round_decimal(payload.quotation_value_threshold) if payload.quotation_value_threshold is not None else None,
        approval_level=payload.approval_level,
        required_role=payload.required_role.strip().lower()
    )

    try:
        db.add(rule)
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise BusinessRuleViolationException("Approval rule creation failed due to database constraint violation.")

    return await get_approval_rule_by_id(db, organization_id, rule.id)


async def list_approval_rules(
    db: AsyncSession,
    organization_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[ApprovalRule]:
    """Lists approval rules scoped strictly to the organization."""
    stmt = select(ApprovalRule).where(ApprovalRule.organization_id == organization_id)
    if is_active is not None:
        stmt = stmt.where(ApprovalRule.is_active == is_active)

    stmt = stmt.order_by(ApprovalRule.priority.asc(), ApprovalRule.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_approval_rule_by_id(
    db: AsyncSession,
    organization_id: uuid.UUID,
    rule_id: uuid.UUID
) -> ApprovalRule:
    """Gets an approval rule by ID within tenant scope."""
    stmt = select(ApprovalRule).where(
        ApprovalRule.id == rule_id,
        ApprovalRule.organization_id == organization_id
    )
    result = await db.execute(stmt)
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundException("Approval rule requested was not found")
    return rule


async def update_approval_rule(
    db: AsyncSession,
    organization_id: uuid.UUID,
    rule_id: uuid.UUID,
    payload: ApprovalRuleUpdate
) -> ApprovalRule:
    """Updates an approval rule."""
    rule = await get_approval_rule_by_id(db, organization_id, rule_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data and data["name"] is not None:
        rule.name = data["name"].strip()
    if "description" in data:
        rule.description = data["description"].strip() if data["description"] else None
    if "is_active" in data and data["is_active"] is not None:
        rule.is_active = data["is_active"]
    if "priority" in data and data["priority"] is not None:
        rule.priority = data["priority"]
    if "min_discount_percent" in data:
        rule.min_discount_percent = round_decimal(data["min_discount_percent"]) if data["min_discount_percent"] is not None else None
    if "max_discount_percent" in data:
        rule.max_discount_percent = round_decimal(data["max_discount_percent"]) if data["max_discount_percent"] is not None else None
    if "min_margin_percent" in data:
        rule.min_margin_percent = round_decimal(data["min_margin_percent"]) if data["min_margin_percent"] is not None else None
    if "risk_level" in data:
        rule.risk_level = data["risk_level"].strip().upper() if data["risk_level"] else None
    if "quotation_value_threshold" in data:
        rule.quotation_value_threshold = round_decimal(data["quotation_value_threshold"]) if data["quotation_value_threshold"] is not None else None
    if "approval_level" in data and data["approval_level"] is not None:
        rule.approval_level = data["approval_level"]
    if "required_role" in data and data["required_role"] is not None:
        rule.required_role = data["required_role"].strip().lower()

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise BusinessRuleViolationException("Approval rule update failed due to database constraint violation.")

    return await get_approval_rule_by_id(db, organization_id, rule.id)


async def delete_approval_rule(
    db: AsyncSession,
    organization_id: uuid.UUID,
    rule_id: uuid.UUID
) -> None:
    """Deletes an approval rule."""
    rule = await get_approval_rule_by_id(db, organization_id, rule_id)
    await db.delete(rule)
    await db.flush()


async def get_latest_quotation_approval(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID
) -> Optional[QuotationApproval]:
    """Retrieves the latest quotation approval record."""
    stmt = (
        select(QuotationApproval)
        .options(
            selectinload(QuotationApproval.requested_by_user),
            selectinload(QuotationApproval.approved_by_user)
        )
        .where(
            QuotationApproval.organization_id == organization_id,
            QuotationApproval.quotation_id == quotation_id
        )
        .order_by(QuotationApproval.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def evaluate_approval_requirement(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    requested_by_user_id: uuid.UUID,
    governance_res: GovernanceEvaluationResult,
    risk_res: RiskEvaluationResult,
    margin_res: QuotationMarginResponse
) -> QuotationApproval:
    """
    Evaluates whether a quotation requires authorization based on active approval rules.
    If required, creates or maintains a PENDING QuotationApproval record and logs audit events.
    """
    quotation = await quotation_service.get_quotation_by_id(db, organization_id, quotation_id)

    # Check if an existing APPROVED record exists and is valid
    existing = await get_latest_quotation_approval(db, organization_id, quotation_id)
    if existing and existing.status == "APPROVED":
        return existing

    # Fetch active approval rules
    rules = await list_approval_rules(db, organization_id, is_active=True)

    triggered_rule: Optional[ApprovalRule] = None
    trigger_reasons: List[str] = []

    blended_disc = risk_res.blended_discount_percent
    overall_margin = margin_res.margin_percent
    total_val = quotation.total_amount

    # 1. Automatic trigger if governance has policy violations
    if not governance_res.compliant:
        trigger_reasons.append(f"Quotation has {len(governance_res.violations)} commercial discount governance policy violations.")

    # 2. Automatic trigger if risk level is HIGH or CRITICAL
    if risk_res.risk_level in ("HIGH", "CRITICAL"):
        trigger_reasons.append(f"Commercial risk engine classified quotation as {risk_res.risk_level} risk.")

    # 3. Check custom approval rules
    for rule in rules:
        matched = False
        rule_reasons = []

        if rule.min_discount_percent is not None and blended_disc >= rule.min_discount_percent:
            matched = True
            rule_reasons.append(f"Blended discount ({blended_disc}%) exceeds rule threshold ({rule.min_discount_percent}%).")

        if rule.min_margin_percent is not None and overall_margin < rule.min_margin_percent:
            matched = True
            rule_reasons.append(f"Gross margin ({overall_margin}%) is below rule threshold ({rule.min_margin_percent}%).")

        if rule.risk_level and risk_res.risk_level == rule.risk_level:
            matched = True
            rule_reasons.append(f"Risk level matched rule condition ({rule.risk_level}).")

        if rule.quotation_value_threshold is not None and total_val >= rule.quotation_value_threshold:
            matched = True
            rule_reasons.append(f"Total quotation value (${total_val}) exceeds threshold (${rule.quotation_value_threshold}).")

        if matched:
            triggered_rule = rule
            trigger_reasons.extend(rule_reasons)
            break

    reasons_text = "; ".join(trigger_reasons) if trigger_reasons else None
    status = "PENDING" if trigger_reasons else "NOT_REQUIRED"
    prev_status = existing.status if existing else None

    # Reuse existing pending record or create new
    if existing and existing.status in ("PENDING", "INVALIDATED", "NOT_REQUIRED"):
        existing.status = status
        existing.approval_rule_id = triggered_rule.id if triggered_rule else None
        existing.reasons = reasons_text
        await db.flush()
        approval_obj = existing
    else:
        new_approval = QuotationApproval(
            organization_id=organization_id,
            quotation_id=quotation_id,
            approval_rule_id=triggered_rule.id if triggered_rule else None,
            requested_by_user_id=requested_by_user_id,
            status=status,
            approval_level=triggered_rule.approval_level if triggered_rule else 1,
            reasons=reasons_text
        )
        db.add(new_approval)
        await db.flush()
        approval_obj = await get_latest_quotation_approval(db, organization_id, quotation_id)

    # Log audit event
    await create_approval_audit_log(
        db=db,
        organization_id=organization_id,
        quotation_id=quotation_id,
        approval_id=approval_obj.id if approval_obj else None,
        event_type="APPROVAL_SUBMITTED" if status == "PENDING" else "APPROVAL_EVALUATED",
        actor_user_id=requested_by_user_id,
        previous_status=prev_status,
        new_status=status,
        reason=reasons_text,
        approval_rule_id=triggered_rule.id if triggered_rule else None,
        approval_level=triggered_rule.approval_level if triggered_rule else 1
    )

    return approval_obj


async def record_approval_decision(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    current_user: User,
    decision: str,
    note: Optional[str] = None
) -> QuotationApproval:
    """Executes an approval or rejection decision on a pending quotation approval."""
    approval = await get_latest_quotation_approval(db, organization_id, quotation_id)
    if not approval or approval.status != "PENDING":
        raise BusinessRuleViolationException("No pending approval request found for this quotation")

    # Segregation of duties rule: non-admin submitter cannot self-approve their own request
    if approval.requested_by_user_id == current_user.id and not current_user.is_admin:
        raise ForbiddenException("Segregation of duties violation: The submitter cannot approve their own quotation request.")

    # Permission check: current user must be admin or have approver role
    if not current_user.is_admin:
        raise ForbiddenException("Only administrators / authorized commercial approvers can approve quotations")

    clean_decision = decision.strip().upper()
    if clean_decision not in ("APPROVED", "REJECTED"):
        raise BusinessRuleViolationException("Decision must be either 'APPROVED' or 'REJECTED'")

    prev_status = approval.status
    approval.status = clean_decision
    approval.approved_by_user_id = current_user.id
    approval.decision_note = note.strip() if note else None

    await db.flush()

    # Log audit event
    await create_approval_audit_log(
        db=db,
        organization_id=organization_id,
        quotation_id=quotation_id,
        approval_id=approval.id,
        event_type=f"APPROVAL_{clean_decision}",
        actor_user_id=current_user.id,
        actor_name=current_user.full_name,
        previous_status=prev_status,
        new_status=clean_decision,
        reason=approval.reasons,
        notes=approval.decision_note,
        approval_rule_id=approval.approval_rule_id,
        approval_level=approval.approval_level
    )

    return await get_latest_quotation_approval(db, organization_id, quotation_id)


async def invalidate_quotation_approval(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    actor_user_id: Optional[uuid.UUID] = None,
    actor_name: Optional[str] = None,
    reason: str = "Invalidated due to subsequent commercial modification of quotation details."
) -> None:
    """Invalidates existing quotation approval if commercial edits occur."""
    approval = await get_latest_quotation_approval(db, organization_id, quotation_id)
    if approval and approval.status in ("APPROVED", "PENDING"):
        prev_status = approval.status
        approval.status = "INVALIDATED"
        approval.decision_note = reason
        await db.flush()

        # Log audit event
        await create_approval_audit_log(
            db=db,
            organization_id=organization_id,
            quotation_id=quotation_id,
            approval_id=approval.id,
            event_type="APPROVAL_INVALIDATED",
            actor_user_id=actor_user_id,
            actor_name=actor_name,
            previous_status=prev_status,
            new_status="INVALIDATED",
            reason=reason,
            approval_rule_id=approval.approval_rule_id,
            approval_level=approval.approval_level
        )
        logger.info(f"Quotation {quotation_id} approval invalidated due to commercial edit.")


async def list_all_quotation_approvals(
    db: AsyncSession,
    organization_id: uuid.UUID,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[QuotationApproval]:
    """Lists quotation approvals for the organization with optional status filtering."""
    stmt = (
        select(QuotationApproval)
        .options(
            selectinload(QuotationApproval.quotation),
            selectinload(QuotationApproval.requested_by_user),
            selectinload(QuotationApproval.approved_by_user),
            selectinload(QuotationApproval.approval_rule),
        )
        .where(QuotationApproval.organization_id == organization_id)
    )
    if status_filter:
        stmt = stmt.where(QuotationApproval.status == status_filter.upper())
    stmt = stmt.order_by(QuotationApproval.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


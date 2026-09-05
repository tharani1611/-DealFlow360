import uuid
from datetime import datetime, timezone
from typing import List, Optional, Set, Dict
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.quotation import Quotation
from app.models.quotation_state import QuotationStateHistory
from app.schemas.quotation_state import QuotationStateHistoryResponse
from app.core.exceptions import NotFoundException, BusinessRuleViolationException

logger = logging.getLogger("dealflow360.quotation_state_service")

# All valid quotation statuses
VALID_STATUSES: Set[str] = {
    "draft",
    "priced",
    "sent",
    "accepted",
    "rejected",
    "expired",
    "cancelled",
    "converted",
}

# Statuses in which commercial fields and line items are locked from direct editing
IMMUTABLE_STATUSES: Set[str] = {
    "sent",
    "accepted",
    "rejected",
    "expired",
    "cancelled",
    "converted",
}

# Allowed transition lifecycle matrix
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "draft": {"priced", "sent", "cancelled"},
    "priced": {"draft", "sent", "cancelled"},
    "sent": {"accepted", "rejected", "expired", "cancelled"},
    "accepted": {"converted"},
    "rejected": set(),
    "expired": {"draft"},
    "cancelled": set(),
    "converted": set(),
}


def can_transition(current_status: str, target_status: str) -> bool:
    """Checks if a transition from current_status to target_status is permitted by the state matrix."""
    curr = current_status.strip().lower()
    targ = target_status.strip().lower()

    if curr == targ:
        return True

    allowed = ALLOWED_TRANSITIONS.get(curr, set())
    return targ in allowed


def is_status_immutable(status: str) -> bool:
    """Returns True if the quotation status locks commercial fields & line items."""
    return status.strip().lower() in IMMUTABLE_STATUSES


async def log_state_history(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    from_status: Optional[str],
    to_status: str,
    changed_by_user_id: Optional[uuid.UUID] = None,
    reason: Optional[str] = None
) -> QuotationStateHistory:
    """Logs a state transition event into quotation_state_history."""
    history_entry = QuotationStateHistory(
        organization_id=organization_id,
        quotation_id=quotation_id,
        from_status=from_status,
        to_status=to_status,
        changed_by_user_id=changed_by_user_id,
        reason=reason.strip() if reason else None
    )
    db.add(history_entry)
    await db.flush()
    return history_entry


async def check_lazy_expiration(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation: Quotation
) -> bool:
    """
    Lazy expiration check: if status is 'sent' and valid_until is past,
    auto-transitions to 'expired' and records audit log.
    """
    if quotation.status == "sent" and quotation.valid_until is not None:
        now = datetime.now(timezone.utc)
        valid_until_utc = quotation.valid_until
        if valid_until_utc.tzinfo is None:
            valid_until_utc = valid_until_utc.replace(tzinfo=timezone.utc)

        if valid_until_utc < now:
            old_status = quotation.status
            quotation.status = "expired"
            await log_state_history(
                db=db,
                organization_id=organization_id,
                quotation_id=quotation.id,
                from_status=old_status,
                to_status="expired",
                changed_by_user_id=None,
                reason="Auto-expired due to valid_until date limit"
            )
            await db.flush()
            logger.info(f"Quotation {quotation.quotation_number} auto-expired.")
            return True
    return False


async def transition_quotation(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID,
    target_status: str,
    reason: Optional[str] = None,
    current_user_id: Optional[uuid.UUID] = None
) -> Quotation:
    """Executes a validated state machine transition for a quotation."""
    from app.services.quotations import get_quotation_by_id

    quotation = await get_quotation_by_id(db, organization_id, quotation_id)
    target_clean = target_status.strip().lower()

    if target_clean not in VALID_STATUSES:
        raise BusinessRuleViolationException(
            f"Invalid target status '{target_status}'. Allowed statuses: {', '.join(sorted(VALID_STATUSES))}"
        )

    # Perform lazy expiration check before evaluating transition
    await check_lazy_expiration(db, organization_id, quotation)

    current_clean = quotation.status.strip().lower()

    if current_clean == target_clean:
        return quotation

    if not can_transition(current_clean, target_clean):
        raise BusinessRuleViolationException(
            f"Invalid quotation status transition from '{current_clean}' to '{target_clean}'."
        )

    # Check commercial approval requirement before sending
    if target_clean == "sent":
        from app.services.approval_engine import get_latest_quotation_approval
        appr = await get_latest_quotation_approval(db, organization_id, quotation.id)
        if appr and appr.status in ("PENDING", "REJECTED", "INVALIDATED"):
            raise BusinessRuleViolationException(
                f"Quotation cannot be sent while commercial approval status is '{appr.status}'. Authorization is required."
            )

    quotation.status = target_clean
    if current_user_id:
        quotation.updated_by_user_id = current_user_id

    await log_state_history(
        db=db,
        organization_id=organization_id,
        quotation_id=quotation.id,
        from_status=current_clean,
        to_status=target_clean,
        changed_by_user_id=current_user_id,
        reason=reason
    )

    await db.flush()
    return await get_quotation_by_id(db, organization_id, quotation.id)


async def get_quotation_history(
    db: AsyncSession,
    organization_id: uuid.UUID,
    quotation_id: uuid.UUID
) -> List[QuotationStateHistoryResponse]:
    """Retrieves all state transition audit records for a quotation within organization scope."""
    from app.services.quotations import get_quotation_by_id

    # Verify quotation exists in tenant
    await get_quotation_by_id(db, organization_id, quotation_id)

    stmt = (
        select(QuotationStateHistory)
        .options(selectinload(QuotationStateHistory.changed_by_user))
        .where(
            QuotationStateHistory.organization_id == organization_id,
            QuotationStateHistory.quotation_id == quotation_id
        )
        .order_by(QuotationStateHistory.created_at.desc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    response: List[QuotationStateHistoryResponse] = []
    for rec in records:
        user_name = None
        if rec.changed_by_user:
            user_name = rec.changed_by_user.full_name or rec.changed_by_user.email

        response.append(
            QuotationStateHistoryResponse(
                id=rec.id,
                organization_id=rec.organization_id,
                quotation_id=rec.quotation_id,
                from_status=rec.from_status,
                to_status=rec.to_status,
                changed_by_user_id=rec.changed_by_user_id,
                changed_by_user_name=user_name,
                reason=rec.reason,
                created_at=rec.created_at
            )
        )

    return response

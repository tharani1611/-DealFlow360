import uuid
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quotation import Quotation
from app.models.customer import Customer
from app.models.activity import Activity
from app.models.quotation_approval import QuotationApproval
from app.models.quotation_change_request import QuotationChangeRequest
from app.schemas.health_monitoring import StalledQuoteItem, StalledQuotesResponse


class StalledQuoteEngine:
    """Phase 54 — Authoritative Stalled Quote Detection Engine.
    
    Detects quotations where commercial progress has stalled past thresholds:
    - Days since quotation creation (>30 days in DRAFT)
    - Days since quotation sent (>14 days without customer activity)
    - Days pending executive approval (>5 days pending)
    
    Excludes accepted, rejected, cancelled, expired, or active change-request quotations to prevent false positives.
    """

    @staticmethod
    async def detect_stalled_quotes(
        session: AsyncSession,
        organization_id: uuid.UUID,
        days_threshold: int = 14,
    ) -> StalledQuotesResponse:
        # Fetch active candidate quotations
        stmt = select(Quotation).where(
            Quotation.organization_id == organization_id,
            Quotation.status.in_(["draft", "priced", "sent"]),
        )
        quotations = list((await session.execute(stmt)).scalars().all())

        now_utc = datetime.now(timezone.utc)
        stalled_items: List[StalledQuoteItem] = []
        total_value = Decimal("0.00")

        for q in quotations:
            # Check for active customer change request being processed
            cr_stmt = select(QuotationChangeRequest).where(
                QuotationChangeRequest.organization_id == organization_id,
                QuotationChangeRequest.quotation_id == q.id,
                QuotationChangeRequest.status == "PENDING",
            )
            has_pending_cr = (await session.execute(cr_stmt)).scalars().first() is not None
            if has_pending_cr:
                continue  # Legitimately active negotiation process

            # Check for pending executive approval
            app_stmt = select(QuotationApproval).where(
                QuotationApproval.organization_id == organization_id,
                QuotationApproval.quotation_id == q.id,
                QuotationApproval.status == "PENDING",
            )
            pending_approval = (await session.execute(app_stmt)).scalars().first()

            # Customer name lookup
            cust_stmt = select(Customer).where(Customer.id == q.customer_id, Customer.organization_id == organization_id)
            customer = (await session.execute(cust_stmt)).scalar_one_or_none()
            cust_name = customer.name if customer else "Unknown"

            # Customer activities lookup
            act_stmt = select(Activity).where(
                Activity.organization_id == organization_id,
                Activity.quotation_id == q.id,
            )
            activities = list((await session.execute(act_stmt)).scalars().all())

            last_act_at: Optional[datetime] = None
            last_cust_act_at: Optional[datetime] = None
            last_int_act_at: Optional[datetime] = None

            for act in activities:
                act_time = act.created_at or act.updated_at
                if act_time:
                    if act_time.tzinfo is None:
                        act_time = act_time.replace(tzinfo=timezone.utc)
                    if last_act_at is None or act_time > last_act_at:
                        last_act_at = act_time
                    if act.activity_type in ("call", "meeting", "email"):
                        if last_cust_act_at is None or act_time > last_cust_act_at:
                            last_cust_act_at = act_time
                    else:
                        if last_int_act_at is None or act_time > last_int_act_at:
                            last_int_act_at = act_time

            ref_date = last_act_at or q.updated_at or q.created_at
            if ref_date:
                if ref_date.tzinfo is None:
                    ref_date = ref_date.replace(tzinfo=timezone.utc)
                inactive_days = (now_utc - ref_date).days
            else:
                inactive_days = 999

            is_stalled = False
            stall_cat = "NEW"
            stall_reason = ""
            rec_action = ""

            if pending_approval and inactive_days >= 5:
                is_stalled = True
                stall_cat = "CRITICAL" if inactive_days >= 10 else "STALLED"
                stall_reason = f"Executive approval pending for {inactive_days} days."
                rec_action = "Remind assigned approvers to review quotation terms."

            elif q.status == "sent" and inactive_days >= days_threshold:
                is_stalled = True
                stall_cat = "CRITICAL" if inactive_days >= 30 else "STALLED" if inactive_days >= 21 else "AGING"
                stall_reason = f"Quotation sent {inactive_days} days ago without customer response."
                rec_action = "Schedule follow-up call with primary customer contact."

            elif q.status == "draft" and inactive_days >= 21:
                is_stalled = True
                stall_cat = "STALLED" if inactive_days >= 30 else "AGING"
                stall_reason = f"Draft quotation unissued for {inactive_days} days."
                rec_action = "Finalize pricing and issue quote or archive draft."

            if is_stalled:
                q_date = q.quotation_date if isinstance(q.quotation_date, date) else q.quotation_date.date() if q.quotation_date else date.today()
                stalled_items.append(StalledQuoteItem(
                    quotation_id=q.id,
                    quotation_number=q.quotation_number,
                    customer_id=q.customer_id,
                    customer_name=cust_name,
                    deal_id=q.deal_id,
                    status=q.status,
                    total_amount=q.total_amount,
                    quotation_date=q_date,
                    days_inactive=inactive_days,
                    stall_category=stall_cat,
                    stall_reason=stall_reason,
                    last_activity_at=last_act_at,
                    last_customer_activity_at=last_cust_act_at,
                    last_internal_activity_at=last_int_act_at,
                    recommended_next_action=rec_action,
                ))
                total_value += q.total_amount

        stalled_items.sort(key=lambda x: x.days_inactive, reverse=True)

        return StalledQuotesResponse(
            stalled_quotes=stalled_items,
            total_stalled_count=len(stalled_items),
            total_stalled_value=total_value,
            generated_at=now_utc,
        )


stalled_quote_engine = StalledQuoteEngine()

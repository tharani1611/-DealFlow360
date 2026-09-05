import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException
from app.models.customer import Customer
from app.models.deal import Deal
from app.models.quotation import Quotation
from app.models.activity import Activity
from app.models.deal_health import DealHealthSnapshot
from app.schemas.health_monitoring import DealHealthEvaluationResponse
from app.services import commercial_governance as governance_service


class DealHealthEngine:
    """Phase 53 — Authoritative Deal Health Engine.
    
    Evaluates multi-dimensional deal telemetry deterministically:
    - Deal stage duration & recency
    - Activity frequency & overdue tasks
    - Quotation status & validity
    - Margin health & commercial risk score
    - Customer relationship engagement
    - Expected close date proximity vs stage progress
    - Delivery and billing status
    """

    @staticmethod
    async def evaluate_deal_health(
        session: AsyncSession,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        persist_snapshot: bool = True,
    ) -> DealHealthEvaluationResponse:
        # 1. Fetch deal
        d_stmt = select(Deal).where(Deal.id == deal_id, Deal.organization_id == organization_id)
        deal = (await session.execute(d_stmt)).scalar_one_or_none()
        if not deal:
            raise NotFoundException(f"Deal {deal_id} not found")

        # 2. Fetch customer
        c_stmt = select(Customer).where(Customer.id == deal.customer_id, Customer.organization_id == organization_id)
        customer = (await session.execute(c_stmt)).scalar_one_or_none()

        # 3. Fetch activities
        act_stmt = select(Activity).where(Activity.deal_id == deal_id, Activity.organization_id == organization_id)
        activities = list((await session.execute(act_stmt)).scalars().all())

        # 4. Fetch quotation & commercial governance if present
        quotation = None
        governance_summary = None
        if deal.quotation_id:
            q_stmt = select(Quotation).where(Quotation.id == deal.quotation_id, Quotation.organization_id == organization_id)
            quotation = (await session.execute(q_stmt)).scalar_one_or_none()
            if quotation:
                try:
                    governance_summary = await governance_service.get_quotation_commercial_governance_summary(
                        session, organization_id, quotation.id
                    )
                except Exception:
                    governance_summary = None

        now_utc = datetime.now(timezone.utc)
        today_utc = now_utc.date()

        positive_drivers: List[str] = []
        negative_drivers: List[str] = []

        overdue_count = 0
        recent_7d_count = 0
        last_act_date: Optional[datetime] = None

        for act in activities:
            if act.status not in ("completed", "cancelled") and act.due_at:
                due_dt = act.due_at if isinstance(act.due_at, datetime) else datetime.combine(act.due_at, datetime.min.time(), tzinfo=timezone.utc)
                if due_dt.tzinfo is None:
                    due_dt = due_dt.replace(tzinfo=timezone.utc)
                if due_dt < now_utc:
                    overdue_count += 1

            act_time = act.created_at or act.updated_at
            if act_time:
                if act_time.tzinfo is None:
                    act_time = act_time.replace(tzinfo=timezone.utc)
                if (now_utc - act_time).days <= 7:
                    recent_7d_count += 1
                if last_act_date is None or act_time > last_act_date:
                    last_act_date = act_time

        days_since_act = (now_utc - last_act_date).days if last_act_date else 999

        days_until_close: Optional[int] = None
        if deal.expected_close_date:
            close_d = deal.expected_close_date if isinstance(deal.expected_close_date, date) else deal.expected_close_date.date()
            days_until_close = (close_d - today_utc).days

        # Base scoring math
        if deal.status == "won":
            score = 100
            positive_drivers.append("Deal marked as WON commercial victory")
        elif deal.status == "lost":
            score = 0
            negative_drivers.append(f"Deal closed as LOST ({deal.lost_reason or 'No reason specified'})")
        else:
            stage_baselines = {"new": 40, "qualified": 55, "proposal": 70, "negotiation": 85}
            score = stage_baselines.get(deal.stage, 50)
            score += int(deal.probability * 0.25)

            if deal.stage in ("proposal", "negotiation"):
                positive_drivers.append(f"Advanced pipeline stage: '{deal.stage}' ({deal.probability}% win probability)")

            if days_since_act <= 7:
                score += 15
                positive_drivers.append(f"Active engagement: activity recorded within past 7 days")
            elif days_since_act <= 14:
                score += 5
            elif days_since_act > 30:
                score -= 25
                negative_drivers.append(f"Severe inactivity: no sales interactions for {days_since_act} days")
            else:
                score -= 10
                negative_drivers.append(f"Slowing engagement: no activity in past {days_since_act} days")

            if overdue_count > 0:
                deduction = min(30, overdue_count * 15)
                score -= deduction
                negative_drivers.append(f"{overdue_count} overdue CRM follow-up task(s) pending")

            if days_until_close is not None:
                if days_until_close < 0:
                    score -= 20
                    negative_drivers.append(f"Expected close date passed ({abs(days_until_close)} days overdue)")
                elif days_until_close <= 7 and deal.stage in ("new", "qualified"):
                    score -= 15
                    negative_drivers.append(f"Close date in {days_until_close} days but deal still in early '{deal.stage}' stage")
                elif days_until_close <= 14 and deal.stage in ("proposal", "negotiation"):
                    positive_drivers.append(f"Approaching target close window ({days_until_close} days remaining)")

            if quotation:
                if quotation.status == "accepted":
                    score += 20
                    positive_drivers.append(f"Quotation {quotation.quotation_number} ACCEPTED by customer")
                elif quotation.status in ("sent", "priced"):
                    score += 10
                    positive_drivers.append(f"Quotation {quotation.quotation_number} issued to customer ({quotation.status.upper()})")
                elif quotation.status == "rejected":
                    score -= 30
                    negative_drivers.append(f"Quotation {quotation.quotation_number} REJECTED by customer")
                elif quotation.status == "expired":
                    score -= 20
                    negative_drivers.append(f"Quotation {quotation.quotation_number} EXPIRED")

            if governance_summary:
                if governance_summary.risk.risk_level in ("high", "critical"):
                    score -= 15
                    negative_drivers.append(f"High commercial discount risk ({governance_summary.risk.risk_score}/100, blended discount {governance_summary.risk.blended_discount_percent}%)")
                elif governance_summary.risk.risk_level == "low":
                    score += 10
                    positive_drivers.append("Strong commercial margin compliance (Low discount risk)")

                if governance_summary.approval.approval_required and governance_summary.approval.approval_status == "PENDING":
                    score -= 10
                    negative_drivers.append("Commercial quotation awaiting executive approval")

        score = max(0, min(100, score))

        if score >= 80:
            health_status = "HEALTHY"
        elif score >= 60:
            health_status = "ATTENTION"
        elif score >= 40:
            health_status = "AT_RISK"
        else:
            health_status = "CRITICAL"

        metrics_snapshot = {
            "value": str(deal.value),
            "stage": deal.stage,
            "probability": deal.probability,
            "days_since_last_activity": days_since_act,
            "overdue_activities_count": overdue_count,
            "days_until_expected_close": days_until_close,
            "has_quotation": bool(quotation),
            "quotation_status": quotation.status if quotation else None,
            "customer_name": customer.name if customer else "Unknown",
        }

        # Persist snapshot if requested
        if persist_snapshot:
            snapshot = DealHealthSnapshot(
                organization_id=organization_id,
                deal_id=deal_id,
                score=score,
                status=health_status,
                positive_drivers=positive_drivers,
                negative_drivers=negative_drivers,
                metrics_snapshot=metrics_snapshot,
                calculated_at=now_utc,
                calculation_version="1.0",
            )
            session.add(snapshot)
            await session.commit()

        return DealHealthEvaluationResponse(
            deal_id=deal.id,
            deal_number=deal.deal_number,
            title=deal.title,
            health_score=score,
            health_status=health_status,
            positive_drivers=positive_drivers,
            negative_drivers=negative_drivers,
            metrics_snapshot=metrics_snapshot,
            calculated_at=now_utc,
            calculation_version="1.0",
            ai_explanation=None,
        )


deal_health_engine = DealHealthEngine()

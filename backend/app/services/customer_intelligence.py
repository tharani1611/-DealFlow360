import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Set
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.core.exceptions import NotFoundException
from app.models.customer import Customer
from app.models.deal import Deal
from app.models.quotation import Quotation, QuotationItem
from app.models.activity import Activity
from app.models.contact import Contact
from app.schemas.intelligence import (
    SalesBriefingResponse,
    CustomerEngagementResponse,
    Customer360IntelligenceResponse,
    CustomerFinancialMetrics,
    CustomerSalesMetrics,
    CustomerEngagementDetails,
    CustomerHealthDetail,
    CustomerTrends,
)
from app.services.sales_intelligence import sales_intelligence_service
from app.services import intelligence as intelligence_service


class CustomerIntelligenceService:
    """Customer Intelligence (Customer 360) service providing relationship health, commercial observations, segmentation, and briefings."""

    @staticmethod
    async def get_customer_360_facts(
        db: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Retrieves complete Customer 360 facts across deals, quotations, engagement, and contacts."""
        facts = await sales_intelligence_service.build_customer_structured_facts(db, organization_id, customer_id)
        if "error" in facts:
            raise NotFoundException(facts["error"])
        return facts

    @staticmethod
    async def get_customer_360_intelligence(
        db: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> Customer360IntelligenceResponse:
        """Calculates comprehensive deterministic Customer 360 intelligence, health score, positive/negative drivers, segmentation, and trends."""
        # 1. Fetch customer record
        cust_q = await db.execute(
            select(Customer).where(
                and_(
                    Customer.id == customer_id,
                    Customer.organization_id == organization_id
                )
            )
        )
        customer = cust_q.scalar_one_or_none()
        if not customer:
            raise NotFoundException(f"Customer with ID '{customer_id}' not found.")

        now_utc = datetime.now(timezone.utc)
        thirty_days_ago = now_utc - timedelta(days=30)
        seven_days_ago = now_utc - timedelta(days=7)

        # 2. Fetch customer deals
        deals_q = await db.execute(
            select(Deal).where(
                and_(
                    Deal.organization_id == organization_id,
                    Deal.customer_id == customer_id
                )
            )
        )
        deals = list(deals_q.scalars().all())

        won_deals = [d for d in deals if d.status == "won"]
        lost_deals = [d for d in deals if d.status == "lost"]
        open_deals = [d for d in deals if d.status == "open"]

        won_rev = sum((d.value for d in won_deals), Decimal("0.00"))
        open_pipe = sum((d.value for d in open_deals), Decimal("0.00"))
        weighted_pipe = sum((d.value * Decimal(d.probability) / Decimal(100) for d in open_deals), Decimal("0.00"))

        closed_count = len(won_deals) + len(lost_deals)
        win_rate = float((len(won_deals) / closed_count) * 100) if closed_count > 0 else 0.0

        avg_cycle_days = 0
        if won_deals:
            cycle_times = []
            for d in won_deals:
                c_at = d.created_at or now_utc
                u_at = d.updated_at or now_utc
                if c_at.tzinfo is None:
                    c_at = c_at.replace(tzinfo=timezone.utc)
                if u_at.tzinfo is None:
                    u_at = u_at.replace(tzinfo=timezone.utc)
                cycle_times.append((u_at - c_at).days)
            avg_cycle_days = int(sum(cycle_times) / len(cycle_times)) if cycle_times else 0

        avg_deal_val = Decimal("0.00")
        if len(won_deals) > 0:
            avg_deal_val = won_rev / Decimal(len(won_deals))
        elif len(open_deals) > 0:
            avg_deal_val = open_pipe / Decimal(len(open_deals))

        # 3. Fetch quotations & items
        quotes_q = await db.execute(
            select(Quotation).where(
                and_(
                    Quotation.organization_id == organization_id,
                    Quotation.customer_id == customer_id
                )
            )
        )
        quotations = list(quotes_q.scalars().all())
        accepted_quotes = [q for q in quotations if q.status == "accepted"]
        quotation_rev = sum((q.total_amount for q in accepted_quotes), Decimal("0.00"))

        # Fetch purchased products
        purchased_product_ids: Set[uuid.UUID] = set()
        quote_items_q = await db.execute(
            select(QuotationItem.product_id, QuotationItem.line_total, QuotationItem.unit_cost, QuotationItem.quantity)
            .join(Quotation, QuotationItem.quotation_id == Quotation.id)
            .where(
                and_(
                    Quotation.organization_id == organization_id,
                    Quotation.customer_id == customer_id,
                    Quotation.status == "accepted"
                )
            )
        )
        quote_item_rows = quote_items_q.all()
        gross_margin = Decimal("0.00")

        for p_id, line_tot, unit_cost, qty in quote_item_rows:
            if p_id:
                purchased_product_ids.add(p_id)
            if line_tot:
                item_cost = (unit_cost or Decimal("0.00")) * Decimal(qty or 1)
                gross_margin += (line_tot - item_cost)

        margin_pct = float((gross_margin / won_rev) * 100) if won_rev > Decimal("0.00") else 0.0

        # 4. Fetch activities
        act_q = await db.execute(
            select(Activity).where(
                and_(
                    Activity.organization_id == organization_id,
                    Activity.customer_id == customer_id
                )
            )
        )
        activities = list(act_q.scalars().all())

        last_act_dt: Optional[datetime] = None
        act_7d = 0
        act_30d = 0
        overdue_cnt = 0
        completed_cnt = 0

        for act in activities:
            a_dt = act.created_at or act.updated_at
            if a_dt:
                if a_dt.tzinfo is None:
                    a_dt = a_dt.replace(tzinfo=timezone.utc)
                if last_act_dt is None or a_dt > last_act_dt:
                    last_act_dt = a_dt
                if a_dt >= seven_days_ago:
                    act_7d += 1
                if a_dt >= thirty_days_ago:
                    act_30d += 1

            if act.status == "completed":
                completed_cnt += 1
            elif act.status not in ("completed", "cancelled") and act.due_at:
                due_dt = act.due_at if isinstance(act.due_at, datetime) else datetime.combine(act.due_at, datetime.min.time(), tzinfo=timezone.utc)
                if due_dt.tzinfo is None:
                    due_dt = due_dt.replace(tzinfo=timezone.utc)
                if due_dt < now_utc:
                    overdue_cnt += 1

        days_since_act = (now_utc - last_act_dt).days if last_act_dt else 999

        if days_since_act <= 7:
            recency = "VERY_RECENT"
        elif days_since_act <= 14:
            recency = "RECENT"
        elif days_since_act <= 30:
            recency = "AGING"
        elif days_since_act <= 60:
            recency = "STALE"
        else:
            recency = "INACTIVE"

        # 5. Deterministic Health Score (0-100) & Drivers
        health_score = 50
        positive_drivers: List[str] = []
        negative_drivers: List[str] = []

        if days_since_act <= 7:
            health_score += 20
            positive_drivers.append("Frequent recent interaction (activity within 7 days)")
        elif days_since_act <= 14:
            health_score += 10
            positive_drivers.append("Regular interaction (activity within 14 days)")
        elif days_since_act > 30:
            health_score -= 20
            negative_drivers.append(f"No recorded activity in {days_since_act} days")

        if win_rate >= 60.0:
            health_score += 15
            positive_drivers.append(f"Strong historical win rate ({win_rate:.1f}%)")
        elif win_rate < 30.0 and closed_count > 0:
            health_score -= 10
            negative_drivers.append(f"Low win rate ({win_rate:.1f}%)")

        if open_pipe > Decimal("0.00"):
            health_score += 15
            positive_drivers.append(f"Active open pipeline (${open_pipe:,.2f})")

        if act_30d >= 3:
            health_score += 10
            positive_drivers.append(f"High engagement density ({act_30d} activities in 30d)")

        if len(accepted_quotes) > 0:
            health_score += 10
            positive_drivers.append(f"Accepted commercial quotations ({len(accepted_quotes)})")

        if overdue_cnt > 0:
            health_score -= (overdue_cnt * 10)
            negative_drivers.append(f"{overdue_cnt} overdue follow-up task(s)")

        if len(open_deals) > 0 and act_30d == 0:
            health_score -= 15
            negative_drivers.append("Open pipeline exists without recent customer interactions")

        health_score = max(0, min(100, health_score))

        if health_score >= 80:
            health_category = "HEALTHY"
        elif health_score >= 65:
            health_category = "ENGAGED"
        elif health_score >= 50:
            health_category = "ATTENTION"
        elif health_score >= 30:
            health_category = "AT_RISK"
        else:
            health_category = "INACTIVE"

        # 6. Customer Segmentation
        if won_rev >= Decimal("100000.00") or open_pipe >= Decimal("100000.00"):
            segment = "ENTERPRISE"
        elif won_rev >= Decimal("50000.00") or open_pipe >= Decimal("50000.00"):
            segment = "HIGH_VALUE"
        elif len(won_deals) >= 2 or open_pipe >= Decimal("20000.00"):
            segment = "GROWTH"
        elif len(won_deals) >= 1:
            segment = "ACTIVE"
        elif len(open_deals) >= 1:
            segment = "DEVELOPING"
        elif health_category in ("AT_RISK", "INACTIVE"):
            segment = "AT_RISK"
        else:
            segment = "INACTIVE"

        # 7. Customer Lifecycle
        if len(won_deals) >= 3 and days_since_act <= 30:
            lifecycle = "MATURE"
        elif len(won_deals) >= 1 and len(open_deals) >= 1:
            lifecycle = "GROWING"
        elif len(won_deals) >= 1:
            lifecycle = "ACTIVE"
        elif len(deals) >= 1 and len(won_deals) == 0:
            lifecycle = "DEVELOPING"
        elif health_category == "AT_RISK":
            lifecycle = "AT_RISK"
        elif days_since_act > 60 and len(open_deals) == 0:
            lifecycle = "INACTIVE"
        else:
            lifecycle = "NEW"

        # 8. Trends
        rev_trend = "UP" if won_rev > Decimal("0.00") else "STABLE"
        deal_trend = "UP" if len(open_deals) > 0 else "STABLE"
        act_trend = "UP" if act_7d > 0 else ("DOWN" if days_since_act > 30 else "STABLE")
        pipe_trend = "UP" if open_pipe > Decimal("0.00") else "STABLE"
        eng_trend = "UP" if recency in ("VERY_RECENT", "RECENT") else ("DOWN" if recency in ("STALE", "INACTIVE") else "STABLE")

        return Customer360IntelligenceResponse(
            customer_id=customer.id,
            customer_name=customer.name,
            industry=getattr(customer, "industry", None),
            financials=CustomerFinancialMetrics(
                total_won_revenue=f"{won_rev:.2f}",
                open_pipeline=f"{open_pipe:.2f}",
                weighted_pipeline=f"{weighted_pipe:.2f}",
                quotation_revenue=f"{quotation_rev:.2f}",
                gross_margin=f"{gross_margin:.2f}",
                margin_percentage=round(margin_pct, 1),
                average_deal_value=f"{avg_deal_val:.2f}"
            ),
            sales=CustomerSalesMetrics(
                deal_count=len(deals),
                won_deal_count=len(won_deals),
                lost_deal_count=len(lost_deals),
                open_deal_count=len(open_deals),
                win_rate_percent=round(win_rate, 1),
                average_sales_cycle_days=avg_cycle_days
            ),
            engagement=CustomerEngagementDetails(
                last_activity_date=last_act_dt,
                days_since_last_activity=days_since_act,
                recency_classification=recency,
                activities_last_7_days=act_7d,
                activities_last_30_days=act_30d,
                overdue_activities_count=overdue_cnt,
                completed_activities_count=completed_cnt
            ),
            health=CustomerHealthDetail(
                health_score=health_score,
                health_category=health_category,
                positive_drivers=positive_drivers,
                negative_drivers=negative_drivers,
                segment=segment,
                lifecycle_stage=lifecycle,
                risk_signals=negative_drivers
            ),
            trends=CustomerTrends(
                revenue_trend=rev_trend,
                deal_trend=deal_trend,
                activity_trend=act_trend,
                pipeline_trend=pipe_trend,
                engagement_trend=eng_trend
            ),
            purchased_product_ids=list(purchased_product_ids)
        )

    @staticmethod
    async def generate_customer_briefing(
        db: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> SalesBriefingResponse:
        """Generates executive Sales & Account Briefing for meeting preparation."""
        return await intelligence_service.get_sales_briefing(db, organization_id, customer_id)

    @staticmethod
    async def get_customer_health(
        db: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> CustomerEngagementResponse:
        """Calculates deterministic customer engagement score and relationship health classification."""
        return await intelligence_service.calculate_customer_engagement(db, organization_id, customer_id)


customer_intelligence_service = CustomerIntelligenceService()


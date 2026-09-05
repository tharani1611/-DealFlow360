import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.quotation import Quotation, QuotationItem
from app.models.activity import Activity
from app.models.product import Product
from app.models.quotation_approval import QuotationApproval

from app.services import commercial_governance as governance_service
from app.services import margins as margin_service
from app.services import pricing as pricing_service
from app.services import intelligence as intelligence_service


class SalesIntelligenceService:
    """Phase 26 — Sales Intelligence Foundation service constructing normalized structured facts for AI consumption."""

    @staticmethod
    async def build_deal_structured_facts(
        db: AsyncSession,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Gathers complete structured telemetry for a single deal including commercial governance and activity facts."""
        deal_q = await db.execute(
            select(Deal).where(and_(Deal.id == deal_id, Deal.organization_id == organization_id))
        )
        deal = deal_q.scalar_one_or_none()
        if not deal:
            return {"error": f"Deal {deal_id} not found."}

        # Customer facts
        cust_q = await db.execute(
            select(Customer).where(and_(Customer.id == deal.customer_id, Customer.organization_id == organization_id))
        )
        customer = cust_q.scalar_one_or_none()

        # Activities
        act_q = await db.execute(
            select(Activity).where(and_(Activity.deal_id == deal_id, Activity.organization_id == organization_id))
        )
        activities = list(act_q.scalars().all())

        now_utc = datetime.now(timezone.utc)
        today_utc = now_utc.date()

        last_act_date: Optional[datetime] = None
        overdue_acts = 0
        pending_acts = 0
        completed_acts = 0

        for act in activities:
            if act.status == "completed":
                completed_acts += 1
            elif act.status == "pending":
                pending_acts += 1
                if act.due_at:
                    due_dt = act.due_at if isinstance(act.due_at, datetime) else datetime.combine(act.due_at, datetime.min.time(), tzinfo=timezone.utc)
                    if due_dt.tzinfo is None:
                        due_dt = due_dt.replace(tzinfo=timezone.utc)
                    if due_dt < now_utc:
                        overdue_acts += 1

            act_dt = act.created_at or act.updated_at
            if act_dt:
                if act_dt.tzinfo is None:
                    act_dt = act_dt.replace(tzinfo=timezone.utc)
                if last_act_date is None or act_dt > last_act_date:
                    last_act_date = act_dt

        days_inactive = (now_utc - last_act_date).days if last_act_date else 999

        days_to_close: Optional[int] = None
        if deal.expected_close_date:
            close_d = deal.expected_close_date if isinstance(deal.expected_close_date, date) else deal.expected_close_date.date()
            days_to_close = (close_d - today_utc).days

        # Health metrics
        health_resp = await intelligence_service.calculate_deal_health(db, organization_id, deal_id)

        # Quotation & Commercial Governance facts
        quotation_facts: Optional[Dict[str, Any]] = None
        governance_facts: Optional[Dict[str, Any]] = None

        if deal.quotation_id:
            q_query = await db.execute(
                select(Quotation)
                .options(selectinload(Quotation.items), selectinload(Quotation.approvals))
                .where(and_(Quotation.id == deal.quotation_id, Quotation.organization_id == organization_id))
            )
            quotation = q_query.scalar_one_or_none()

            if quotation:
                quotation_facts = {
                    "quotation_id": str(quotation.id),
                    "quotation_number": quotation.quotation_number,
                    "status": quotation.status,
                    "subtotal": str(quotation.subtotal),
                    "discount_amount": str(quotation.total_discount),
                    "total_amount": str(quotation.total_amount),
                    "valid_until": str(quotation.valid_until) if quotation.valid_until else None,
                    "item_count": len(quotation.items),
                    "items": [
                        {
                            "product_name": item.product_name,
                            "quantity": item.quantity,
                            "unit_price": str(item.unit_price),
                            "discount_percent": str(item.discount_percent),
                            "subtotal": str(item.subtotal),
                        }
                        for item in quotation.items
                    ]
                }

                # Comprehensive Governance Pipeline
                gov_resp = await governance_service.get_quotation_commercial_governance_summary(db, organization_id, quotation.id)
                governance_facts = gov_resp.model_dump(mode="json")

        return {
            "deal": {
                "id": str(deal.id),
                "deal_number": deal.deal_number,
                "title": deal.title,
                "value": str(deal.value),
                "stage": deal.stage,
                "status": deal.status,
                "probability": deal.probability,
                "days_inactive": days_inactive,
                "days_until_expected_close": days_to_close,
                "expected_close_date": str(deal.expected_close_date) if deal.expected_close_date else None,
                "health_score": health_resp.health_score,
                "health_status": health_resp.health_status,
                "risk_level": health_resp.risk_level,
                "risk_factors": [rf.model_dump(mode="json") for rf in health_resp.risk_factors],
            },
            "customer": {
                "id": str(customer.id) if customer else None,
                "name": customer.name if customer else "Unknown",
                "industry": getattr(customer, "industry", None),
            },
            "activity_summary": {
                "total_activities": len(activities),
                "completed": completed_acts,
                "pending": pending_acts,
                "overdue": overdue_acts,
                "days_since_last_activity": days_inactive,
            },
            "quotation": quotation_facts,
            "commercial_governance": governance_facts,
        }

    @staticmethod
    async def build_customer_structured_facts(
        db: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Gathers complete Customer 360 facts across deals, quotations, margins, and engagement metrics."""
        cust_q = await db.execute(
            select(Customer).where(and_(Customer.id == customer_id, Customer.organization_id == organization_id))
        )
        customer = cust_q.scalar_one_or_none()
        if not customer:
            return {"error": f"Customer {customer_id} not found."}

        # Contacts
        contact_q = await db.execute(
            select(Contact).where(and_(Contact.customer_id == customer_id, Contact.organization_id == organization_id))
        )
        contacts = list(contact_q.scalars().all())

        # Deals
        deal_q = await db.execute(
            select(Deal).where(and_(Deal.customer_id == customer_id, Deal.organization_id == organization_id))
        )
        deals = list(deal_q.scalars().all())

        open_deals = [d for d in deals if d.status == "open"]
        won_deals = [d for d in deals if d.status == "won"]
        lost_deals = [d for d in deals if d.status == "lost"]

        open_val = sum((d.value for d in open_deals), Decimal("0.00"))
        won_val = sum((d.value for d in won_deals), Decimal("0.00"))

        # Quotations
        quote_q = await db.execute(
            select(Quotation).where(and_(Quotation.customer_id == customer_id, Quotation.organization_id == organization_id))
        )
        quotations = list(quote_q.scalars().all())

        accepted_quotes = [q for q in quotations if q.status == "accepted"]
        rejected_quotes = [q for q in quotations if q.status == "rejected"]

        total_quote_val = sum((q.total_amount for q in quotations), Decimal("0.00"))

        # Engagement metrics
        eng_resp = await intelligence_service.calculate_customer_engagement(db, organization_id, customer_id)

        return {
            "customer": {
                "id": str(customer.id),
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "industry": getattr(customer, "industry", None),
                "is_active": customer.is_active,
            },
            "contacts": [
                {
                    "id": str(c.id),
                    "name": f"{c.first_name} {c.last_name}",
                    "email": c.email,
                    "is_primary": c.is_primary,
                }
                for c in contacts
            ],
            "engagement": eng_resp.model_dump(mode="json"),
            "deal_summary": {
                "total_deals": len(deals),
                "open_deals_count": len(open_deals),
                "won_deals_count": len(won_deals),
                "lost_deals_count": len(lost_deals),
                "open_deals_value": str(open_val),
                "won_deals_value": str(won_val),
            },
            "quotation_summary": {
                "total_quotations": len(quotations),
                "accepted_count": len(accepted_quotes),
                "rejected_count": len(rejected_quotes),
                "total_quotation_value": str(total_quote_val),
            },
        }

    @staticmethod
    async def build_pipeline_structured_facts(
        db: AsyncSession,
        organization_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Gathers aggregate pipeline, commercial risk, and attention center facts."""
        dash = await intelligence_service.calculate_pipeline_intelligence(db, organization_id)
        att = await intelligence_service.get_sales_attention_items(db, organization_id)

        return {
            "dashboard_intelligence": dash.model_dump(mode="json"),
            "attention_center": att.model_dump(mode="json"),
        }


sales_intelligence_service = SalesIntelligenceService()

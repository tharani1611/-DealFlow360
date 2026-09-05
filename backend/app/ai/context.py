import uuid
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.contact import Contact
from app.models.product import Product
from app.models.quotation import Quotation
from app.models.deal import Deal
from app.models.activity import Activity
from app.core.exceptions import NotFoundException


class AIContextBuilder:
    """Retrieves and sanitizes tenant-isolated CRM data for AI context inputs."""

    @staticmethod
    async def build_customer_context(
        db: AsyncSession,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Builds safe AI context for a customer record."""
        # 1. Fetch Customer
        c_stmt = select(Customer).where(Customer.id == customer_id, Customer.organization_id == organization_id)
        c_res = await db.execute(c_stmt)
        customer = c_res.scalar_one_or_none()
        if not customer:
            raise NotFoundException("Target customer requested was not found")

        # 2. Fetch Contacts
        ct_stmt = select(Contact).where(Contact.customer_id == customer_id, Contact.organization_id == organization_id)
        ct_res = await db.execute(ct_stmt)
        contacts = ct_res.scalars().all()

        # 3. Fetch Deals
        d_stmt = select(Deal).where(Deal.customer_id == customer_id, Deal.organization_id == organization_id)
        d_res = await db.execute(d_stmt)
        deals = d_res.scalars().all()

        # 4. Fetch Quotations
        q_stmt = select(Quotation).where(Quotation.customer_id == customer_id, Quotation.organization_id == organization_id)
        q_res = await db.execute(q_stmt)
        quotations = q_res.scalars().all()

        # 5. Fetch Recent Activities
        act_stmt = (
            select(Activity)
            .where(Activity.customer_id == customer_id, Activity.organization_id == organization_id)
            .order_by(Activity.created_at.desc())
            .limit(10)
        )
        act_res = await db.execute(act_stmt)
        activities = act_res.scalars().all()

        return {
            "customer": {
                "id": str(customer.id),
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "city": customer.city,
                "state": customer.state,
                "country": customer.country,
                "is_active": customer.is_active
            },
            "contacts_count": len(contacts),
            "contacts": [
                {"name": f"{ct.first_name} {ct.last_name or ''}".strip(), "job_title": ct.job_title, "email": ct.email}
                for ct in contacts
            ],
            "deals_summary": [
                {"deal_number": d.deal_number, "title": d.title, "stage": d.stage, "status": d.status, "value": float(d.value)}
                for d in deals
            ],
            "quotations_summary": [
                {"quotation_number": q.quotation_number, "status": q.status, "total_amount": float(q.total_amount)}
                for q in quotations
            ],
            "recent_activities": [
                {"type": a.activity_type, "title": a.title, "status": a.status, "due_at": a.due_at.isoformat() if a.due_at else None}
                for a in activities
            ]
        }

    @staticmethod
    async def build_deal_context(
        db: AsyncSession,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Builds safe AI context for a deal record."""
        # 1. Fetch Deal
        d_stmt = select(Deal).where(Deal.id == deal_id, Deal.organization_id == organization_id)
        d_res = await db.execute(d_stmt)
        deal = d_res.scalar_one_or_none()
        if not deal:
            raise NotFoundException("Target deal requested was not found")

        # 2. Fetch Customer
        c_stmt = select(Customer).where(Customer.id == deal.customer_id, Customer.organization_id == organization_id)
        c_res = await db.execute(c_stmt)
        customer = c_res.scalar_one_or_none()

        # 3. Fetch Quotation if attached
        quotation_data = None
        if deal.quotation_id:
            q_stmt = select(Quotation).where(Quotation.id == deal.quotation_id, Quotation.organization_id == organization_id)
            q_res = await db.execute(q_stmt)
            quotation = q_res.scalar_one_or_none()
            if quotation:
                quotation_data = {
                    "quotation_number": quotation.quotation_number,
                    "status": quotation.status,
                    "subtotal": float(quotation.subtotal),
                    "total_amount": float(quotation.total_amount)
                }

        # 4. Fetch Deal Activities
        act_stmt = (
            select(Activity)
            .where(Activity.deal_id == deal_id, Activity.organization_id == organization_id)
            .order_by(Activity.created_at.desc())
            .limit(15)
        )
        act_res = await db.execute(act_stmt)
        activities = act_res.scalars().all()

        return {
            "deal": {
                "id": str(deal.id),
                "deal_number": deal.deal_number,
                "title": deal.title,
                "description": deal.description,
                "stage": deal.stage,
                "status": deal.status,
                "value": float(deal.value),
                "probability": deal.probability,
                "expected_close_date": deal.expected_close_date.isoformat() if deal.expected_close_date else None,
                "lost_reason": deal.lost_reason,
                "notes": deal.notes
            },
            "customer": {
                "name": customer.name if customer else "Unknown Customer",
                "email": customer.email if customer else None
            },
            "quotation": quotation_data,
            "activities": [
                {"type": a.activity_type, "title": a.title, "status": a.status, "priority": a.priority, "due_at": a.due_at.isoformat() if a.due_at else None}
                for a in activities
            ]
        }

    @staticmethod
    async def build_assistant_context(
        db: AsyncSession,
        organization_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Builds concise tenant context summary for general CRM assistant inquiries."""
        # Active Deals
        d_stmt = (
            select(Deal)
            .where(Deal.organization_id == organization_id)
            .order_by(Deal.created_at.desc())
            .limit(15)
        )
        d_res = await db.execute(d_stmt)
        deals = d_res.scalars().all()

        # Pending Activities
        act_stmt = (
            select(Activity)
            .where(Activity.organization_id == organization_id, Activity.status == "pending")
            .order_by(Activity.due_at.asc().nulls_last())
            .limit(15)
        )
        act_res = await db.execute(act_stmt)
        activities = act_res.scalars().all()

        return {
            "deals": [
                {"id": str(d.id), "deal_number": d.deal_number, "title": d.title, "stage": d.stage, "status": d.status, "value": float(d.value), "expected_close": d.expected_close_date.isoformat() if d.expected_close_date else None}
                for d in deals
            ],
            "pending_activities": [
                {"id": str(a.id), "type": a.activity_type, "title": a.title, "priority": a.priority, "due_at": a.due_at.isoformat() if a.due_at else None}
                for a in activities
            ]
        }

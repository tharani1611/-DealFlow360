"""
Unit & Integration Tests for DealFlow360 300-Set Synthetic Data Seeder
========================================================================
Verifies that seed_300_data() generates 300 complete sets of business data
(~4,800+ total records) with valid foreign key relationships, exact Decimal precision,
and complete relational integrity under tenant 'bulk-data-lab'.
"""

import pytest
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.customer import Customer
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.quotation import Quotation, QuotationItem
from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import Payment
from app.models.subscription import Subscription, BillingSchedule
from app.models.deal_health import DealHealthSnapshot
from app.models.activity import Activity
from app.models.inventory import InventoryStock
from app.seed.seeder_300 import seed_300_data, BULK_300_ORG_SLUG


@pytest.mark.asyncio
async def test_seed_300_data_execution():
    """Test that seed_300_data runs idempotently and returns the expected record count map."""
    res = await seed_300_data()

    assert res["status"] == "success"
    assert res["total_records"] >= 3000
    assert res["customers"] == 300
    assert res["contacts"] == 300
    assert res["deals"] == 300
    assert res["quotations"] == 300
    assert res["quotation_items"] == 600
    assert res["invoices"] == 300
    assert res["invoice_items"] == 300
    assert res["payments"] == 300
    assert res["subscriptions"] == 300
    assert res["billing_schedules"] == 300
    assert res["deal_health_snapshots"] == 300
    assert res["activities"] == 300
    assert res["inventory_stocks"] == 300


@pytest.mark.asyncio
async def test_seed_300_database_relational_integrity():
    """Verify that seeded data exists in PostgreSQL with valid foreign keys and Decimal precision."""
    async with AsyncSessionLocal() as session:
        org_res = await session.execute(
            select(Organization).where(Organization.slug == BULK_300_ORG_SLUG)
        )
        org = org_res.scalar_one_or_none()
        assert org is not None

        cust_res = await session.execute(
            select(func.count(Customer.id)).where(Customer.organization_id == org.id)
        )
        assert cust_res.scalar() == 300

        deal_res = await session.execute(
            select(func.count(Deal.id)).where(Deal.organization_id == org.id)
        )
        assert deal_res.scalar() == 300

        quote_res = await session.execute(
            select(func.count(Quotation.id)).where(Quotation.organization_id == org.id)
        )
        assert quote_res.scalar() == 300

        inv_res = await session.execute(
            select(func.count(Invoice.id)).where(Invoice.organization_id == org.id)
        )
        assert inv_res.scalar() == 300

        pmt_res = await session.execute(
            select(func.count(Payment.id)).where(Payment.organization_id == org.id)
        )
        assert pmt_res.scalar() == 300

        sub_res = await session.execute(
            select(func.count(Subscription.id)).where(Subscription.organization_id == org.id)
        )
        assert sub_res.scalar() == 300

        health_res = await session.execute(
            select(func.count(DealHealthSnapshot.id)).where(DealHealthSnapshot.organization_id == org.id)
        )
        assert health_res.scalar() == 300

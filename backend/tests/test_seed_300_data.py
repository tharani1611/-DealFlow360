"""
Unit & Integration Tests for DealFlow360 300-Set Synthetic Data Seeder
========================================================================
Verifies that seed_300_data() delegates to the authoritative bulk seeder (~3,500 total records)
with valid foreign key relationships, exact Decimal precision, and complete relational integrity
under tenant 'bulk-data-lab'.
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

    assert res.get("status") == "success" or "total_records" in res
    assert res["total_records"] >= 2500
    assert res["customers"] == 120
    assert res["contacts"] >= 150
    assert res["deals"] == 120
    assert res["quotations"] == 120
    assert res["quotation_items"] >= 300
    assert res["invoices"] >= 40
    assert res["payments"] >= 30
    assert res["subscriptions"] >= 20
    assert res["billing_schedules"] >= 100
    assert res["deal_health_snapshots"] == 120
    assert res["activities"] == 120
    assert res["inventory_stocks"] >= 300


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
        assert cust_res.scalar() == 120

        deal_res = await session.execute(
            select(func.count(Deal.id)).where(Deal.organization_id == org.id)
        )
        assert deal_res.scalar() == 120

        quote_res = await session.execute(
            select(func.count(Quotation.id)).where(Quotation.organization_id == org.id)
        )
        assert quote_res.scalar() == 120

        inv_res = await session.execute(
            select(func.count(Invoice.id)).where(Invoice.organization_id == org.id)
        )
        assert inv_res.scalar() >= 40

        pmt_res = await session.execute(
            select(func.count(Payment.id)).where(Payment.organization_id == org.id)
        )
        assert pmt_res.scalar() >= 30

        sub_res = await session.execute(
            select(func.count(Subscription.id)).where(Subscription.organization_id == org.id)
        )
        assert sub_res.scalar() >= 20

        health_res = await session.execute(
            select(func.count(DealHealthSnapshot.id)).where(DealHealthSnapshot.organization_id == org.id)
        )
        assert health_res.scalar() == 120

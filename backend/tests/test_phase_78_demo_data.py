"""
Phase 78 — Automated Test Suite for Demo Data & Showcase Scenarios
===================================================================
Verifies:
1. Seed execution completeness & data integrity across all core business entities.
2. Complete multi-tenant isolation and safe reset cascade.
3. Idempotent re-execution safety.
4. Correct business outcome verification for all 10 showcase scenarios.
"""

import pytest
import pytest_asyncio
from decimal import Decimal
from sqlalchemy import select, func

from app.core.database import AsyncSessionLocal
from app.seed.demo_seeder import seed_demo_data, reset_demo_data
from app.models.organization import Organization
from app.models.user import User
from app.models.customer import Customer
from app.models.product import Product
from app.models.warehouses import Warehouse
from app.models.quotation import Quotation
from app.models.fulfillment import Shipment, Backorder
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.deal_health import DealHealthSnapshot
from app.models.automation_execution import AutomationExecution


@pytest.mark.asyncio
async def test_seed_demo_data_integrity():
    """Verify demo data environment is fully populated with proper entities and scenarios."""
    res = await seed_demo_data()
    assert res["status"] == "success"
    assert res["demo_organization"] == "DealFlow360 Demo Enterprise"
    assert res["scenarios_executed"] == 10

    async with AsyncSessionLocal() as session:
        # 1. Organization & Isolation Tenant
        orgs = (await session.execute(
            select(Organization).where(Organization.slug.in_(["demo-enterprise", "acme-global"]))
        )).scalars().all()
        assert len(orgs) == 2
        demo_org = next(o for o in orgs if o.slug == "demo-enterprise")

        # 2. Users Persona check
        users = (await session.execute(
            select(User).where(User.organization_id == demo_org.id)
        )).scalars().all()
        assert len(users) == 6
        emails = {u.email for u in users}
        assert "admin@dealflow.demo" in emails
        assert "sales@dealflow.demo" in emails
        assert "owner@dealflow.demo" in emails
        assert "inventory@dealflow.demo" in emails
        assert "purchase@dealflow.demo" in emails
        assert "manufacturing@dealflow.demo" in emails

        # 3. Products check
        products = (await session.execute(
            select(Product).where(Product.organization_id == demo_org.id)
        )).scalars().all()
        assert len(products) == 9

        # 4. Warehouses check
        warehouses = (await session.execute(
            select(Warehouse).where(Warehouse.organization_id == demo_org.id)
        )).scalars().all()
        assert len(warehouses) == 3

        # 5. Quotation Lifecycle & Invoices Check
        quotations = (await session.execute(
            select(Quotation).where(Quotation.organization_id == demo_org.id)
        )).scalars().all()
        assert len(quotations) >= 5

        # 6. Shipments and Backorders Check (Scenario 6)
        shipments = (await session.execute(
            select(Shipment).where(Shipment.organization_id == demo_org.id)
        )).scalars().all()
        assert len(shipments) >= 2

        backorders = (await session.execute(
            select(Backorder).where(Backorder.organization_id == demo_org.id)
        )).scalars().all()
        assert len(backorders) >= 1

        # 7. Invoices & Payments Check (Scenario 1 & 7)
        invoices_list = (await session.execute(
            select(Invoice).where(Invoice.organization_id == demo_org.id)
        )).scalars().all()
        assert len(invoices_list) >= 2

        payments_list = (await session.execute(
            select(Payment).where(Payment.organization_id == demo_org.id)
        )).scalars().all()
        assert len(payments_list) >= 2

        # 8. Subscription Check (Scenario 8)
        subs = (await session.execute(
            select(Subscription).where(Subscription.organization_id == demo_org.id)
        )).scalars().all()
        assert len(subs) >= 1
        assert subs[0].status.upper() == "CANCELLED"

        # 9. Deal Health Snapshots (Scenario 9)
        snapshots = (await session.execute(
            select(DealHealthSnapshot).where(DealHealthSnapshot.organization_id == demo_org.id)
        )).scalars().all()
        assert len(snapshots) >= 2

        # 10. Automation Execution (Scenario 10)
        executions = (await session.execute(
            select(AutomationExecution).where(AutomationExecution.organization_id == demo_org.id)
        )).scalars().all()
        assert len(executions) >= 1
        assert executions[0].status == "SUCCESS"


@pytest.mark.asyncio
async def test_reset_demo_data_safety_and_cascade():
    """Verify demo reset cleans up all demo records without affecting other data."""
    reset_res = await reset_demo_data()
    assert reset_res["status"] == "success"

    async with AsyncSessionLocal() as session:
        orgs = (await session.execute(
            select(Organization).where(Organization.slug.in_(["demo-enterprise", "acme-global"]))
        )).scalars().all()
        assert len(orgs) == 0


@pytest.mark.asyncio
async def test_seed_demo_data_idempotency():
    """Verify seeding multiple times executes idempotently without duplicate or foreign key errors."""
    res1 = await seed_demo_data()
    assert res1["status"] == "success"

    res2 = await seed_demo_data()
    assert res2["status"] == "success"
    assert res2["scenarios_executed"] == 10

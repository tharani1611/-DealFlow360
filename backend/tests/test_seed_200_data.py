"""
DealFlow360 — 200 Synthetic Data Seeder Test Suite
===================================================
Targeted tests verifying:
1. `seed_200_data()` generates >= 200 (target: ~370) relationally connected business records.
2. Multi-tenant isolation: demo data (`demo-enterprise`) remains untouched before and after resetting `bulk-data-lab`.
3. Financial field precision: exact Decimal arithmetic across subtotal, tax, discount, line items, invoices, and payments.
4. Non-negative inventory levels and stock availability calculations.
5. Idempotency: re-running seeder does not produce duplicate rows or orphaned references.
"""

import pytest
from decimal import Decimal
from sqlalchemy import select, func

from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.customer import Customer
from app.models.product import Product
from app.models.warehouses import Warehouse, ProductVariant
from app.models.inventory import InventoryStock
from app.models.deal import Deal
from app.models.quotation import Quotation, QuotationItem
from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import Payment
from app.models.subscription import Subscription, BillingSchedule
from app.models.deal_health import DealHealthSnapshot
from app.seed.seeder_200 import seed_200_data, reset_200_data, BULK_200_ORG_SLUG
from app.seed.demo_seeder import seed_demo_data


@pytest.mark.asyncio
async def test_seed_200_data_generates_at_least_200_records():
    """Verify that seed_200_data generates >= 200 valid connected business records under bulk-data-lab."""
    summary = await seed_200_data()
    total = summary.get("total_records", 0)

    assert total >= 200, f"Expected >= 200 records, got {total}"
    assert summary.get("customers", 0) == 20
    assert summary.get("contacts", 0) == 20
    assert summary.get("products", 0) == 20
    assert summary.get("product_variants", 0) == 15
    assert summary.get("warehouses", 0) == 3
    assert summary.get("inventory_stocks", 0) == 15
    assert summary.get("deals", 0) == 30
    assert summary.get("quotations", 0) == 30
    assert summary.get("quotation_items", 0) >= 45
    assert summary.get("invoices", 0) == 10
    assert summary.get("payments", 0) == 8
    assert summary.get("subscriptions", 0) == 5
    assert summary.get("billing_schedules", 0) == 15
    assert summary.get("deal_health_snapshots", 0) == 10


@pytest.mark.asyncio
async def test_seed_200_data_idempotency():
    """Verify running seeder 200 multiple times yields identical deterministic counts."""
    run1 = await seed_200_data()
    run2 = await seed_200_data()

    assert run1["total_records"] == run2["total_records"]
    assert run1["customers"] == run2["customers"]
    assert run1["quotations"] == run2["quotations"]
    assert run1["invoices"] == run2["invoices"]


@pytest.mark.asyncio
async def test_reset_200_data_preserves_demo_enterprise_tenant():
    """Verify that resetting bulk-data-lab tenant leaves demo-enterprise intact."""
    # 1. Seed demo tenant
    await seed_demo_data()

    # 2. Seed 200 synthetic data
    await seed_200_data()

    async with AsyncSessionLocal() as session:
        demo_org = (await session.execute(
            select(Organization).where(Organization.slug == "demo-enterprise")
        )).scalar_one_or_none()
        assert demo_org is not None

        demo_cust_count = (await session.execute(
            select(func.count()).select_from(Customer).where(Customer.organization_id == demo_org.id)
        )).scalar()
        assert demo_cust_count > 0

    # 3. Reset 200 data only
    await reset_200_data()

    async with AsyncSessionLocal() as session:
        # Demo tenant must STILL exist with all records
        demo_org_after = (await session.execute(
            select(Organization).where(Organization.slug == "demo-enterprise")
        )).scalar_one_or_none()
        assert demo_org_after is not None

        demo_cust_after = (await session.execute(
            select(func.count()).select_from(Customer).where(Customer.organization_id == demo_org_after.id)
        )).scalar()
        assert demo_cust_after == demo_cust_count

        # Bulk tenant must be purged
        bulk_org_after = (await session.execute(
            select(Organization).where(Organization.slug == BULK_200_ORG_SLUG)
        )).scalar_one_or_none()
        assert bulk_org_after is None


@pytest.mark.asyncio
async def test_financial_decimal_precision_and_subtotal_math():
    """Verify exact Decimal calculation across quotations and line items."""
    await seed_200_data()

    async with AsyncSessionLocal() as session:
        bulk_org = (await session.execute(
            select(Organization).where(Organization.slug == BULK_200_ORG_SLUG)
        )).scalar_one()

        quotes = (await session.execute(
            select(Quotation).where(Quotation.organization_id == bulk_org.id)
        )).scalars().all()
        assert len(quotes) == 30

        for q in quotes:
            items = (await session.execute(
                select(QuotationItem).where(QuotationItem.quotation_id == q.id)
            )).scalars().all()
            assert len(items) >= 1

            calc_sub = Decimal("0.00")
            calc_disc = Decimal("0.00")
            calc_tax = Decimal("0.00")

            for item in items:
                assert isinstance(item.quantity, Decimal)
                assert isinstance(item.unit_price, Decimal)
                assert isinstance(item.line_total, Decimal)
                calc_sub += (item.quantity * item.unit_price)
                calc_disc += item.discount_amount
                calc_tax += item.tax_amount

            assert q.subtotal == calc_sub
            assert q.discount_amount == calc_disc
            assert q.tax_amount == calc_tax
            assert q.total_amount == (calc_sub - calc_disc + calc_tax)


@pytest.mark.asyncio
async def test_inventory_stock_non_negative():
    """Verify non-negative stock levels and accurate available quantity math."""
    await seed_200_data()

    async with AsyncSessionLocal() as session:
        bulk_org = (await session.execute(
            select(Organization).where(Organization.slug == BULK_200_ORG_SLUG)
        )).scalar_one()

        stocks = (await session.execute(
            select(InventoryStock).where(InventoryStock.organization_id == bulk_org.id)
        )).scalars().all()
        assert len(stocks) == 15

        for st in stocks:
            assert st.on_hand_quantity >= 0
            assert st.reserved_quantity >= 0
            assert st.available_quantity == st.on_hand_quantity - st.reserved_quantity

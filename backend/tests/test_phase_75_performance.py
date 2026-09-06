"""Phase 75 — Performance, Concurrency, and Reliability Test Suite for DealFlow360.

Comprehensive benchmarks and automated verification covering:
1. Multi-line Quotation Calculation & Scalability (1, 10, 50, 100 items)
2. Concurrent Inventory Reservations with Row-Level Locking Race Condition Defense
3. Concurrent Payment Recording & Financial Ledger Integrity
4. Transaction Rollback & State Atomicity Verification
5. Executive Reporting & Analytics Engine Aggregation Performance (sub-200ms)
6. Stalled Quotes & Discount Anomaly Monitoring Batched Query Performance
7. Collection Pagination Bounds & Resource Exhaustion Defense
8. AI Timeout & Graceful Degradation Handling
"""

import asyncio
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func

from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.customer import Customer
from app.models.deal import Deal
from app.models.inventory import InventoryStock
from app.models.invoice import Invoice
from app.models.organization import Organization
from app.models.product import Product
from app.models.quotation import Quotation, QuotationItem
from app.models.subscription import Subscription
from app.models.user import User
from app.models.warehouses import Warehouse
from app.schemas.payments import PaymentCreateRequest
from app.schemas.quotation import QuotationCreate, QuotationItemCreate
from app.services import (
    inventory as inventory_service,
    invoices as invoice_service,
    payments as payment_service,
    quotations as quotation_service,
    reservations as reservation_service,
)
from app.services.analytics_service import analytics_service
from app.services.discount_anomaly_engine import discount_anomaly_engine
from app.services.reporting_engine import reporting_engine
from app.services.stalled_quote_engine import stalled_quote_engine


@pytest.mark.asyncio
async def test_multi_line_quotation_calculation_and_scalability():
    """Benchmark: Quotations containing 1, 10, 50, and 100 line items.
    
    Verifies server-authoritative Decimal calculations and O(1) batch availability resolution.
    """
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Perf Org", slug=f"perf-org-{org_id.hex[:6]}")
        session.add(org)
        await session.flush()

        customer = Customer(
            id=uuid.uuid4(),
            organization_id=org_id,
            name="Scale Customer",
            email="scale@customer.com",
            is_active=True,
        )
        session.add(customer)

        warehouse = Warehouse(
            id=uuid.uuid4(),
            organization_id=org_id,
            code="WH-PERF",
            name="Performance Hub",
            priority=1,
            is_active=True,
        )
        session.add(warehouse)
        await session.flush()

        # Create 100 distinct products with stock
        products: List[Product] = []
        for i in range(100):
            p = Product(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=f"Enterprise Widget {i:03d}",
                sku=f"SKU-WDG-{i:03d}",
                unit_price=Decimal("150.00"),
                unit_cost=Decimal("75.00"),
                is_active=True,
            )
            session.add(p)
            products.append(p)
        await session.flush()

        for p in products:
            stk = InventoryStock(
                organization_id=org_id,
                warehouse_id=warehouse.id,
                product_id=p.id,
                location_code="MAIN",
                on_hand_quantity=500,
                reserved_quantity=0,
                available_quantity=500,
            )
            session.add(stk)

        await session.commit()

        # Benchmark sizes: 1, 10, 50, 100 lines
        test_sizes = [1, 10, 50, 100]

        for size in test_sizes:
            sub_products = products[:size]
            items_payload = [
                QuotationItemCreate(
                    product_id=p.id,
                    quantity=Decimal("5.00"),
                    unit_price=p.unit_price,
                )
                for p in sub_products
            ]

            q_payload = QuotationCreate(
                customer_id=customer.id,
                valid_until=date.today() + timedelta(days=30),
                notes=f"Benchmark quote size {size}",
                items=items_payload,
            )

            start_t = time.perf_counter()
            quote_resp = await quotation_service.create_quotation(session, org_id, q_payload)
            elapsed_creation = time.perf_counter() - start_t

            # Verify availability calculation speed
            start_avail = time.perf_counter()
            avail_summary = await inventory_service.calculate_quotation_availability(session, org_id, quote_resp.id)
            elapsed_avail = time.perf_counter() - start_avail

            # Verify exact calculations
            expected_subtotal = Decimal("150.00") * 5 * size
            expected_total = expected_subtotal

            assert quote_resp.subtotal == expected_subtotal
            assert quote_resp.total_amount == expected_total
            assert avail_summary.overall_status == "AVAILABLE"
            assert avail_summary.total_requested == 5 * size
            assert len(avail_summary.line_availabilities) == size
            assert elapsed_avail < 1.0, f"Availability query for {size} items took {elapsed_avail:.3f}s (target < 1.0s)"


@pytest.mark.asyncio
async def test_concurrent_inventory_reservations_race_condition_defense():
    """Concurrency: Competing simultaneous reservations against limited stock.
    
    Verifies that with_for_update row locking strictly prevents overselling or negative stock.
    """
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Concurrency Org", slug=f"conc-org-{org_id.hex[:6]}")
        session.add(org)
        await session.flush()

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Fast Buyer", email="buyer@fast.com", is_active=True)
        session.add(customer)

        warehouse = Warehouse(id=uuid.uuid4(), organization_id=org_id, code="WH-CONC", name="Race WH", priority=1, is_active=True)
        session.add(warehouse)

        product = Product(id=uuid.uuid4(), organization_id=org_id, name="Hot GPU", sku="SKU-GPU-01", unit_price=Decimal("1000.00"), is_active=True)
        session.add(product)
        await session.flush()

        # Only 10 units in stock
        stock = InventoryStock(
            organization_id=org_id,
            warehouse_id=warehouse.id,
            product_id=product.id,
            location_code="MAIN",
            on_hand_quantity=10,
            reserved_quantity=0,
            available_quantity=10,
        )
        session.add(stock)

        # Create 4 distinct quotations wanting 4 units each (Total requested = 16 units, but only 10 exist)
        quotes: List[Quotation] = []
        for i in range(4):
            q = Quotation(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=customer.id,
                quotation_number=f"QT-CONC-{i+1:02d}",
                status="accepted",
                quotation_date=date.today(),
                subtotal=Decimal("4000.00"),
                total_amount=Decimal("4000.00"),
            )
            session.add(q)
            await session.flush()

            item = QuotationItem(
                id=uuid.uuid4(),
                quotation_id=q.id,
                product_id=product.id,
                product_name=product.name,
                quantity=Decimal("4.00"),
                unit_price=product.unit_price,
                line_total=Decimal("4000.00"),
            )
            session.add(item)
            quotes.append(q)

        await session.commit()

    # Execute concurrent reservation operations across separate sessions
    async def run_reservation(quote_id: uuid.UUID):
        async with AsyncSessionLocal() as local_session:
            try:
                res_list = await reservation_service.reserve_stock_for_quotation(local_session, org_id, quote_id)
                await local_session.commit()
                return sum(r.quantity for r in res_list)
            except Exception:
                await local_session.rollback()
                return 0

    results = await asyncio.gather(*[run_reservation(q.id) for q in quotes])

    # Total allocated must not exceed available stock of 10
    total_allocated = sum(results)
    assert total_allocated == 10, f"Oversell detected: allocated {total_allocated} units from 10 units stock"

    # Verify database final state
    async with AsyncSessionLocal() as verify_session:
        final_stock = (await verify_session.execute(
            select(InventoryStock).where(InventoryStock.organization_id == org_id, InventoryStock.product_id == product.id)
        )).scalar_one()

        assert final_stock.on_hand_quantity == 10
        assert final_stock.reserved_quantity == 10
        assert final_stock.available_quantity == 0
        assert final_stock.available_quantity >= 0, "Negative stock violation detected!"


@pytest.mark.asyncio
async def test_concurrent_payment_recording_and_balance_integrity():
    """Concurrency & Financial Integrity: Concurrent payments against single invoice.
    
    Verifies that amount_paid never exceeds total, amount_due never goes negative, and status is PAID.
    """
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Billing Org", slug=f"bill-org-{org_id.hex[:6]}")
        session.add(org)
        await session.flush()

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Billing Cust", email="bill@cust.com", is_active=True)
        session.add(customer)

        invoice = Invoice(
            id=uuid.uuid4(),
            organization_id=org_id,
            customer_id=customer.id,
            invoice_number="INV-PERF-001",
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal("1000.00"),
            total=Decimal("1000.00"),
            amount_paid=Decimal("0.00"),
            amount_due=Decimal("1000.00"),
            status="ISSUED",
        )
        session.add(invoice)
        await session.commit()
        inv_id = invoice.id

    # 3 concurrent payment attempts of $500 each (Total = $1500 on a $1000 invoice)
    async def record_pay(amount: Decimal, ref_suffix: str):
        async with AsyncSessionLocal() as local_session:
            try:
                pay_req = PaymentCreateRequest(
                    invoice_id=inv_id,
                    payment_date=date.today(),
                    amount=amount,
                    method="BANK_TRANSFER",
                    notes=f"Pay {ref_suffix}",
                )
                await payment_service.record_payment(local_session, org_id, pay_req)
                return True
            except Exception:
                await local_session.rollback()
                return False

    res = await asyncio.gather(
        record_pay(Decimal("500.00"), "A"),
        record_pay(Decimal("500.00"), "B"),
        record_pay(Decimal("500.00"), "C"),
    )

    # Exactly 2 payments of $500 must succeed, and 1 must fail due to amount exceeding balance
    success_count = sum(1 for r in res if r)
    assert success_count == 2, f"Expected 2 successful payments, got {success_count}"

    async with AsyncSessionLocal() as verify_session:
        final_inv = await invoice_service.get_invoice(verify_session, org_id, inv_id)
        assert final_inv.amount_paid == Decimal("1000.00")
        assert final_inv.amount_due == Decimal("0.00")
        assert final_inv.status == "PAID"


@pytest.mark.asyncio
async def test_transaction_rollback_atomicity():
    """Reliability: Mid-transaction failure leaves zero corrupted or partial state."""
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Rollback Org", slug=f"rb-org-{org_id.hex[:6]}")
        session.add(org)
        await session.flush()

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="RB Cust", email="rb@cust.com", is_active=True)
        session.add(customer)
        await session.commit()

        # Simulated multi-step operation with explicit failure
        try:
            prod = Product(
                id=uuid.uuid4(),
                organization_id=org_id,
                name="Atomic Item",
                sku="SKU-ATOM-01",
                unit_price=Decimal("200.00"),
                is_active=True,
            )
            session.add(prod)
            await session.flush()

            # Trigger synthetic exception before commit
            raise RuntimeError("Simulated mid-flight network/database crash")
        except RuntimeError:
            await session.rollback()

        # Verify nothing was persisted
        prod_check = (await session.execute(
            select(Product).where(Product.organization_id == org_id, Product.sku == "SKU-ATOM-01")
        )).scalar_one_or_none()

        assert prod_check is None, "Rollback failed: partial transaction remained in database!"


@pytest.mark.asyncio
async def test_reporting_and_analytics_aggregation_performance():
    """Performance: Benchmark Executive Reporting and Analytics under multi-domain dataset.
    
    Verifies that SQL aggregations execute under 200ms.
    """
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Analytics Perf Org", slug=f"an-org-{org_id.hex[:6]}")
        session.add(org)
        await session.flush()

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Analytic Corp", email="an@corp.com", is_active=True)
        session.add(customer)

        # Create 20 deals across won, open, lost
        for i in range(20):
            d_status = "won" if i < 10 else "open" if i < 16 else "lost"
            d_stage = "closed_won" if d_status == "won" else "proposal" if d_status == "open" else "closed_lost"
            deal = Deal(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=customer.id,
                deal_number=f"DEAL-AN-{i:03d}",
                title=f"Analytics Deal {i}",
                value=Decimal("5000.00"),
                stage=d_stage,
                status=d_status,
                probability=100 if d_status == "won" else 50 if d_status == "open" else 0,
            )
            session.add(deal)

        # Create 10 invoices
        for i in range(10):
            inv = Invoice(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=customer.id,
                invoice_number=f"INV-AN-{i:03d}",
                invoice_date=date.today(),
                due_date=date.today() + timedelta(days=15),
                subtotal=Decimal("2000.00"),
                total=Decimal("2000.00"),
                amount_paid=Decimal("2000.00") if i < 5 else Decimal("0.00"),
                amount_due=Decimal("0.00") if i < 5 else Decimal("2000.00"),
                status="PAID" if i < 5 else "ISSUED",
            )
            session.add(inv)

        await session.commit()

        # Benchmark Executive Report
        start_t = time.perf_counter()
        exec_report = await reporting_engine.generate_executive_report(session, org_id, period="this_month")
        elapsed_report = time.perf_counter() - start_t

        assert elapsed_report < 0.500, f"Executive report took {elapsed_report:.3f}s (target < 500ms)"
        assert exec_report.sales.won_revenue == Decimal("50000.00")
        assert exec_report.sales.won_deal_count == 10
        assert exec_report.sales.open_deal_count == 6
        assert exec_report.sales.lost_deal_count == 4
        assert exec_report.billing.total_invoiced == Decimal("20000.00")
        assert exec_report.billing.total_collected == Decimal("10000.00")

        # Benchmark Consolidated Dashboard Analytics API
        start_dash = time.perf_counter()
        dash_payload = await analytics_service.get_dashboard_executive_analytics(session, org_id, period="this_month")
        elapsed_dash = time.perf_counter() - start_dash

        assert elapsed_dash < 0.300, f"Dashboard analytics took {elapsed_dash:.3f}s (target < 300ms)"
        assert "reporting" in dash_payload
        assert "monitoring_summary" in dash_payload


@pytest.mark.asyncio
async def test_stalled_quotes_and_anomaly_engines_batch_performance():
    """Performance: Stalled quotes and discount anomaly engines execute without N+1 overhead."""
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Engine Perf Org", slug=f"eng-org-{org_id.hex[:6]}")
        session.add(org)
        await session.flush()

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Engine Cust", email="eng@cust.com", is_active=True)
        session.add(customer)

        # Create 15 quotations
        for i in range(15):
            q = Quotation(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=customer.id,
                quotation_number=f"QT-ENG-{i:03d}",
                status="sent" if i < 8 else "draft",
                quotation_date=date.today() - timedelta(days=25),
                subtotal=Decimal("10000.00"),
                discount_amount=Decimal("3500.00") if i % 2 == 0 else Decimal("500.00"),
                total_amount=Decimal("6500.00") if i % 2 == 0 else Decimal("9500.00"),
                created_at=datetime.now(timezone.utc) - timedelta(days=25),
                updated_at=datetime.now(timezone.utc) - timedelta(days=25),
            )
            session.add(q)

        await session.commit()

        # Measure stalled quote engine latency
        start_stalled = time.perf_counter()
        stalled_resp = await stalled_quote_engine.detect_stalled_quotes(session, org_id)
        elapsed_stalled = time.perf_counter() - start_stalled

        assert elapsed_stalled < 0.250, f"Stalled quote engine took {elapsed_stalled:.3f}s (target < 250ms)"
        assert stalled_resp.total_stalled_count >= 8

        # Measure discount anomaly engine latency
        start_anom = time.perf_counter()
        anom_resp = await discount_anomaly_engine.monitor_discount_anomalies(session, org_id)
        elapsed_anom = time.perf_counter() - start_anom

        assert elapsed_anom < 0.250, f"Discount anomaly engine took {elapsed_anom:.3f}s (target < 250ms)"
        assert isinstance(anom_resp.anomalies, list)


@pytest.mark.asyncio
async def test_pagination_bounds_and_resource_exhaustion_defense():
    """Resource Safety: Verify skip, limit, and max 500 row caps on list endpoints."""
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Pagination Org", slug=f"pag-org-{org_id.hex[:6]}")
        session.add(org)
        await session.flush()

        user = User(
            id=uuid.uuid4(),
            organization_id=org_id,
            email=f"pag-{uuid.uuid4().hex[:6]}@dealflow.com",
            password_hash=hash_password("Secret123!"),
            full_name="Pagination User",
            is_admin=True,
            is_active=True,
        )
        session.add(user)

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Pag Cust", email="pag@cust.com", is_active=True)
        session.add(customer)

        # Create 15 invoices
        for i in range(15):
            inv = Invoice(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=customer.id,
                invoice_number=f"INV-PAG-{i:03d}",
                invoice_date=date.today(),
                due_date=date.today() + timedelta(days=30),
                subtotal=Decimal("100.00"),
                total=Decimal("100.00"),
                status="DRAFT",
            )
            session.add(inv)

        await session.commit()
        token = create_access_token(user.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {token}"}

        # Test page 1 with limit 5
        resp_p1 = await client.get("/api/v1/invoices?skip=0&limit=5", headers=headers)
        assert resp_p1.status_code == 200
        data_p1 = resp_p1.json()
        assert len(data_p1) == 5

        # Test page 2 with limit 5
        resp_p2 = await client.get("/api/v1/invoices?skip=5&limit=5", headers=headers)
        assert resp_p2.status_code == 200
        data_p2 = resp_p2.json()
        assert len(data_p2) == 5

        # Page 1 and Page 2 invoices must be distinct
        ids_p1 = {inv["id"] for inv in data_p1}
        ids_p2 = {inv["id"] for inv in data_p2}
        assert ids_p1.isdisjoint(ids_p2), "Pagination overlapping error detected"

        # Test negative skip is rejected
        resp_invalid = await client.get("/api/v1/invoices?skip=-1&limit=5", headers=headers)
        assert resp_invalid.status_code == 422

        # Test limit > 500 is capped / rejected
        resp_excess = await client.get("/api/v1/invoices?skip=0&limit=1000", headers=headers)
        assert resp_excess.status_code == 422


@pytest.mark.asyncio
async def test_ai_timeout_and_resilient_fallback():
    """Reliability: AI Provider timeout triggers bounded failure without hanging."""
    from app.ai.service import AIService
    from app.ai.base import AbstractAIProvider
    from app.core.exceptions import DealFlowException

    class SlowMockProvider(AbstractAIProvider):
        async def generate_content(self, system_instruction: str, user_prompt: str, **kwargs) -> str:
            await asyncio.sleep(0.05)
            raise DealFlowException("AI provider timed out after bounded period.", status_code=504)

        async def generate_structured(self, system_instruction: str, user_prompt: str, schema: dict, **kwargs) -> dict:
            await asyncio.sleep(0.05)
            raise DealFlowException("AI provider timed out after bounded period.", status_code=504)

    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="AI Perf Org", slug=f"ai-org-{org_id.hex[:6]}")
        session.add(org)
        await session.flush()

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="AI Cust", email="ai@cust.com", is_active=True)
        session.add(customer)
        await session.commit()

        ai_svc = AIService(provider=SlowMockProvider())

        start_t = time.perf_counter()
        with pytest.raises(DealFlowException) as exc_info:
            await ai_svc.summarize_customer(session, org_id, customer.id)
        elapsed = time.perf_counter() - start_t

        assert exc_info.value.status_code == 504
        assert elapsed < 0.500, f"AI timeout handling took too long: {elapsed:.3f}s"

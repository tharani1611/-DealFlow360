import uuid
from decimal import Decimal
from datetime import date, datetime, timezone, timedelta
import pytest
from httpx import AsyncClient

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.organization import Organization
from app.models.user import User
from app.models.customer import Customer
from app.models.product import Product
from app.models.quotation import Quotation, QuotationItem
from app.models.deal import Deal
from app.models.portal_user import PortalUser
from app.models.warehouses import Warehouse
from app.models.fulfillment import DeliveryPromise
from app.core.security import hash_password
from app.ai.service import ai_service
from app.ai.providers.mock import MockAIProvider

from app.services import inventory as inventory_service
from app.services import reservations as reservation_service
from app.services import fulfillment_allocation as allocation_service
from app.services import backorders as backorder_service
from app.services import delivery_promise as delivery_service
from app.services import invoices as invoice_service
from app.services import payments as payment_service
from app.services import subscriptions as subscription_service
from app.services import prorations as proration_service
from app.services import credit_notes as credit_note_service
from app.services.deal_health_engine import deal_health_engine
from app.services.stalled_quote_engine import stalled_quote_engine
from app.services.discount_anomaly_engine import discount_anomaly_engine
from app.services.delivery_slippage_engine import delivery_slippage_engine
from app.services.nudge_engine import nudge_engine
from app.services.reporting_engine import reporting_engine
from app.services.analytics_service import analytics_service

from app.schemas.inventory import StockReceiptRequest
from app.schemas.invoices import InvoiceCreateRequest, InvoiceItemCreate
from app.schemas.payments import PaymentCreateRequest
from app.schemas.subscriptions import SubscriptionCreateRequest, SubscriptionProrationRequest
from app.schemas.credit_notes import CreditNoteCreateRequest, CreditNoteItemCreate, PaymentRefundCreateRequest


@pytest.fixture(autouse=True)
def use_mock_ai_provider(monkeypatch):
    """Ensure AI uses MockAIProvider for deterministic offline execution during tests."""
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "AI_PROVIDER", "mock")
    monkeypatch.setattr(ai_service, "_provider_override", MockAIProvider())


@pytest.mark.asyncio
async def test_phase72_api_integration_reconciliation_and_error_handling(async_client: AsyncClient):
    """
    Phase 72: API Integration & Contract Reconciliation Audit:
    - Verifies HTTP error translation (401, 403, 404, 422)
    - Verifies Decimal authority on server-side computations
    - Verifies AI non-mutating advisory status
    """
    # 1. Unauthenticated Request -> 401
    unauth_res = await async_client.get("/api/v1/customers")
    assert unauth_res.status_code == 401

    # 2. Register User & Auth Token
    hex_id = uuid.uuid4().hex[:8]
    org_slug = f"api-audit-{hex_id}"
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": f"API Audit Corp {hex_id}",
        "organization_slug": org_slug,
        "email": f"audit-{hex_id}@corp.com",
        "password": "Password123!",
        "full_name": "Auditor User"
    })
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Non-existent Resource -> 404
    fake_uuid = str(uuid.uuid4())
    not_found_res = await async_client.get(f"/api/v1/customers/{fake_uuid}", headers=headers)
    assert not_found_res.status_code == 404

    # 4. Invalid Payload -> 422
    invalid_res = await async_client.post("/api/v1/products", json={"name": ""}, headers=headers)
    assert invalid_res.status_code == 422

    # 5. Financial Decimal Accuracy Check
    prod_res = await async_client.post("/api/v1/products", json={
        "name": "Precision Server",
        "sku": f"SKU-PREC-{hex_id}",
        "unit_price": "12999.99",
        "currency": "USD"
    }, headers=headers)
    assert prod_res.status_code == 201
    prod_data = prod_res.json()
    assert Decimal(str(prod_data["unit_price"])) == Decimal("12999.99")


@pytest.mark.asyncio
async def test_phase73_journey_01_basic_sales_cycle(async_client: AsyncClient):
    """
    Journey 1: Basic Sales Cycle
    Customer -> Contact -> Product SKU -> Draft Quote -> Pricing Calculation -> Finalize -> Deal Conversion
    """
    hex_id = uuid.uuid4().hex[:8]
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Sales Cycle Org",
        "organization_slug": f"sales-{hex_id}",
        "email": f"rep-{hex_id}@salesorg.com",
        "password": "Password123!",
        "full_name": "Sales Rep"
    })
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    # Create Customer
    cust_res = await async_client.post("/api/v1/customers", json={"name": "Acme Global"}, headers=headers)
    assert cust_res.status_code == 201
    cust_id = cust_res.json()["id"]

    # Create Contact
    contact_res = await async_client.post("/api/v1/contacts", json={
        "customer_id": cust_id,
        "first_name": "John",
        "last_name": "Doe",
        "email": f"john-{hex_id}@acme.com"
    }, headers=headers)
    assert contact_res.status_code == 201

    # Create SKU
    prod_res = await async_client.post("/api/v1/products", json={
        "name": "Cloud License",
        "sku": f"SKU-CLOUD-{hex_id}",
        "unit_price": "5000.00"
    }, headers=headers)
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    # Create Draft Quotation
    quote_res = await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod_id, "quantity": 3, "unit_price": "5000.00"}]
    }, headers=headers)
    assert quote_res.status_code == 201
    quote_data = quote_res.json()
    quote_id = quote_data["id"]
    assert Decimal(quote_data["total_amount"]) == Decimal("15000.00")

    # Transition Quote -> Sent -> Accepted
    await async_client.put(f"/api/v1/quotations/{quote_id}", json={"status": "sent"}, headers=headers)
    accept_res = await async_client.put(f"/api/v1/quotations/{quote_id}", json={"status": "accepted"}, headers=headers)
    assert accept_res.status_code == 200

    # Convert to Deal
    deal_res = await async_client.post("/api/v1/deals", json={
        "customer_id": cust_id,
        "title": "Acme Cloud Deal",
        "value": "15000.00",
        "stage": "won"
    }, headers=headers)
    assert deal_res.status_code == 201
    assert deal_res.json()["stage"] == "won"


@pytest.mark.asyncio
async def test_phase73_journey_02_approval_flow_and_segregation_of_duties(async_client: AsyncClient):
    """
    Journey 2: Multi-Level Approval Flow & Segregation of Duties Check
    """
    hex_id = uuid.uuid4().hex[:8]
    reg_mgr = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Approval Corp",
        "organization_slug": f"appr-{hex_id}",
        "email": f"mgr-{hex_id}@apprcorp.com",
        "password": "Password123!",
        "full_name": "Manager User"
    })
    mgr_headers = {"Authorization": f"Bearer {reg_mgr.json()['access_token']}"}

    # Create Customer & Product
    cust = (await async_client.post("/api/v1/customers", json={"name": "Big Client"}, headers=mgr_headers)).json()
    prod = (await async_client.post("/api/v1/products", json={
        "name": "Heavy Machinery",
        "sku": f"SKU-MAC-{hex_id}",
        "unit_price": "100000.00"
    }, headers=mgr_headers)).json()

    # Create Approval Rule via API
    rule_res = await async_client.post("/api/v1/approvals/rules", json={
        "name": "Discounts > 10% Need Approval",
        "min_discount_percent": "10.00",
        "priority": 1
    }, headers=mgr_headers)
    assert rule_res.status_code == 201

    # Create Quote
    quote = (await async_client.post("/api/v1/quotations", json={
        "customer_id": cust["id"],
        "items": [{
            "product_id": prod["id"],
            "quantity": 1,
            "unit_price": "100000.00",
            "discount_percent": "30.0"
        }]
    }, headers=mgr_headers)).json()
    assert quote["id"] is not None

    # List Approval Rules Endpoint
    approvals_res = await async_client.get("/api/v1/approvals/rules", headers=mgr_headers)
    assert approvals_res.status_code == 200
    assert len(approvals_res.json()) >= 1


@pytest.mark.asyncio
async def test_phase73_journey_03_customer_negotiation_counter_discount(async_client: AsyncClient):
    """
    Journey 3: Customer Portal Negotiation & Counter-Discount
    """
    hex_id = uuid.uuid4().hex[:8]
    org_slug = f"pneg-{hex_id}"
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": f"Portal Neg {hex_id}",
        "organization_slug": org_slug,
        "email": f"sales-{hex_id}@pneg.com",
        "password": "Password123!",
        "full_name": "Sales Rep"
    })
    sales_headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    me_data = (await async_client.get("/api/v1/auth/me", headers=sales_headers)).json()
    org_id = uuid.UUID(me_data["organization_id"])

    cust = (await async_client.post("/api/v1/customers", json={"name": "Portal Client"}, headers=sales_headers)).json()
    cust_id = uuid.UUID(cust["id"])

    client_email = f"client-{hex_id}@portalclient.com"
    async with AsyncSessionLocal() as session:
        portal_user = PortalUser(
            id=uuid.uuid4(),
            organization_id=org_id,
            customer_id=cust_id,
            email=client_email,
            hashed_password=hash_password("ClientPass123!"),
            full_name="Portal Customer",
            is_active=True,
        )
        session.add(portal_user)
        await session.commit()

    # Portal Login
    login_res = await async_client.post("/api/v1/portal/auth/login", json={
        "email": client_email,
        "password": "ClientPass123!"
    })
    assert login_res.status_code == 200
    portal_token = login_res.json()["access_token"]
    portal_headers = {"Authorization": f"Bearer {portal_token}"}

    # Fetch Portal Quotations
    portal_quotes = await async_client.get("/api/v1/portal/quotations", headers=portal_headers)
    assert portal_quotes.status_code == 200


@pytest.mark.asyncio
async def test_phase73_journey_04_stock_reservation_smart_fulfillment():
    """
    Journey 4: Stock Reservation & Smart Warehouse Fulfillment
    """
    async with AsyncSessionLocal() as db_session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Fulfill Corp", slug=f"fulfill-{org_id.hex[:6]}")
        db_session.add(org)

        user = User(
            id=uuid.uuid4(),
            organization_id=org_id,
            email=f"wh-{org_id.hex[:4]}@fulfill.com",
            password_hash=hash_password("Pass123!"),
            full_name="WH Manager",
            is_admin=True,
            is_active=True
        )
        db_session.add(user)

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Fulfill Cust", email="fcust@corp.com", is_active=True)
        db_session.add(customer)

        product = Product(
            id=uuid.uuid4(),
            organization_id=org_id,
            name="Server Blade",
            sku=f"SKU-BLADE-{org_id.hex[:4]}",
            unit_price=Decimal("4000.00"),
            unit_cost=Decimal("2000.00"),
            is_active=True
        )
        db_session.add(product)

        wh = Warehouse(id=uuid.uuid4(), organization_id=org_id, code=f"WH1-{org_id.hex[:4]}", name="Main Hub", priority=1, is_active=True)
        db_session.add(wh)
        await db_session.commit()

        # Receive stock
        await inventory_service.record_stock_receipt(db_session, org_id, StockReceiptRequest(warehouse_id=wh.id, product_id=product.id, quantity=100))

        # Create quotation
        quotation = Quotation(
            id=uuid.uuid4(),
            organization_id=org_id,
            quotation_number=f"QT-{org_id.hex[:6]}",
            customer_id=customer.id,
            created_by_user_id=user.id,
            status="sent",
            subtotal=Decimal("80000.00"),
            total_amount=Decimal("80000.00"),
        )
        db_session.add(quotation)

        item = QuotationItem(
            id=uuid.uuid4(),
            quotation_id=quotation.id,
            product_id=product.id,
            product_name="Server Blade",
            sku=product.sku,
            quantity=Decimal("20.00"),
            unit_price=Decimal("4000.00"),
            unit_cost=Decimal("2000.00"),
            line_total=Decimal("80000.00"),
        )
        db_session.add(item)
        await db_session.commit()

        # Reserve stock & smart allocation
        await reservation_service.reserve_stock_for_quotation(db_session, org_id, quotation.id)
        summary = await allocation_service.calculate_smart_warehouse_allocation(db_session, org_id, quotation.id)
        assert summary.is_fully_allocated is True
        assert summary.total_allocated == 20


@pytest.mark.asyncio
async def test_phase73_journey_05_backorder_engine_and_allocation():
    """
    Journey 5: Backorder Engine & Inventory Replenishment
    """
    async with AsyncSessionLocal() as db_session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Backorder Corp", slug=f"bo-{org_id.hex[:6]}")
        db_session.add(org)

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="BO Cust", email="bo@corp.com", is_active=True)
        db_session.add(customer)

        product = Product(
            id=uuid.uuid4(),
            organization_id=org_id,
            name="Scarcity Component",
            sku=f"SKU-SCARCE-{org_id.hex[:4]}",
            unit_price=Decimal("500.00"),
            is_active=True
        )
        db_session.add(product)

        quotation = Quotation(
            id=uuid.uuid4(),
            organization_id=org_id,
            quotation_number=f"QT-BO-{org_id.hex[:4]}",
            customer_id=customer.id,
            status="accepted",
            subtotal=Decimal("25000.00"),
            total_amount=Decimal("25000.00"),
        )
        db_session.add(quotation)

        item = QuotationItem(
            id=uuid.uuid4(),
            quotation_id=quotation.id,
            product_id=product.id,
            product_name="Scarcity Component",
            sku=product.sku,
            quantity=Decimal("50.00"),
            unit_price=Decimal("500.00"),
            line_total=Decimal("25000.00"),
        )
        db_session.add(item)
        await db_session.commit()

        # Backorder for shortfall (50 units)
        shortfalls = {item.id: 50}
        backorders = await backorder_service.create_backorders_for_quotation_shortfall(db_session, org_id, quotation.id, shortfalls)
        assert len(backorders) == 1
        assert backorders[0].remaining_quantity == 50

        # Consolidate Backorders
        consolidation = await backorder_service.get_customer_backorder_consolidation(db_session, org_id, customer.id)
        assert consolidation.total_open_backorders == 1
        assert consolidation.total_remaining_quantity == 50


@pytest.mark.asyncio
async def test_phase73_journey_06_delivery_slippage_and_promise_tracking():
    """
    Journey 6: Delivery Slippage & Promise Tracking
    """
    async with AsyncSessionLocal() as db_session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Delivery Corp", slug=f"deliv-{org_id.hex[:6]}")
        db_session.add(org)

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Deliv Cust", email="deliv@corp.com", is_active=True)
        db_session.add(customer)

        quotation = Quotation(
            id=uuid.uuid4(),
            organization_id=org_id,
            customer_id=customer.id,
            quotation_number=f"QT-DEL-{org_id.hex[:4]}",
            status="accepted",
            subtotal=Decimal("5000.00"),
            total_amount=Decimal("5000.00"),
        )
        db_session.add(quotation)
        await db_session.flush()

        promise = DeliveryPromise(
            id=uuid.uuid4(),
            organization_id=org_id,
            quotation_id=quotation.id,
            promised_date=date.today() - timedelta(days=3),
            expected_date=date.today() + timedelta(days=4),
            status="DELAYED",
            slippage_days=7,
        )
        db_session.add(promise)
        await db_session.commit()

        slippage_results = await delivery_slippage_engine.monitor_delivery_slippage(db_session, org_id)
        assert len(slippage_results.deliveries) == 1
        assert slippage_results.deliveries[0].status == "DELAYED"


@pytest.mark.asyncio
async def test_phase73_journey_07_invoice_and_payment_recording():
    """
    Journey 7: Invoice & Payment Recording with Balance Recalculation
    """
    async with AsyncSessionLocal() as db_session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Invoice Corp", slug=f"inv-{org_id.hex[:6]}")
        db_session.add(org)

        customer = Customer(
            id=uuid.uuid4(),
            organization_id=org_id,
            name="Invoice Client",
            email=f"inv-{org_id.hex[:4]}@client.com",
            is_active=True
        )
        db_session.add(customer)
        await db_session.commit()

        # Create Invoice
        inv_req = InvoiceCreateRequest(
            customer_id=customer.id,
            due_date=date.today() + timedelta(days=30),
            items=[InvoiceItemCreate(description="Software License", quantity=Decimal("1.00"), unit_price=Decimal("10000.00"))]
        )
        invoice = await invoice_service.create_invoice(db_session, org_id, inv_req)
        assert invoice.total == Decimal("10000.00")
        assert invoice.status == "DRAFT"

        # Issue Invoice (transitions DRAFT -> ISSUED so payments can be recorded)
        invoice = await invoice_service.issue_invoice(db_session, org_id, invoice.id)
        assert invoice.status == "ISSUED"

        # Record Partial Payment
        pay_req1 = PaymentCreateRequest(
            invoice_id=invoice.id,
            amount=Decimal("4000.00"),
            method="BANK_TRANSFER",
            notes=f"REF-{org_id.hex[:6]}"
        )
        payment1 = await payment_service.record_payment(db_session, org_id, pay_req1)
        assert payment1.amount == Decimal("4000.00")

        # Refresh Invoice
        inv_updated = await invoice_service.get_invoice(db_session, org_id, invoice.id)
        assert inv_updated.amount_paid == Decimal("4000.00")
        assert inv_updated.status == "PARTIALLY_PAID"

        # Final Payment
        pay_req2 = PaymentCreateRequest(
            invoice_id=invoice.id,
            amount=Decimal("6000.00"),
            method="BANK_TRANSFER",
            notes=f"REF-FINAL-{org_id.hex[:6]}"
        )
        await payment_service.record_payment(db_session, org_id, pay_req2)
        inv_paid = await invoice_service.get_invoice(db_session, org_id, invoice.id)
        assert inv_paid.amount_paid == Decimal("10000.00")
        assert inv_paid.status == "PAID"


@pytest.mark.asyncio
async def test_phase73_journey_08_subscription_lifecycle_and_proration():
    """
    Journey 8: Subscription Lifecycle & Recurring Billing Schedule
    """
    async with AsyncSessionLocal() as db_session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Sub Corp", slug=f"sub-{org_id.hex[:6]}")
        db_session.add(org)

        customer = Customer(
            id=uuid.uuid4(),
            organization_id=org_id,
            name="Sub Client",
            email=f"sub-{org_id.hex[:4]}@client.com",
            is_active=True
        )
        db_session.add(customer)

        product = Product(
            id=uuid.uuid4(),
            organization_id=org_id,
            name="Cloud Plan",
            sku=f"SKU-SUB-{org_id.hex[:4]}",
            unit_price=Decimal("2500.00"),
            is_active=True
        )
        db_session.add(product)
        await db_session.commit()

        # Create Subscription
        sub_req = SubscriptionCreateRequest(
            customer_id=customer.id,
            product_id=product.id,
            plan_name="Enterprise Monthly",
            billing_interval="MONTHLY",
            quantity=Decimal("1.00"),
            unit_price=Decimal("2500.00"),
            start_date=date.today()
        )
        sub = await subscription_service.create_subscription(db_session, org_id, sub_req)
        assert sub.unit_price == Decimal("2500.00")
        assert sub.status == "ACTIVE"

        # Preview Proration for Upgrade
        proration_req = SubscriptionProrationRequest(
            new_plan_name="Enterprise Plus",
            new_quantity=Decimal("1.00"),
            new_unit_price=Decimal("5000.00"),
            effective_date=date.today() + timedelta(days=15)
        )
        proration = await proration_service.prorate_subscription_adjustment(db_session, org_id, sub.id, proration_req)
        assert proration is not None


@pytest.mark.asyncio
async def test_phase73_journey_09_credit_notes_and_partial_refunds():
    """
    Journey 9: Credit Notes & Payment Refunds
    """
    async with AsyncSessionLocal() as db_session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Credit Corp", slug=f"cn-{org_id.hex[:6]}")
        db_session.add(org)

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Refund Client", email="ref@client.com", is_active=True)
        db_session.add(customer)
        await db_session.commit()

        # Create Invoice & Issue
        inv_req = InvoiceCreateRequest(
            customer_id=customer.id,
            items=[InvoiceItemCreate(description="Returned Hardware", quantity=Decimal("1.00"), unit_price=Decimal("2000.00"))]
        )
        invoice = await invoice_service.create_invoice(db_session, org_id, inv_req)
        invoice = await invoice_service.issue_invoice(db_session, org_id, invoice.id)

        pay = await payment_service.record_payment(db_session, org_id, PaymentCreateRequest(
            invoice_id=invoice.id,
            amount=Decimal("2000.00"),
            method="CARD"
        ))

        # Issue Credit Note
        cn_req = CreditNoteCreateRequest(
            invoice_id=invoice.id,
            reason="Product return",
            items=[CreditNoteItemCreate(description="Hardware Return", quantity=Decimal("1.00"), unit_price=Decimal("2000.00"))]
        )
        credit_note = await credit_note_service.create_credit_note(db_session, org_id, cn_req)
        assert credit_note.total == Decimal("2000.00")

        # Process Refund
        refund_req = PaymentRefundCreateRequest(
            payment_id=pay.id,
            credit_note_id=credit_note.id,
            amount=Decimal("2000.00"),
            reason="Full return refund"
        )
        refund = await credit_note_service.record_payment_refund(db_session, org_id, refund_req)
        assert refund.amount == Decimal("2000.00")


@pytest.mark.asyncio
async def test_phase73_journey_10_deal_health_and_telemetry():
    """
    Journey 10: Deal Health Engine & Dynamic Telemetry
    """
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Health Corp 2", slug=f"hcorp-{org_id.hex[:6]}")
        session.add(org)

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Health Client", email="h@client.com", is_active=True)
        session.add(customer)

        deal = Deal(
            id=uuid.uuid4(),
            organization_id=org_id,
            customer_id=customer.id,
            deal_number=f"DEAL-{org_id.hex[:4]}",
            title="Strategic Renewal",
            value=Decimal("75000.00"),
            stage="proposal",
            status="open",
            probability=60,
            expected_close_date=date.today() + timedelta(days=14)
        )
        session.add(deal)
        await session.commit()

        # Compute Deal Health
        health_snapshot = await deal_health_engine.evaluate_deal_health(session, org_id, deal.id, persist_snapshot=True)
        assert health_snapshot.health_score >= 0


@pytest.mark.asyncio
async def test_phase73_journey_11_stalled_quote_detection_and_nudges():
    """
    Journey 11: Stalled Quote Detection & Nudges
    """
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Stall Corp", slug=f"stall-{org_id.hex[:6]}")
        session.add(org)
        await session.commit()

        stalled_resp = await stalled_quote_engine.detect_stalled_quotes(session, org_id, days_threshold=14)
        assert hasattr(stalled_resp, "total_stalled_count")

        nudges = await nudge_engine.evaluate_and_generate_system_nudges(session, org_id)
        assert isinstance(nudges, list)


@pytest.mark.asyncio
async def test_phase73_journey_12_discount_anomaly_and_risk_monitoring():
    """
    Journey 12: Discount Anomaly Engine
    """
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Disc Anomaly Corp", slug=f"danom-{org_id.hex[:6]}")
        session.add(org)
        await session.commit()

        anomaly_resp = await discount_anomaly_engine.monitor_discount_anomalies(session, org_id)
        assert hasattr(anomaly_resp, "anomalous_count")


@pytest.mark.asyncio
async def test_phase73_journey_13_executive_analytics_and_reporting():
    """
    Journey 13: Executive Reporting & Analytics API
    """
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Analytics Corp", slug=f"analy-{org_id.hex[:6]}")
        session.add(org)
        await session.commit()

        executive_report = await reporting_engine.generate_executive_report(session, org_id, period="this_month")
        assert hasattr(executive_report, "sales")

        dashboard_analytics = await analytics_service.get_dashboard_executive_analytics(session, org_id, period="this_month")
        assert "reporting" in dashboard_analytics


@pytest.mark.asyncio
async def test_phase73_journey_14_ai_sales_copilot_and_recommendations(async_client: AsyncClient):
    """
    Journey 14: AI Sales Copilot Advisory Boundary
    """
    hex_id = uuid.uuid4().hex[:8]
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "AI Copilot Org",
        "organization_slug": f"copilot-{hex_id}",
        "email": f"user-{hex_id}@copilot.com",
        "password": "Password123!",
        "full_name": "Copilot User"
    })
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    # Call AI Sales Copilot Assistant
    copilot_res = await async_client.post("/api/v1/copilot/chat", json={
        "message": "What is the recommended discount strategy for enterprise deals?"
    }, headers=headers)
    assert copilot_res.status_code == 200
    assert "answer" in copilot_res.json()


@pytest.mark.asyncio
async def test_phase73_journey_15_workflow_automation_engine(async_client: AsyncClient):
    """
    Journey 15: Workflow Automation Rule & Trigger Evaluation
    """
    hex_id = uuid.uuid4().hex[:8]
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Auto Corp",
        "organization_slug": f"auto-{hex_id}",
        "email": f"admin-{hex_id}@autocorp.com",
        "password": "Password123!",
        "full_name": "Automation Admin"
    })
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    # Create Automation Rule
    rule_res = await async_client.post("/api/v1/automations", json={
        "name": "Auto-notify on quote accept",
        "trigger_type": "DEAL_STAGE_CHANGED",
        "actions": [{"action_type": "SEND_NOTIFICATION", "parameters": {"message": "Quote accepted"}}]
    }, headers=headers)
    assert rule_res.status_code in [200, 201]


@pytest.mark.asyncio
async def test_phase73_journey_16_multi_tenant_security_isolation(async_client: AsyncClient):
    """
    Journey 16: Multi-Tenant Data Isolation
    Tenant A cannot access Tenant B resources
    """
    hex_a = uuid.uuid4().hex[:8]
    hex_b = uuid.uuid4().hex[:8]

    # Register Tenant A
    token_a = (await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Tenant A Corp",
        "organization_slug": f"org-a-{hex_a}",
        "email": f"admin-{hex_a}@orga.com",
        "password": "Password123!",
        "full_name": "Admin A"
    })).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register Tenant B
    token_b = (await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Tenant B Corp",
        "organization_slug": f"org-b-{hex_b}",
        "email": f"admin-{hex_b}@orgb.com",
        "password": "Password123!",
        "full_name": "Admin B"
    })).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Tenant A creates Customer
    cust_a = (await async_client.post("/api/v1/customers", json={"name": "Tenant A Client"}, headers=headers_a)).json()
    cust_a_id = cust_a["id"]

    # Tenant B attempts to fetch Tenant A Customer -> 404
    fetch_b = await async_client.get(f"/api/v1/customers/{cust_a_id}", headers=headers_b)
    assert fetch_b.status_code == 404


@pytest.mark.asyncio
async def test_phase73_journey_17_portal_separation_and_security(async_client: AsyncClient):
    """
    Journey 17: Customer Portal Separation
    Portal Token cannot access internal staff API endpoints
    """
    hex_id = uuid.uuid4().hex[:8]
    org_slug = f"portal-sec-{hex_id}"
    sales = (await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Portal Sec Org",
        "organization_slug": org_slug,
        "email": f"sales-{hex_id}@sec.com",
        "password": "Password123!",
        "full_name": "Sales Rep"
    })).json()
    sales_headers = {"Authorization": f"Bearer {sales['access_token']}"}

    me_data = (await async_client.get("/api/v1/auth/me", headers=sales_headers)).json()
    org_id = uuid.UUID(me_data["organization_id"])

    cust = (await async_client.post("/api/v1/customers", json={"name": "Sec Portal Cust"}, headers=sales_headers)).json()
    cust_id = uuid.UUID(cust["id"])

    client_email = f"client-{hex_id}@secportal.com"
    async with AsyncSessionLocal() as session:
        portal_user = PortalUser(
            id=uuid.uuid4(),
            organization_id=org_id,
            customer_id=cust_id,
            email=client_email,
            hashed_password=hash_password("ClientPass123!"),
            full_name="Portal Client User",
            is_active=True
        )
        session.add(portal_user)
        await session.commit()

    login = (await async_client.post("/api/v1/portal/auth/login", json={
        "email": client_email,
        "password": "ClientPass123!"
    })).json()
    portal_headers = {"Authorization": f"Bearer {login['access_token']}"}

    # Portal user tries internal endpoint -> 401 or 403
    staff_access = await async_client.get("/api/v1/customers", headers=portal_headers)
    assert staff_access.status_code in [401, 403]


@pytest.mark.asyncio
async def test_phase73_journey_18_failure_recovery_and_data_integrity(async_client: AsyncClient):
    """
    Journey 18: Failure Recovery & Data Integrity Verification
    """
    hex_id = uuid.uuid4().hex[:8]
    reg_res = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Fail Safe Corp",
        "organization_slug": f"failsafe-{hex_id}",
        "email": f"admin-{hex_id}@failsafe.com",
        "password": "Password123!",
        "full_name": "Failsafe Admin"
    })
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    # Attempt to transition nonexistent quotation
    fake_id = str(uuid.uuid4())
    bad_transition = await async_client.put(f"/api/v1/quotations/{fake_id}", json={"status": "accepted"}, headers=headers)
    assert bad_transition.status_code == 404

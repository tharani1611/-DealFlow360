import uuid
import pytest
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.customer import Customer
from app.models.product import Product
from app.models.deal import Deal
from app.models.activity import Activity
from app.models.quotation import Quotation, QuotationItem
from app.models.fulfillment import DeliveryPromise
from app.models.invoice import Invoice, InvoiceItem
from app.models.subscription import Subscription, BillingSchedule

from app.services.deal_health_engine import deal_health_engine
from app.services.stalled_quote_engine import stalled_quote_engine
from app.services.discount_anomaly_engine import discount_anomaly_engine
from app.services.delivery_slippage_engine import delivery_slippage_engine
from app.services.nudge_engine import nudge_engine
from app.services.reporting_engine import reporting_engine
from app.services.analytics_service import analytics_service


@pytest.mark.asyncio
async def test_phase_53_deal_health_engine():
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Health Corp", slug=f"health-corp-{org_id.hex[:6]}")
        session.add(org)

        user = User(
            id=uuid.uuid4(),
            organization_id=org_id,
            email="rep@healthcorp.com",
            full_name="Sales Rep",
            password_hash="fakehash",
            is_active=True,
        )
        session.add(user)

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Health Cust", email="hcust@corp.com", is_active=True)
        session.add(customer)

        deal = Deal(
            id=uuid.uuid4(),
            organization_id=org_id,
            customer_id=customer.id,
            deal_number="DEAL-H-001",
            title="Enterprise Cloud Deal",
            value=Decimal("50000.00"),
            stage="proposal",
            status="open",
            probability=70,
            expected_close_date=date.today() + timedelta(days=10),
        )
        session.add(deal)

        activity = Activity(
            id=uuid.uuid4(),
            organization_id=org_id,
            deal_id=deal.id,
            created_by_user_id=user.id,
            activity_type="call",
            title="Follow-up Call",
            status="completed",
        )
        session.add(activity)
        await session.commit()

        # Evaluate Deal Health
        health = await deal_health_engine.evaluate_deal_health(session, org_id, deal.id, persist_snapshot=True)
        assert health.deal_id == deal.id
        assert health.health_score >= 60
        assert health.health_status in ["HEALTHY", "ATTENTION"]
        assert len(health.positive_drivers) > 0


@pytest.mark.asyncio
async def test_phase_54_stalled_quote_detection():
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Stall Corp", slug=f"stall-corp-{org_id.hex[:6]}")
        session.add(org)

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Stall Cust", email="scust@corp.com", is_active=True)
        session.add(customer)

        # Stalled Sent Quotation (sent 20 days ago)
        old_date = datetime.now(timezone.utc) - timedelta(days=20)
        stalled_q = Quotation(
            id=uuid.uuid4(),
            organization_id=org_id,
            customer_id=customer.id,
            quotation_number="QT-STALL-01",
            status="sent",
            quotation_date=date.today() - timedelta(days=20),
            subtotal=Decimal("1000.00"),
            discount_amount=Decimal("50.00"),
            total_amount=Decimal("950.00"),
            created_at=old_date,
            updated_at=old_date,
        )
        session.add(stalled_q)

        # Active Accepted Quotation (should NOT be detected as stalled)
        accepted_q = Quotation(
            id=uuid.uuid4(),
            organization_id=org_id,
            customer_id=customer.id,
            quotation_number="QT-ACTIVE-01",
            status="accepted",
            quotation_date=date.today() - timedelta(days=25),
            subtotal=Decimal("2000.00"),
            discount_amount=Decimal("100.00"),
            total_amount=Decimal("1900.00"),
            created_at=old_date,
            updated_at=old_date,
        )
        session.add(accepted_q)
        await session.commit()

        stalled_resp = await stalled_quote_engine.detect_stalled_quotes(session, org_id, days_threshold=14)
        assert stalled_resp.total_stalled_count == 1
        assert stalled_resp.stalled_quotes[0].quotation_number == "QT-STALL-01"
        assert stalled_resp.stalled_quotes[0].days_inactive >= 20


@pytest.mark.asyncio
async def test_phase_55_discount_anomaly_monitoring():
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Disc Corp", slug=f"disc-corp-{org_id.hex[:6]}")
        session.add(org)

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Disc Cust", email="dcust@corp.com", is_active=True)
        session.add(customer)

        # Historical Accepted Quote with 5% discount
        past_q = Quotation(
            id=uuid.uuid4(),
            organization_id=org_id,
            customer_id=customer.id,
            quotation_number="QT-PAST-01",
            status="accepted",
            quotation_date=date.today() - timedelta(days=60),
            subtotal=Decimal("10000.00"),
            discount_amount=Decimal("500.00"),  # 5%
            total_amount=Decimal("9500.00"),
        )
        session.add(past_q)

        # Active Sent Quote with 35% discount (High Anomaly Variance +30%)
        anomalous_q = Quotation(
            id=uuid.uuid4(),
            organization_id=org_id,
            customer_id=customer.id,
            quotation_number="QT-ANOMALOUS-01",
            status="sent",
            quotation_date=date.today(),
            subtotal=Decimal("10000.00"),
            discount_amount=Decimal("3500.00"),  # 35%
            total_amount=Decimal("6500.00"),
        )
        session.add(anomalous_q)
        await session.commit()

        anomaly_resp = await discount_anomaly_engine.monitor_discount_anomalies(session, org_id)
        assert anomaly_resp.anomalous_count >= 1
        top_anom = anomaly_resp.anomalies[0]
        assert top_anom.quotation_number == "QT-ANOMALOUS-01"
        assert top_anom.blended_discount_percent == Decimal("35.00")
        assert top_anom.severity in ["ANOMALOUS", "CRITICAL"]


@pytest.mark.asyncio
async def test_phase_56_delivery_slippage_monitoring():
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Delivery Corp", slug=f"deliv-corp-{org_id.hex[:6]}")
        session.add(org)

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Deliv Cust", email="deliv@corp.com", is_active=True)
        session.add(customer)

        quotation = Quotation(
            id=uuid.uuid4(),
            organization_id=org_id,
            customer_id=customer.id,
            quotation_number="QT-DELIV-01",
            status="accepted",
            quotation_date=date.today(),
            subtotal=Decimal("5000.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("5000.00"),
        )
        session.add(quotation)
        await session.flush()

        promise = DeliveryPromise(
            id=uuid.uuid4(),
            organization_id=org_id,
            quotation_id=quotation.id,
            promised_date=date.today() - timedelta(days=2),
            expected_date=date.today() + timedelta(days=5),
            status="DELAYED",
            slippage_days=7,
        )
        session.add(promise)
        await session.commit()

        deliv_resp = await delivery_slippage_engine.monitor_delivery_slippage(session, org_id)
        assert len(deliv_resp.deliveries) == 1
        assert deliv_resp.deliveries[0].slippage_days == 7
        assert deliv_resp.deliveries[0].status == "DELAYED"


@pytest.mark.asyncio
async def test_phase_57_nudges_and_escalations():
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Nudge Corp", slug=f"nudge-corp-{org_id.hex[:6]}")
        session.add(org)

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Nudge Cust", email="nudge@corp.com", is_active=True)
        session.add(customer)

        stalled_q = Quotation(
            id=uuid.uuid4(),
            organization_id=org_id,
            customer_id=customer.id,
            quotation_number="QT-NUDGE-01",
            status="sent",
            quotation_date=date.today() - timedelta(days=20),
            subtotal=Decimal("1000.00"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("1000.00"),
            created_at=datetime.now(timezone.utc) - timedelta(days=20),
            updated_at=datetime.now(timezone.utc) - timedelta(days=20),
        )
        session.add(stalled_q)
        await session.commit()

        # 1. Generate system nudges
        created_nudges = await nudge_engine.evaluate_and_generate_system_nudges(session, org_id)
        assert len(created_nudges) >= 1

        target_nudge = created_nudges[0]
        assert target_nudge.status == "OPEN"

        # 2. Idempotency test (re-evaluate nudges, deduplication prevents duplicate)
        re_created = await nudge_engine.evaluate_and_generate_system_nudges(session, org_id)
        assert len(re_created) == 0

        # 3. Status transition: ACKNOWLEDGED -> COMPLETED
        ack_nudge = await nudge_engine.transition_nudge_status(session, org_id, target_nudge.id, "ACKNOWLEDGED", notes="Reviewed by rep")
        assert ack_nudge.status == "ACKNOWLEDGED"

        comp_nudge = await nudge_engine.transition_nudge_status(session, org_id, target_nudge.id, "COMPLETED", notes="Followed up with client")
        assert comp_nudge.status == "COMPLETED"


@pytest.mark.asyncio
async def test_phase_58_59_reporting_and_analytics_engine():
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Report Corp", slug=f"report-corp-{org_id.hex[:6]}")
        session.add(org)

        customer = Customer(id=uuid.uuid4(), organization_id=org_id, name="Report Cust", email="rcust@corp.com", is_active=True)
        session.add(customer)

        deal = Deal(
            id=uuid.uuid4(),
            organization_id=org_id,
            customer_id=customer.id,
            deal_number="DEAL-R-001",
            title="Reporting Test Deal",
            value=Decimal("10000.00"),
            stage="negotiation",
            status="won",
            probability=100,
        )
        session.add(deal)

        product = Product(
            id=uuid.uuid4(),
            organization_id=org_id,
            name="Enterprise Software",
            sku="SKU-ENT-01",
            unit_price=Decimal("100.00"),
            is_active=True,
        )
        session.add(product)

        sub = Subscription(
            id=uuid.uuid4(),
            organization_id=org_id,
            subscription_number="SUB-R-001",
            customer_id=customer.id,
            product_id=product.id,
            plan_name="Enterprise Plan",
            quantity=Decimal("10.00"),
            unit_price=Decimal("100.00"),
            billing_interval="MONTHLY",
            start_date=date.today(),
            next_billing_date=date.today() + timedelta(days=30),
            status="ACTIVE",
        )
        session.add(sub)
        await session.commit()

        # Executive Report Summary
        report = await reporting_engine.generate_executive_report(session, org_id, period="this_month")
        assert report.sales.won_revenue == Decimal("10000.00")
        assert report.subscriptions.monthly_recurring_revenue == Decimal("1000.00")
        assert report.subscriptions.annual_recurring_revenue == Decimal("12000.00")

        # Dashboard Analytics API Payload
        analytics = await analytics_service.get_dashboard_executive_analytics(session, org_id, period="this_month")
        assert "reporting" in analytics
        assert "monitoring_summary" in analytics

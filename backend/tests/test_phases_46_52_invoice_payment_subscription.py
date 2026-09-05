import uuid
from decimal import Decimal
from datetime import date, timedelta
import pytest
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.customer import Customer
from app.models.product import Product
from app.models.quotation import Quotation, QuotationItem
from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import Payment
from app.models.subscription import Subscription, BillingSchedule, SubscriptionProration, SubscriptionCancellation
from app.models.credit_note import CreditNote, CreditNoteItem, PaymentRefund
from app.core.security import hash_password
from app.services import invoices as invoice_service
from app.services import payments as payment_service
from app.services import subscriptions as subscription_service
from app.services import billing_schedules as schedule_service
from app.services import prorations as proration_service
from app.services import cancellations as cancellation_service
from app.services import credit_notes as credit_note_service
from app.schemas.invoices import InvoiceCreateRequest, InvoiceItemCreate
from app.schemas.payments import PaymentCreateRequest
from app.schemas.subscriptions import (
    SubscriptionCreateRequest,
    SubscriptionProrationRequest,
    SubscriptionCancellationRequest,
)
from app.schemas.credit_notes import CreditNoteCreateRequest, CreditNoteItemCreate, PaymentRefundCreateRequest
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


@pytest.mark.asyncio
async def test_phase_46_invoice_creation_and_calculation():
    async with AsyncSessionLocal() as db_session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Billing Corp 1", slug=f"bill-corp-{org_id.hex[:6]}")
        db_session.add(org)

        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            organization_id=org_id,
            email=f"finance-{user_id.hex[:6]}@billcorp.com",
            password_hash=hash_password("Password123!"),
            full_name="Finance Manager",
            is_admin=True,
            is_active=True,
        )
        db_session.add(user)

        cust_id = uuid.uuid4()
        customer = Customer(
            id=cust_id,
            organization_id=org_id,
            name="Acme Global Inc",
            email=f"acme-{org_id.hex[:4]}@global.com",
            is_active=True,
        )
        db_session.add(customer)
        await db_session.commit()

        # 1. Manual Invoice creation with Decimal calculation
        req = InvoiceCreateRequest(
            customer_id=cust_id,
            currency="USD",
            items=[
                InvoiceItemCreate(
                    description="Cloud Server License",
                    quantity=Decimal("2.00"),
                    unit_price=Decimal("1500.00"),
                    discount_amount=Decimal("200.00"),
                    tax_amount=Decimal("140.00"),
                ),
                InvoiceItemCreate(
                    description="Onboarding Professional Services",
                    quantity=Decimal("1.00"),
                    unit_price=Decimal("500.00"),
                    discount_amount=Decimal("0.00"),
                    tax_amount=Decimal("25.00"),
                ),
            ],
        )
        invoice = await invoice_service.create_invoice(db_session, org_id, req)
        assert invoice.invoice_number.startswith("INV-")
        assert invoice.status == "DRAFT"
        assert invoice.subtotal == Decimal("3500.00")
        assert invoice.discount_total == Decimal("200.00")
        assert invoice.tax_total == Decimal("165.00")
        assert invoice.total == Decimal("3465.00")
        assert invoice.amount_due == Decimal("3465.00")
        assert invoice.amount_paid == Decimal("0.00")

        # 2. Issue invoice
        issued_inv = await invoice_service.issue_invoice(db_session, org_id, invoice.id)
        assert issued_inv.status == "ISSUED"

        # 3. Create invoice from accepted quotation
        prod_id = uuid.uuid4()
        product = Product(
            id=prod_id,
            organization_id=org_id,
            name="Enterprise Hardware Server",
            sku="HW-ENT-1",
            unit_price=Decimal("5000.00"),
            is_active=True,
        )
        db_session.add(product)

        q_id = uuid.uuid4()
        quotation = Quotation(
            id=q_id,
            organization_id=org_id,
            quotation_number=f"QT-{org_id.hex[:6]}",
            customer_id=cust_id,
            created_by_user_id=user.id,
            status="accepted",
            subtotal=Decimal("5000.00"),
            total_amount=Decimal("5000.00"),
            currency="USD",
        )
        db_session.add(quotation)
        q_item = QuotationItem(
            id=uuid.uuid4(),
            quotation_id=q_id,
            product_id=prod_id,
            product_name="Enterprise Hardware Server",
            sku="HW-ENT-1",
            quantity=Decimal("1.00"),
            unit_price=Decimal("5000.00"),
            line_total=Decimal("5000.00"),
        )
        db_session.add(q_item)
        await db_session.commit()

        q_invoice = await invoice_service.create_invoice_from_quotation(db_session, org_id, q_id)
        assert q_invoice.quotation_id == q_id
        assert q_invoice.total == Decimal("5000.00")

        # Prevent duplicate invoice creation for same quotation
        dup_invoice = await invoice_service.create_invoice_from_quotation(db_session, org_id, q_id)
        assert dup_invoice.id == q_invoice.id


@pytest.mark.asyncio
async def test_phase_47_payment_recording_and_balance_update():
    async with AsyncSessionLocal() as db_session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Billing Corp 2", slug=f"bill-corp-{org_id.hex[:6]}")
        db_session.add(org)

        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            organization_id=org_id,
            email=f"finance-{user_id.hex[:6]}@billcorp.com",
            password_hash=hash_password("Password123!"),
            full_name="Finance Manager",
            is_admin=True,
            is_active=True,
        )
        db_session.add(user)

        cust_id = uuid.uuid4()
        customer = Customer(id=cust_id, organization_id=org_id, name="Beta Corp", email="beta@corp.com", is_active=True)
        db_session.add(customer)
        await db_session.commit()

        # Create & issue invoice for $1,000
        req = InvoiceCreateRequest(
            customer_id=cust_id,
            currency="USD",
            items=[
                InvoiceItemCreate(description="Software Subscription", quantity=Decimal("1.00"), unit_price=Decimal("1000.00")),
            ],
        )
        invoice = await invoice_service.create_invoice(db_session, org_id, req)
        await invoice_service.issue_invoice(db_session, org_id, invoice.id)

        # 1. Record Partial Payment of $400
        pay1_req = PaymentCreateRequest(invoice_id=invoice.id, amount=Decimal("400.00"), method="BANK_TRANSFER")
        payment1 = await payment_service.record_payment(db_session, org_id, pay1_req, user)
        assert payment1.payment_reference.startswith("PAY-")
        assert payment1.amount == Decimal("400.00")

        # Reload invoice to check balance
        inv_after_pay1 = await invoice_service.get_invoice(db_session, org_id, invoice.id)
        assert inv_after_pay1.amount_paid == Decimal("400.00")
        assert inv_after_pay1.amount_due == Decimal("600.00")
        assert inv_after_pay1.status == "PARTIALLY_PAID"

        # 2. Test overpayment rejection ($700 > remaining $600)
        overpay_req = PaymentCreateRequest(invoice_id=invoice.id, amount=Decimal("700.00"), method="CARD")
        with pytest.raises(BusinessRuleViolationException):
            await payment_service.record_payment(db_session, org_id, overpay_req, user)

        # 3. Record remaining payment of $600
        pay2_req = PaymentCreateRequest(invoice_id=invoice.id, amount=Decimal("600.00"), method="CARD")
        await payment_service.record_payment(db_session, org_id, pay2_req, user)

        inv_final = await invoice_service.get_invoice(db_session, org_id, invoice.id)
        assert inv_final.amount_paid == Decimal("1000.00")
        assert inv_final.amount_due == Decimal("0.00")
        assert inv_final.status == "PAID"


@pytest.mark.asyncio
async def test_phase_48_49_subscription_and_billing_schedules():
    async with AsyncSessionLocal() as db_session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Billing Corp 3", slug=f"bill-corp-{org_id.hex[:6]}")
        db_session.add(org)

        cust_id = uuid.uuid4()
        customer = Customer(id=cust_id, organization_id=org_id, name="Gamma LLC", email="gamma@llc.com", is_active=True)
        db_session.add(customer)

        prod_id = uuid.uuid4()
        product = Product(id=prod_id, organization_id=org_id, name="Enterprise SaaS Plan", sku="SUB-SAAS-ENT", unit_price=Decimal("200.00"), is_active=True)
        db_session.add(product)
        await db_session.commit()

        # 1. Create Subscription
        sub_req = SubscriptionCreateRequest(
            customer_id=cust_id,
            product_id=prod_id,
            plan_name="Enterprise SaaS Plan",
            quantity=Decimal("5.00"),
            unit_price=Decimal("200.00"),
            billing_interval="MONTHLY",
            start_date=date(2026, 9, 1),
        )
        subscription = await subscription_service.create_subscription(db_session, org_id, sub_req)
        assert subscription.subscription_number.startswith("SUB-")
        assert subscription.status == "ACTIVE"
        assert subscription.quantity == Decimal("5.00")
        assert subscription.unit_price == Decimal("200.00")
        assert len(subscription.schedules) == 1
        assert subscription.schedules[0].amount == Decimal("1000.00")

        # 2. Generate due billing schedules as of October 1, 2026
        due_schedules = await schedule_service.generate_due_billing_schedules(db_session, org_id, as_of_date=date(2026, 10, 1))
        assert len(due_schedules) >= 1

        # 3. Execute billing schedule invoice generation
        sched = due_schedules[0]
        sched_invoice = await schedule_service.execute_billing_schedule_invoice(db_session, org_id, sched.id)
        assert sched_invoice.total == Decimal("1000.00")
        assert sched_invoice.status == "DRAFT"

        # Verify schedule status updated to INVOICED
        sched_after = (await db_session.execute(select(BillingSchedule).where(BillingSchedule.id == sched.id))).scalar_one()
        assert sched_after.status == "INVOICED"
        assert sched_after.invoice_id == sched_invoice.id

        # Idempotency verification: repeated execution returns existing invoice
        dup_sched_inv = await schedule_service.execute_billing_schedule_invoice(db_session, org_id, sched.id)
        assert dup_sched_inv.id == sched_invoice.id


@pytest.mark.asyncio
async def test_phase_50_51_proration_and_cancellation():
    async with AsyncSessionLocal() as db_session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Billing Corp 4", slug=f"bill-corp-{org_id.hex[:6]}")
        db_session.add(org)

        user_id = uuid.uuid4()
        user = User(id=user_id, organization_id=org_id, email="mgr@corp.com", password_hash=hash_password("Password123!"), is_admin=True, is_active=True)
        db_session.add(user)

        cust_id = uuid.uuid4()
        customer = Customer(id=cust_id, organization_id=org_id, name="Delta Tech", email="delta@tech.com", is_active=True)
        db_session.add(customer)

        prod_id = uuid.uuid4()
        product = Product(id=prod_id, organization_id=org_id, name="Cloud Hosting Tier", sku="SUB-HOSTING", unit_price=Decimal("100.00"), is_active=True)
        db_session.add(product)
        await db_session.commit()

        # Create active subscription for 10 units @ $100 = $1,000/mo for September 1 to October 1 (30 days)
        sub_req = SubscriptionCreateRequest(
            customer_id=cust_id,
            product_id=prod_id,
            plan_name="Cloud Hosting Tier",
            quantity=Decimal("10.00"),
            unit_price=Decimal("100.00"),
            billing_interval="MONTHLY",
            start_date=date(2026, 9, 1),
        )
        subscription = await subscription_service.create_subscription(db_session, org_id, sub_req)

        # 1. Execute mid-cycle upgrade on September 16 (15 days remaining out of 30)
        # Upgrade quantity to 15 units @ $100 (+$500/mo base delta -> 15/30 * $500 = $250 prorated charge)
        prorate_req = SubscriptionProrationRequest(
            new_quantity=Decimal("15.00"),
            new_unit_price=Decimal("100.00"),
            effective_date=date(2026, 9, 16),
            notes="Customer upgraded from 10 to 15 host instances",
        )
        proration = await proration_service.prorate_subscription_adjustment(db_session, org_id, subscription.id, prorate_req, user)
        assert proration.total_period_days == 30
        assert proration.remaining_days == 15
        assert proration.prorated_amount == Decimal("250.00")

        # Verify subscription parameters updated
        sub_after_prorate = await subscription_service.get_subscription(db_session, org_id, subscription.id)
        assert sub_after_prorate.quantity == Decimal("15.00")

        # 2. Execute IMMEDIATE subscription cancellation
        cancel_req = SubscriptionCancellationRequest(
            cancellation_type="IMMEDIATE",
            reason="Customer migrating off-premise",
        )
        cancellation = await cancellation_service.cancel_subscription(db_session, org_id, subscription.id, cancel_req, user)
        assert cancellation.cancellation_type == "IMMEDIATE"
        assert cancellation.reason == "Customer migrating off-premise"

        sub_cancelled = await subscription_service.get_subscription(db_session, org_id, subscription.id)
        assert sub_cancelled.status == "CANCELLED"
        assert sub_cancelled.end_date == date.today()


@pytest.mark.asyncio
async def test_phase_52_credit_note_and_payment_refund():
    async with AsyncSessionLocal() as db_session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Billing Corp 5", slug=f"bill-corp-{org_id.hex[:6]}")
        db_session.add(org)

        user_id = uuid.uuid4()
        user = User(id=user_id, organization_id=org_id, email="mgr5@corp.com", password_hash=hash_password("Password123!"), is_admin=True, is_active=True)
        db_session.add(user)

        cust_id = uuid.uuid4()
        customer = Customer(id=cust_id, organization_id=org_id, name="Epsilon Systems", email="epsilon@sys.com", is_active=True)
        db_session.add(customer)
        await db_session.commit()

        # Create & issue invoice for $2,000
        req = InvoiceCreateRequest(
            customer_id=cust_id,
            currency="USD",
            items=[
                InvoiceItemCreate(description="Enterprise Software Package", quantity=Decimal("1.00"), unit_price=Decimal("2000.00")),
            ],
        )
        invoice = await invoice_service.create_invoice(db_session, org_id, req)
        await invoice_service.issue_invoice(db_session, org_id, invoice.id)

        # 1. Issue Partial Credit Note of $500
        cn_req = CreditNoteCreateRequest(
            invoice_id=invoice.id,
            reason="SLA outage credit allowance",
            items=[
                CreditNoteItemCreate(description="SLA Outage Adjustment", quantity=Decimal("1.00"), unit_price=Decimal("500.00")),
            ],
        )
        credit_note = await credit_note_service.create_credit_note(db_session, org_id, cn_req, user)
        assert credit_note.credit_note_number.startswith("CN-")
        assert credit_note.total == Decimal("500.00")
        assert credit_note.status == "ISSUED"

        # Verify invoice remaining amount_due deducted ($2000 - $500 = $1500)
        inv_after_cn = await invoice_service.get_invoice(db_session, org_id, invoice.id)
        assert inv_after_cn.amount_due == Decimal("1500.00")

        # 2. Test over-credit rejection (max remaining credit is $1500, attempt $1600)
        over_cn_req = CreditNoteCreateRequest(
            invoice_id=invoice.id,
            reason="Excess credit test",
            items=[CreditNoteItemCreate(description="Test", quantity=Decimal("1.00"), unit_price=Decimal("1600.00"))],
        )
        with pytest.raises(BusinessRuleViolationException):
            await credit_note_service.create_credit_note(db_session, org_id, over_cn_req, user)

        # 3. Record payment for remaining $1500
        pay_req = PaymentCreateRequest(invoice_id=invoice.id, amount=Decimal("1500.00"), method="BANK_TRANSFER")
        payment = await payment_service.record_payment(db_session, org_id, pay_req, user)

        # 4. Record Cash Payment Refund of $300 against payment
        rfd_req = PaymentRefundCreateRequest(
            payment_id=payment.id,
            credit_note_id=credit_note.id,
            amount=Decimal("300.00"),
            reason="Partial cash refund requested by customer",
        )
        refund = await credit_note_service.record_payment_refund(db_session, org_id, rfd_req, user)
        assert refund.refund_number.startswith("RFD-")
        assert refund.amount == Decimal("300.00")
        assert refund.status == "COMPLETED"

        # 5. Test over-refund rejection (max remaining refund on payment is $1200, attempt $1300)
        over_rfd_req = PaymentRefundCreateRequest(payment_id=payment.id, amount=Decimal("1300.00"), reason="Excess refund")
        with pytest.raises(BusinessRuleViolationException):
            await credit_note_service.record_payment_refund(db_session, org_id, over_rfd_req, user)


@pytest.mark.asyncio
async def test_phase_46_52_multi_tenant_isolation():
    async with AsyncSessionLocal() as db_session:
        org1_id = uuid.uuid4()
        org2_id = uuid.uuid4()
        org1 = Organization(id=org1_id, name="Org One", slug=f"org1-{org1_id.hex[:6]}")
        org2 = Organization(id=org2_id, name="Org Two", slug=f"org2-{org2_id.hex[:6]}")
        db_session.add_all([org1, org2])

        c1 = Customer(id=uuid.uuid4(), organization_id=org1_id, name="Customer One", email="c1@org1.com", is_active=True)
        c2 = Customer(id=uuid.uuid4(), organization_id=org2_id, name="Customer Two", email="c2@org2.com", is_active=True)
        db_session.add_all([c1, c2])
        await db_session.commit()

        # Create Invoice in Org 1
        inv1_req = InvoiceCreateRequest(
            customer_id=c1.id,
            items=[InvoiceItemCreate(description="Org 1 Service", quantity=Decimal("1.00"), unit_price=Decimal("100.00"))],
        )
        inv1 = await invoice_service.create_invoice(db_session, org1_id, inv1_req)

        # Org 2 attempts to fetch Org 1 invoice
        with pytest.raises(NotFoundException):
            await invoice_service.get_invoice(db_session, org2_id, inv1.id)

        # Org 2 attempts to record payment on Org 1 invoice
        pay_req = PaymentCreateRequest(invoice_id=inv1.id, amount=Decimal("50.00"), method="CASH")
        with pytest.raises(NotFoundException):
            await payment_service.record_payment(db_session, org2_id, pay_req)

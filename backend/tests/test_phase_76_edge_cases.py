import pytest
import uuid
from decimal import Decimal
from datetime import date, datetime, timezone, timedelta
from typing import List

from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from pydantic import ValidationError

from app.main import app
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, hash_password
from app.models.organization import Organization
from app.models.user import User
from app.models.customer import Customer
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.product import Product
from app.models.quotation import Quotation, QuotationItem
from app.models.quotation_approval import QuotationApproval
from app.models.approval_rule import ApprovalRule
from app.models.warehouses import Warehouse
from app.models.inventory import InventoryStock, InventoryReservation
from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import Payment
from app.models.credit_note import CreditNote
from app.models.subscription import Subscription

from app.schemas.quotation import QuotationCreate, QuotationItemCreate
from app.schemas.payments import PaymentCreateRequest
from app.schemas.credit_notes import CreditNoteCreateRequest, CreditNoteItemCreate, PaymentRefundCreateRequest
from app.schemas.subscriptions import SubscriptionCreateRequest, SubscriptionProrationRequest, SubscriptionCancellationRequest
from app.schemas.automation import AutomationCondition, AutomationConditionGroup
from app.schemas.inventory import ShipmentCreateRequest

from app.services import (
    quotations as quotation_service,
    quotation_state as quotation_state_service,
    approval_engine as approval_service,
    inventory as inventory_service,
    reservations as reservation_service,
    shipments as shipment_service,
    invoices as invoice_service,
    payments as payment_service,
    credit_notes as credit_note_service,
    subscriptions as subscription_service,
    prorations as proration_service,
    cancellations as cancellation_service,
    forecast as forecast_service,
    stalled_quote_engine,
    automation_conditions as automation_conditions_service,
)
from app.services.customer_intelligence import CustomerIntelligenceService
from app.core.exceptions import (
    NotFoundException,
    BusinessRuleViolationException,
    UnauthorizedException,
    ForbiddenException,
)


@pytest.mark.asyncio
async def test_auth_edge_cases_and_token_boundaries():
    async with AsyncSessionLocal() as session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name='Auth Edge Org', slug=f'auth-edge-{org_id.hex[:6]}', is_active=False)
        session.add(org)
        await session.flush()

        user = User(
            id=uuid.uuid4(),
            organization_id=org_id,
            email='inactive-org@dealflow.com',
            password_hash=hash_password('Secret123!'),
            is_active=True,
            is_admin=True,
        )
        session.add(user)

        active_org = Organization(id=uuid.uuid4(), name='Active Org', slug=f'act-{uuid.uuid4().hex[:6]}', is_active=True)
        session.add(active_org)
        await session.flush()

        inactive_user = User(
            id=uuid.uuid4(),
            organization_id=active_org.id,
            email='inactive-user@dealflow.com',
            password_hash=hash_password('Secret123!'),
            is_active=False,
            is_admin=False,
        )
        session.add(inactive_user)
        await session.commit()

        token_inactive_org = create_access_token(user.id)
        token_inactive_user = create_access_token(inactive_user.id)
        portal_token = create_access_token(subject=str(uuid.uuid4()), claims={'type': 'portal'})
        invalid_uuid_token = create_access_token(subject='not-a-valid-uuid-string')

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        res = await client.get('/api/v1/customers', headers={'Authorization': f'Bearer {token_inactive_org}'})
        assert res.status_code == 401

        res = await client.get('/api/v1/customers', headers={'Authorization': f'Bearer {token_inactive_user}'})
        assert res.status_code == 401

        res = await client.get('/api/v1/customers', headers={'Authorization': f'Bearer {portal_token}'})
        assert res.status_code == 401

        res = await client.get('/api/v1/customers', headers={'Authorization': f'Bearer {invalid_uuid_token}'})
        assert res.status_code == 401

        res = await client.get('/api/v1/customers', headers={'Authorization': 'Bearer   '})
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_multi_tenant_cross_entity_mix_and_match_rejection():
    async with AsyncSessionLocal() as session:
        org_a = Organization(id=uuid.uuid4(), name='Tenant A', slug=f'tenant-a-{uuid.uuid4().hex[:6]}')
        org_b = Organization(id=uuid.uuid4(), name='Tenant B', slug=f'tenant-b-{uuid.uuid4().hex[:6]}')
        session.add_all([org_a, org_b])
        await session.flush()

        cust_a = Customer(id=uuid.uuid4(), organization_id=org_a.id, name='Cust A', email='custA@a.com', is_active=True)
        cust_b = Customer(id=uuid.uuid4(), organization_id=org_b.id, name='Cust B', email='custB@b.com', is_active=True)
        session.add_all([cust_a, cust_b])

        contact_b = Contact(id=uuid.uuid4(), organization_id=org_b.id, customer_id=cust_b.id, first_name='Bob', last_name='B', email='bob@b.com', is_primary=True)
        prod_b = Product(id=uuid.uuid4(), organization_id=org_b.id, name='Widget B', sku='SKU-B', unit_price=Decimal('100.00'), is_active=True)
        session.add_all([contact_b, prod_b])

        inv_b = Invoice(
            id=uuid.uuid4(),
            organization_id=org_b.id,
            customer_id=cust_b.id,
            invoice_number='INV-B-001',
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('500.00'),
            total=Decimal('500.00'),
            amount_due=Decimal('500.00'),
            amount_paid=Decimal('0.00'),
            status='ISSUED',
        )
        session.add(inv_b)
        await session.commit()

        with pytest.raises(NotFoundException):
            await quotation_service.verify_contact_in_tenant(session, org_a.id, cust_a.id, contact_b.id)

        with pytest.raises(NotFoundException):
            await quotation_service.verify_product_in_tenant(session, org_a.id, prod_b.id)

        with pytest.raises(NotFoundException):
            pay_req = PaymentCreateRequest(
                invoice_id=inv_b.id,
                payment_date=date.today(),
                amount=Decimal('100.00'),
                method='BANK_TRANSFER',
            )
            await payment_service.record_payment(session, org_a.id, pay_req)

        with pytest.raises(NotFoundException):
            cn_req = CreditNoteCreateRequest(
                invoice_id=inv_b.id,
                reason='Cross-tenant test',
                items=[CreditNoteItemCreate(description='Item', quantity=Decimal('1.00'), unit_price=Decimal('50.00'))]
            )
            await credit_note_service.create_credit_note(session, org_a.id, cn_req)


@pytest.mark.asyncio
async def test_financial_and_margin_edge_cases():
    async with AsyncSessionLocal() as session:
        org = Organization(id=uuid.uuid4(), name='Fin Edge Org', slug=f'fin-edge-{uuid.uuid4().hex[:6]}')
        session.add(org)
        await session.flush()

        customer = Customer(id=uuid.uuid4(), organization_id=org.id, name='Fin Cust', email='fin@cust.com', is_active=True)
        prod_free = Product(id=uuid.uuid4(), organization_id=org.id, name='Free Sample', sku='SKU-FREE', unit_price=Decimal('0.00'), unit_cost=Decimal('0.00'), is_active=True)
        prod_loss = Product(id=uuid.uuid4(), organization_id=org.id, name='Loss Leader', sku='SKU-LOSS', unit_price=Decimal('50.00'), unit_cost=Decimal('100.00'), is_active=True)
        prod_profit = Product(id=uuid.uuid4(), organization_id=org.id, name='Pure Software', sku='SKU-PROFIT', unit_price=Decimal('200.00'), unit_cost=Decimal('0.00'), is_active=True)
        session.add_all([customer, prod_free, prod_loss, prod_profit])
        await session.commit()

        # 1. Zero quantity rejected by Pydantic schema validation
        with pytest.raises(ValidationError):
            QuotationItemCreate(product_id=prod_free.id, quantity=Decimal('0.00'))

        # 2. Negative quantity rejected by Pydantic schema validation
        with pytest.raises(ValidationError):
            QuotationItemCreate(product_id=prod_free.id, quantity=Decimal('-5.00'))

        # 3. Negative unit price rejected by Pydantic schema validation
        with pytest.raises(ValidationError):
            QuotationItemCreate(product_id=prod_free.id, quantity=Decimal('1.00'), unit_price=Decimal('-10.00'))

        # 4. 100% Margin calculation (cost = 0, price = 200)
        items_prof, sub_prof, tot_prof = await quotation_service.calculate_line_items_and_totals(
            session,
            org.id,
            [QuotationItemCreate(product_id=prod_profit.id, quantity=Decimal('2.00'))],
            discount_amount=Decimal('0.00'),
            tax_amount=Decimal('0.00'),
        )
        assert sub_prof == Decimal('400.00')
        assert tot_prof == Decimal('400.00')

        # 5. Half-cent rounding / tax quantization determinism (33.333% tax on  -> .67)
        items_tax, sub_tax, tot_tax = await quotation_service.calculate_line_items_and_totals(
            session,
            org.id,
            [QuotationItemCreate(product_id=prod_loss.id, quantity=Decimal('1.00'), tax_rate=Decimal('33.333'))],
            discount_amount=Decimal('0.00'),
            tax_amount=Decimal('0.00'),
        )
        assert items_tax[0].tax_amount == Decimal('16.67')


@pytest.mark.asyncio
async def test_quotation_state_machine_and_commercial_locking():
    async with AsyncSessionLocal() as session:
        org = Organization(id=uuid.uuid4(), name='State Org', slug=f'state-org-{uuid.uuid4().hex[:6]}')
        session.add(org)
        await session.flush()

        customer = Customer(id=uuid.uuid4(), organization_id=org.id, name='State Cust', email='state@cust.com', is_active=True)
        user = User(id=uuid.uuid4(), organization_id=org.id, email='rep@state.com', password_hash=hash_password('Secret123!'), is_admin=False, is_active=True)
        session.add_all([customer, user])
        await session.flush()

        quote = Quotation(
            id=uuid.uuid4(),
            organization_id=org.id,
            customer_id=customer.id,
            quotation_number='QT-STATE-001',
            status='rejected',
            quotation_date=date.today(),
            subtotal=Decimal('1000.00'),
            total_amount=Decimal('1000.00'),
        )
        session.add(quote)
        await session.commit()

        with pytest.raises(BusinessRuleViolationException, match='Invalid quotation status transition'):
            await quotation_state_service.transition_quotation(session, org.id, quote.id, target_status='accepted')

        with pytest.raises(BusinessRuleViolationException, match='Invalid quotation status transition'):
            await quotation_state_service.transition_quotation(session, org.id, quote.id, target_status='draft')


@pytest.mark.asyncio
async def test_inventory_and_fulfillment_edge_cases():
    async with AsyncSessionLocal() as session:
        org = Organization(id=uuid.uuid4(), name='Inv Edge Org', slug=f'inv-edge-{uuid.uuid4().hex[:6]}')
        session.add(org)
        await session.flush()

        customer = Customer(id=uuid.uuid4(), organization_id=org.id, name='Inv Cust', email='inv@cust.com', is_active=True)
        warehouse = Warehouse(id=uuid.uuid4(), organization_id=org.id, code='WH-ACT', name='Active WH', priority=1, is_active=True)
        product = Product(id=uuid.uuid4(), organization_id=org.id, name='Stock Item', sku='SKU-STK', unit_price=Decimal('100.00'), is_active=True)
        session.add_all([customer, warehouse, product])
        await session.flush()

        quote_canc = Quotation(
            id=uuid.uuid4(),
            organization_id=org.id,
            customer_id=customer.id,
            quotation_number='QT-CANC-001',
            status='cancelled',
            quotation_date=date.today(),
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
        )
        session.add(quote_canc)
        await session.commit()

        with pytest.raises(BusinessRuleViolationException, match='Cannot reserve inventory for quotation in status'):
            await reservation_service.reserve_stock_for_quotation(session, org.id, quote_canc.id)

        fake_shipment_id = uuid.uuid4()
        with pytest.raises(NotFoundException):
            await shipment_service.update_shipment_status(session, org.id, fake_shipment_id, 'SUPER_DELIVERED')


@pytest.mark.asyncio
async def test_billing_payment_and_refund_edge_cases():
    async with AsyncSessionLocal() as session:
        org = Organization(id=uuid.uuid4(), name='Bill Edge Org', slug=f'bill-edge-{uuid.uuid4().hex[:6]}')
        session.add(org)
        await session.flush()

        customer = Customer(id=uuid.uuid4(), organization_id=org.id, name='Bill Cust', email='bill@cust.com', is_active=True)
        session.add(customer)
        await session.flush()

        draft_q = Quotation(
            id=uuid.uuid4(),
            organization_id=org.id,
            customer_id=customer.id,
            quotation_number='QT-DRAFT-001',
            status='draft',
            quotation_date=date.today(),
            subtotal=Decimal('200.00'),
            total_amount=Decimal('200.00'),
        )
        session.add(draft_q)
        await session.commit()

        with pytest.raises(BusinessRuleViolationException, match='Cannot invoice quotation in status'):
            await invoice_service.create_invoice_from_quotation(session, org.id, draft_q.id)


@pytest.mark.asyncio
async def test_subscription_proration_and_cancellation_boundaries():
    async with AsyncSessionLocal() as session:
        org = Organization(id=uuid.uuid4(), name='Sub Edge Org', slug=f'sub-edge-{uuid.uuid4().hex[:6]}')
        session.add(org)
        await session.flush()

        customer = Customer(id=uuid.uuid4(), organization_id=org.id, name='Sub Cust', email='sub@cust.com', is_active=True)
        product = Product(id=uuid.uuid4(), organization_id=org.id, name='SaaS Plan', sku='SKU-SAAS', unit_price=Decimal('50.00'), is_active=True)
        session.add_all([customer, product])
        await session.flush()

        sub_req = SubscriptionCreateRequest(
            customer_id=customer.id,
            product_id=product.id,
            plan_name='Cloud Enterprise',
            quantity=Decimal('10.00'),
            unit_price=Decimal('50.00'),
            billing_interval='MONTHLY',
            start_date=date.today(),
        )
        sub = await subscription_service.create_subscription(session, org.id, sub_req)
        assert sub.status == 'ACTIVE'

        pro_req = SubscriptionProrationRequest(
            new_quantity=Decimal('20.00'),
            new_unit_price=Decimal('50.00'),
            effective_date=date.today(),
            notes='Upgrade 10 -> 20 seats',
        )
        proration = await proration_service.prorate_subscription_adjustment(session, org.id, sub.id, pro_req)
        assert proration.prorated_amount > Decimal('0.00')
        assert proration.new_quantity == Decimal('20.00')

        canc_req = SubscriptionCancellationRequest(
            cancellation_type='IMMEDIATE',
            reason='Project completed',
        )
        cancellation = await cancellation_service.cancel_subscription(session, org.id, sub.id, canc_req)
        assert cancellation.cancellation_type == 'IMMEDIATE'

        with pytest.raises(BusinessRuleViolationException, match='Subscription is already in status'):
            await cancellation_service.cancel_subscription(session, org.id, sub.id, canc_req)


@pytest.mark.asyncio
async def test_customer_analytics_and_forecasting_zero_division_safety():
    async with AsyncSessionLocal() as session:
        org = Organization(id=uuid.uuid4(), name='Zero Div Org', slug=f'zero-div-{uuid.uuid4().hex[:6]}')
        session.add(org)
        await session.flush()

        customer = Customer(id=uuid.uuid4(), organization_id=org.id, name='New Zero Cust', email='zero@cust.com', is_active=True)
        session.add(customer)
        await session.commit()

        c360 = await CustomerIntelligenceService.get_customer_360_intelligence(session, org.id, customer.id)
        assert c360.customer_id == customer.id
        assert c360.sales.win_rate_percent == 0.0
        assert c360.financials.total_won_revenue == "0.00"
        assert c360.financials.margin_percentage == 0.0

        forecast = await forecast_service.calculate_revenue_forecast(session, org.id)
        assert forecast.open_pipeline == "0.00"
        assert forecast.weighted_pipeline == "0.00"
        assert len(forecast.deals) == 0


@pytest.mark.asyncio
async def test_automation_conditions_safe_evaluation():
    context = {
        'entity_type': 'quotation',
        'payload': {
            'total_amount': '5000.00',
            'discount_percent': 25,
            'status': 'sent',
            'customer': {
                'name': 'Acme Corp',
                'tier': 'ENTERPRISE'
            }
        }
    }

    cond1 = AutomationCondition(field='payload.customer.name', operator='equals', value='Acme Corp')
    assert automation_conditions_service.evaluate_single_condition(context, cond1) is True

    cond2 = AutomationCondition(field='payload.total_amount', operator='greater_than', value=4000)
    assert automation_conditions_service.evaluate_single_condition(context, cond2) is True

    cond_missing = AutomationCondition(field='payload.non_existent_key.deep_field', operator='equals', value='something')
    assert automation_conditions_service.evaluate_single_condition(context, cond_missing) is False

    cond_unknown_op = AutomationCondition(field='payload.status', operator='regex_match_custom', value='sent')
    assert automation_conditions_service.evaluate_single_condition(context, cond_unknown_op) is False

    group = AutomationConditionGroup(
        logical_operator='AND',
        conditions=[
            AutomationCondition(field='payload.status', operator='equals', value='sent'),
        ],
        groups=[
            AutomationConditionGroup(
                logical_operator='OR',
                conditions=[
                    AutomationCondition(field='payload.discount_percent', operator='greater_than', value=20),
                    AutomationCondition(field='payload.total_amount', operator='greater_than', value=100000),
                ]
            )
        ]
    )
    assert automation_conditions_service.evaluate_condition_group(context, group) is True

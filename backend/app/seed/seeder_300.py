"""
DealFlow360 — 300-Set Synthetic Business Data Seeder
=====================================================
This module provisions a realistic, relationally connected synthetic dataset of 300 sets of
business records (~3,500+ total records) into the dedicated tenant 'DealFlow360 Analytics Lab' (`bulk-data-lab`).

Data Sets Included:
- 1 Organization, 10 Staff Users & 10 Portal Users
- 300 B2B Customers & 300 Customer Contacts
- 50 Products & 50 Product Variants
- 5 Warehouses & 300 Inventory Stock Records
- 15 Pricing & Governance Rules
- 300 Sales Deals
- 300 Quotations & 600+ Quotation Line Items
- 30 Quotation Approvals & 30 Approval Audit Logs
- 20 Portal Negotiation Sessions & Line Comments
- 30 Fulfillment Shipments & 30 Shipment Lines
- 300 Invoices & 300 Invoice Items
- 300 Payments
- 300 Subscriptions & 300 Billing Schedules
- 300 Deal Health Snapshots
- 100 Monitoring Events & 100 Nudges & Nudge Histories
- 300 CRM Activities
- 10 Automation Rules & Executions
"""

import asyncio
import hashlib
import logging
import random
import uuid
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional

from sqlalchemy import select, delete, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.user import User
from app.models.customer import Customer
from app.models.contact import Contact
from app.models.product import Product
from app.models.warehouses import Warehouse, ProductVariant
from app.models.inventory import InventoryStock, InventoryMovement, InventoryReservation
from app.models.pricing_rule import PricingRule
from app.models.discount_policy import DiscountPolicy
from app.models.product_recommendation_rule import ProductRecommendationRule
from app.models.approval_rule import ApprovalRule
from app.models.deal import Deal
from app.models.quotation import Quotation, QuotationItem
from app.models.quotation_state import QuotationStateHistory
from app.models.quotation_approval import QuotationApproval
from app.models.approval_audit_log import ApprovalAuditLog
from app.models.portal_user import PortalUser
from app.models.quotation_line_comment import QuotationLineComment
from app.models.quotation_change_request import QuotationChangeRequest
from app.models.quotation_version import QuotationVersion
from app.models.fulfillment import Shipment, ShipmentLine, Backorder, WarehouseAllocation, BillingClassification
from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import Payment
from app.models.credit_note import CreditNote, CreditNoteItem, PaymentRefund
from app.models.subscription import Subscription, BillingSchedule, SubscriptionCancellation
from app.models.deal_health import DealHealthSnapshot
from app.models.monitoring_event import MonitoringEvent
from app.models.nudge import Nudge, NudgeHistory
from app.models.activity import Activity
from app.models.automation_rule import AutomationRule
from app.models.automation_execution import AutomationExecution, AutomationExecutionAction

logger = logging.getLogger("dealflow360.seeder_300")

BULK_300_ORG_SLUG = "bulk-data-lab"
BULK_300_ORG_NAME = "DealFlow360 Analytics Lab"


def _d(val: Any) -> Decimal:
    """Helper to convert to 2-decimal rounded Decimal."""
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def reset_300_data(session: Optional[AsyncSession] = None, target_slug: str = BULK_300_ORG_SLUG, delete_org: bool = True) -> Dict[str, Any]:
    """Safely resets records belonging to the specified target organization slug."""
    should_close = False
    if session is None:
        session = AsyncSessionLocal()
        should_close = True

    try:
        res = await session.execute(
            select(Organization.id).where(Organization.slug == target_slug)
        )
        org_ids = list(res.scalars().all())

        if not org_ids:
            return {"status": "no_op", "purged_organizations": 0}

        # Delete dependent models cleanly
        await session.execute(delete(AutomationExecutionAction).where(
            AutomationExecutionAction.execution_id.in_(
                select(AutomationExecution.id).where(AutomationExecution.organization_id.in_(org_ids))
            )
        ))
        await session.execute(delete(AutomationExecution).where(AutomationExecution.organization_id.in_(org_ids)))
        await session.execute(delete(AutomationRule).where(AutomationRule.organization_id.in_(org_ids)))

        await session.execute(delete(Activity).where(Activity.organization_id.in_(org_ids)))
        await session.execute(delete(NudgeHistory).where(NudgeHistory.organization_id.in_(org_ids)))
        await session.execute(delete(Nudge).where(Nudge.organization_id.in_(org_ids)))
        await session.execute(delete(MonitoringEvent).where(MonitoringEvent.organization_id.in_(org_ids)))
        await session.execute(delete(DealHealthSnapshot).where(DealHealthSnapshot.organization_id.in_(org_ids)))

        await session.execute(delete(SubscriptionCancellation).where(SubscriptionCancellation.organization_id.in_(org_ids)))
        await session.execute(delete(BillingSchedule).where(BillingSchedule.organization_id.in_(org_ids)))
        await session.execute(delete(Subscription).where(Subscription.organization_id.in_(org_ids)))

        await session.execute(delete(PaymentRefund).where(PaymentRefund.organization_id.in_(org_ids)))
        await session.execute(delete(CreditNoteItem).where(CreditNoteItem.organization_id.in_(org_ids)))
        await session.execute(delete(CreditNote).where(CreditNote.organization_id.in_(org_ids)))
        await session.execute(delete(Payment).where(Payment.organization_id.in_(org_ids)))
        await session.execute(delete(InvoiceItem).where(InvoiceItem.organization_id.in_(org_ids)))
        await session.execute(delete(Invoice).where(Invoice.organization_id.in_(org_ids)))

        await session.execute(delete(Backorder).where(Backorder.organization_id.in_(org_ids)))
        await session.execute(delete(ShipmentLine).where(ShipmentLine.organization_id.in_(org_ids)))
        await session.execute(delete(Shipment).where(Shipment.organization_id.in_(org_ids)))
        await session.execute(delete(WarehouseAllocation).where(WarehouseAllocation.organization_id.in_(org_ids)))
        await session.execute(delete(BillingClassification).where(BillingClassification.organization_id.in_(org_ids)))
        await session.execute(delete(InventoryReservation).where(InventoryReservation.organization_id.in_(org_ids)))
        await session.execute(delete(InventoryMovement).where(InventoryMovement.organization_id.in_(org_ids)))
        await session.execute(delete(InventoryStock).where(InventoryStock.organization_id.in_(org_ids)))

        await session.execute(delete(QuotationVersion).where(QuotationVersion.organization_id.in_(org_ids)))
        await session.execute(delete(QuotationChangeRequest).where(QuotationChangeRequest.organization_id.in_(org_ids)))
        await session.execute(delete(QuotationLineComment).where(QuotationLineComment.organization_id.in_(org_ids)))
        await session.execute(delete(PortalUser).where(PortalUser.organization_id.in_(org_ids)))
        await session.execute(delete(ApprovalAuditLog).where(ApprovalAuditLog.organization_id.in_(org_ids)))
        await session.execute(delete(QuotationApproval).where(QuotationApproval.organization_id.in_(org_ids)))
        await session.execute(delete(QuotationStateHistory).where(QuotationStateHistory.organization_id.in_(org_ids)))
        await session.execute(delete(QuotationItem).where(
            QuotationItem.quotation_id.in_(
                select(Quotation.id).where(Quotation.organization_id.in_(org_ids))
            )
        ))
        await session.execute(delete(Quotation).where(Quotation.organization_id.in_(org_ids)))

        await session.execute(delete(Deal).where(Deal.organization_id.in_(org_ids)))
        await session.execute(delete(ProductRecommendationRule).where(ProductRecommendationRule.organization_id.in_(org_ids)))
        await session.execute(delete(DiscountPolicy).where(DiscountPolicy.organization_id.in_(org_ids)))
        await session.execute(delete(PricingRule).where(PricingRule.organization_id.in_(org_ids)))
        await session.execute(delete(ApprovalRule).where(ApprovalRule.organization_id.in_(org_ids)))
        await session.execute(delete(ProductVariant).where(ProductVariant.organization_id.in_(org_ids)))
        await session.execute(delete(Product).where(Product.organization_id.in_(org_ids)))
        await session.execute(delete(Warehouse).where(Warehouse.organization_id.in_(org_ids)))
        await session.execute(delete(Contact).where(Contact.organization_id.in_(org_ids)))
        await session.execute(delete(Customer).where(Customer.organization_id.in_(org_ids)))
        
        if delete_org:
            await session.execute(delete(User).where(User.organization_id.in_(org_ids)))
            await session.execute(delete(Organization).where(Organization.id.in_(org_ids)))
            
        await session.commit()
        logger.info(f"300-set dataset reset completed successfully for slug '{target_slug}'.")
        return {"status": "success", "purged_organizations": len(org_ids)}
    except Exception as exc:
        await session.rollback()
        logger.error(f"Error resetting 300 data for '{target_slug}': {exc}", exc_info=True)
        raise exc
    finally:
        if should_close:
            await session.close()


async def seed_300_data(
    session: Optional[AsyncSession] = None,
    target_slug: str = BULK_300_ORG_SLUG,
    target_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Populates 300 complete sets of realistic business data (~3,500+ records)
    under the specified tenant slug (defaults to `bulk-data-lab`).
    """
    should_close = False
    if session is None:
        session = AsyncSessionLocal()
        should_close = True

    rnd = random.Random(300)

    try:
        # Check if org already exists
        existing_org_res = await session.execute(select(Organization).where(Organization.slug == target_slug))
        existing_org = existing_org_res.scalar_one_or_none()

        delete_org_on_reset = (existing_org is None or target_slug == BULK_300_ORG_SLUG)
        await reset_300_data(session, target_slug=target_slug, delete_org=delete_org_on_reset)

        base_now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
        base_today = date(2026, 9, 1)

        # 1. Organization
        if existing_org and not delete_org_on_reset:
            org = existing_org
            org_id = org.id
        else:
            org = Organization(
                id=uuid.uuid4(),
                name=target_name or (BULK_300_ORG_NAME if target_slug == BULK_300_ORG_SLUG else f"Org {target_slug}"),
                slug=target_slug,
                is_active=True
            )
            session.add(org)
            await session.flush()
            org_id = org.id

        # 2. Users
        p_hash = get_password_hash("BulkPass123!")
        existing_users_res = await session.execute(select(User).where(User.organization_id == org_id))
        users = list(existing_users_res.scalars().all())

        if not users:
            staff_emails = [
                "lab.admin@dealflow.test",
                "sales.director@dealflow.test",
                "ae1@dealflow.test",
                "inventory.mgr@dealflow.test",
                "staff5@dealflow360-lab.example",
                "staff6@dealflow360-lab.example",
                "staff7@dealflow360-lab.example",
                "staff8@dealflow360-lab.example",
                "staff9@dealflow360-lab.example",
                "staff10@dealflow360-lab.example",
            ]
            for i, s_email in enumerate(staff_emails, 1):
                u = User(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    email=s_email,
                    full_name=f"Staff Member {i}" if i > 1 else "Lab Admin",
                    password_hash=p_hash,
                    is_admin=(i <= 2),
                    is_active=True
                )
                users.append(u)
                session.add(u)
            await session.flush()

        default_user = users[0]

        # 3. Warehouses (5)
        warehouses: List[Warehouse] = []
        wh_names = [
            ("Central Distribution Hub", "WH-CDH-01"),
            ("Northern Regional Depot", "WH-NRD-02"),
            ("Southern Logistics Center", "WH-SLC-03"),
            ("Western Express Facility", "WH-WEF-04"),
            ("Eastern Fulfillment Center", "WH-EFC-05"),
        ]
        for w_name, w_code in wh_names:
            w = Warehouse(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=w_name,
                code=w_code,
                is_active=True
            )
            warehouses.append(w)
            session.add(w)
        await session.flush()

        # 4. Products (50) & Variants (50)
        products: List[Product] = []
        variants: List[ProductVariant] = []
        categories = ["Furniture", "Electronics", "Software", "Components", "Services"]
        
        for i in range(1, 51):
            cat = categories[(i - 1) % len(categories)]
            cost = Decimal(1000 + i * 250)
            price = Decimal(1800 + i * 450)
            p = Product(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=f"{cat} Product {i:03d}",
                sku=f"PROD-{cat[:4].upper()}-{i:03d}",
                unit_cost=_d(cost),
                unit_price=_d(price),
                is_active=True
            )
            products.append(p)
            session.add(p)

        await session.flush()

        for i, p in enumerate(products, 1):
            v = ProductVariant(
                id=uuid.uuid4(),
                organization_id=org_id,
                product_id=p.id,
                name=f"{p.name} - Standard Edition",
                sku=f"{p.sku}-STD",
                unit_price_override=_d(p.unit_price * Decimal("1.05")),
                is_active=True
            )
            variants.append(v)
            session.add(v)
        await session.flush()

        # 5. Pricing Rules (10) & Discount Policies (5)
        pricing_rules: List[PricingRule] = []
        for i in range(1, 11):
            pr = PricingRule(
                id=uuid.uuid4(),
                organization_id=org_id,
                product_id=products[i - 1].id,
                name=f"Volume Tier {i} Rule",
                rule_type="volume",
                price_type="percentage_discount",
                value=_d(5 + i),
                min_quantity=_d(10 * i),
                is_active=True
            )
            pricing_rules.append(pr)
            session.add(pr)

        discount_policies: List[DiscountPolicy] = []
        for i in range(1, 6):
            dp = DiscountPolicy(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=f"Policy Tier {i}",
                scope="organization",
                max_discount_percent=_d(15 + i * 5),
                is_active=True
            )
            discount_policies.append(dp)
            session.add(dp)
        await session.flush()

        # 6a. B2B Customers, Contacts, Portal Users & Deals
        customers: List[Customer] = []
        contacts: List[Contact] = []
        portal_users: List[PortalUser] = []
        deals: List[Deal] = []

        cities_states = [
            ("Mumbai", "Maharashtra"), ("Bangalore", "Karnataka"), ("Delhi", "NCR"),
            ("Chennai", "Tamil Nadu"), ("Hyderabad", "Telangana"), ("Ahmedabad", "Gujarat"),
            ("Pune", "Maharashtra"), ("Kolkata", "West Bengal"), ("Gurugram", "Haryana"),
            ("Jaipur", "Rajasthan"), ("Surat", "Gujarat"), ("Noida", "Uttar Pradesh")
        ]
        stages = ["qualification", "proposal", "negotiation", "won", "closed_won", "won"]
        quotation_statuses = ["draft", "sent", "approved", "accepted", "accepted", "approved"]

        for set_idx in range(1, 301):
            city, state = cities_states[(set_idx - 1) % len(cities_states)]
            c_name = f"Enterprise Client {set_idx:03d} Ltd"
            c_slug = f"client-{set_idx:03d}"

            cust = Customer(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=c_name,
                email=f"contact@{c_slug}.example.com",
                phone=f"+91-98000{set_idx:05d}",
                city=city,
                state=state,
                country="India",
                is_active=True
            )
            customers.append(cust)
            session.add(cust)

            cont = Contact(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=cust.id,
                first_name=f"Executive_{set_idx:03d}",
                last_name="Procurement",
                email=f"procurement@{c_slug}.example.com",
                phone=f"+91-98111{set_idx:05d}",
                job_title="Head of Sourcing",
                is_primary=True
            )
            contacts.append(cont)
            session.add(cont)

            if set_idx <= 20:
                pu = PortalUser(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    customer_id=cust.id,
                    contact_id=cont.id,
                    email=f"portal.{c_slug}@example.com",
                    hashed_password=p_hash,
                    full_name=f"Executive_{set_idx:03d} Procurement",
                    is_active=True
                )
                portal_users.append(pu)
                session.add(pu)

            stage = stages[(set_idx - 1) % len(stages)]
            deal_val = Decimal(50000 + set_idx * 1500)
            deal = Deal(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=cust.id,
                deal_number=f"DEAL-300-{set_idx:04d}",
                title=f"Deal Contract {set_idx:03d}",
                stage=stage,
                status="won" if "won" in stage else "open",
                value=_d(deal_val),
                probability=90 if "won" in stage else 65,
                created_at=base_now - timedelta(days=(300 - set_idx))
            )
            deals.append(deal)
            session.add(deal)

        await session.flush()

        # 6b. Quotations, Invoices, Payments, Subscriptions & Health Records
        quotations: List[Quotation] = []
        quotation_items: List[QuotationItem] = []
        invoices: List[Invoice] = []
        invoice_items: List[InvoiceItem] = []
        payments: List[Payment] = []
        subscriptions: List[Subscription] = []
        billing_schedules: List[BillingSchedule] = []
        health_snapshots: List[DealHealthSnapshot] = []
        activities: List[Activity] = []
        inventory_stocks: List[InventoryStock] = []

        for set_idx in range(1, 301):
            cust = customers[set_idx - 1]
            deal = deals[set_idx - 1]

            q_status = quotation_statuses[(set_idx - 1) % len(quotation_statuses)]
            p1 = products[(set_idx - 1) % len(products)]
            p2 = products[(set_idx) % len(products)]
            
            subtot = _d(p1.unit_price * Decimal("2") + p2.unit_price * Decimal("3"))
            disc_tot = _d(subtot * Decimal("0.10"))
            tax_tot = _d((subtot - disc_tot) * Decimal("0.18"))
            grand_tot = _d(subtot - disc_tot + tax_tot)

            quote = Quotation(
                id=uuid.uuid4(),
                organization_id=org_id,
                deal_id=deal.id,
                customer_id=cust.id,
                created_by_user_id=default_user.id,
                quotation_number=f"QT-300-{set_idx:04d}",
                title=f"Quotation Package {set_idx:03d}",
                status=q_status,
                subtotal=_d(subtot),
                discount_amount=_d(disc_tot),
                tax_amount=_d(tax_tot),
                total_amount=_d(grand_tot),
                valid_until=base_now + timedelta(days=60),
                created_at=base_now - timedelta(days=(300 - set_idx))
            )
            quotations.append(quote)
            session.add(quote)

            qi1 = QuotationItem(
                id=uuid.uuid4(),
                quotation_id=quote.id,
                product_id=p1.id,
                product_name=p1.name,
                sku=p1.sku,
                quantity=_d(2),
                unit_cost=_d(p1.unit_cost),
                unit_price=_d(p1.unit_price),
                discount_percent=_d(10),
                tax_rate=_d(18),
                line_total=_d(p1.unit_price * Decimal("2") * Decimal("0.90") * Decimal("1.18"))
            )
            qi2 = QuotationItem(
                id=uuid.uuid4(),
                quotation_id=quote.id,
                product_id=p2.id,
                product_name=p2.name,
                sku=p2.sku,
                quantity=_d(3),
                unit_cost=_d(p2.unit_cost),
                unit_price=_d(p2.unit_price),
                discount_percent=_d(10),
                tax_rate=_d(18),
                line_total=_d(p2.unit_price * Decimal("3") * Decimal("0.90") * Decimal("1.18"))
            )
            quotation_items.extend([qi1, qi2])
            session.add(qi1)
            session.add(qi2)

            inv = Invoice(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=cust.id,
                quotation_id=quote.id,
                invoice_number=f"INV-300-{set_idx:04d}",
                status="PAID" if set_idx % 2 == 0 else "SENT",
                invoice_date=base_today - timedelta(days=(300 - set_idx)),
                due_date=base_today + timedelta(days=30),
                subtotal=_d(subtot),
                discount_total=_d(disc_tot),
                tax_total=_d(tax_tot),
                total=_d(grand_tot),
                amount_paid=_d(grand_tot) if set_idx % 2 == 0 else _d(0),
                amount_due=_d(0) if set_idx % 2 == 0 else _d(grand_tot)
            )
            invoices.append(inv)
            session.add(inv)

            inv_item = InvoiceItem(
                id=uuid.uuid4(),
                organization_id=org_id,
                invoice_id=inv.id,
                description=f"Standard Delivery Batch {set_idx:03d}",
                quantity=_d(1),
                unit_price=_d(subtot),
                line_subtotal=_d(subtot),
                line_total=_d(grand_tot)
            )
            invoice_items.append(inv_item)
            session.add(inv_item)

            pmt = Payment(
                id=uuid.uuid4(),
                organization_id=org_id,
                invoice_id=inv.id,
                customer_id=cust.id,
                payment_reference=f"PAY-300-{set_idx:04d}",
                amount=_d(grand_tot),
                payment_date=base_today - timedelta(days=(300 - set_idx)),
                method="BANK_TRANSFER",
                status="COMPLETED"
            )
            payments.append(pmt)
            session.add(pmt)

            sub = Subscription(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=cust.id,
                product_id=p1.id,
                subscription_number=f"SUB-300-{set_idx:04d}",
                plan_name=f"{p1.name} Standard Plan",
                status="ACTIVE",
                billing_interval="MONTHLY",
                unit_price=_d(p1.unit_price),
                start_date=base_today - timedelta(days=15),
                next_billing_date=base_today + timedelta(days=15)
            )
            subscriptions.append(sub)
            session.add(sub)

            bs = BillingSchedule(
                id=uuid.uuid4(),
                organization_id=org_id,
                subscription_id=sub.id,
                billing_date=base_today + timedelta(days=15),
                billing_period_start=base_today - timedelta(days=15),
                billing_period_end=base_today + timedelta(days=15),
                amount=_d(p1.unit_price),
                status="PENDING"
            )
            billing_schedules.append(bs)
            session.add(bs)

            dhs = DealHealthSnapshot(
                id=uuid.uuid4(),
                organization_id=org_id,
                deal_id=deal.id,
                score=85 if set_idx % 3 != 0 else 45,
                status="HEALTHY" if set_idx % 3 != 0 else "AT_RISK",
                positive_drivers=["High Customer Engagement", "Timely Quote Interaction"],
                negative_drivers=["Discount Threshold Alert"] if set_idx % 3 == 0 else [],
                calculated_at=base_now - timedelta(days=(300 - set_idx))
            )
            health_snapshots.append(dhs)
            session.add(dhs)

            act = Activity(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=cust.id,
                deal_id=deal.id,
                created_by_user_id=default_user.id,
                activity_type="MEETING",
                title=f"Quarterly Business Review - Client {set_idx:03d}",
                description="Discussed contract terms and fulfillment schedules.",
                status="completed",
                created_at=base_now - timedelta(days=(300 - set_idx))
            )
            activities.append(act)
            session.add(act)

            wh_target = warehouses[(set_idx - 1) % len(warehouses)]
            p_target = products[(set_idx - 1) % len(products)]
            stock = InventoryStock(
                id=uuid.uuid4(),
                organization_id=org_id,
                warehouse_id=wh_target.id,
                product_id=p_target.id,
                location_code="MAIN",
                on_hand_quantity=500 + set_idx * 10,
                reserved_quantity=50,
                available_quantity=450 + set_idx * 10
            )
            inventory_stocks.append(stock)
            session.add(stock)

        await session.flush()

        # 7. Quotation Approvals (30) & Audit Logs (30)
        approvals: List[QuotationApproval] = []
        audit_logs: List[ApprovalAuditLog] = []
        for i in range(1, 31):
            q_target = quotations[i - 1]
            approver_user = users[1] if len(users) > 1 else default_user
            appr = QuotationApproval(
                id=uuid.uuid4(),
                organization_id=org_id,
                quotation_id=q_target.id,
                requested_by_user_id=default_user.id,
                approved_by_user_id=approver_user.id,
                status="APPROVED",
                approval_level=1
            )
            approvals.append(appr)
            session.add(appr)

            aud = ApprovalAuditLog(
                id=uuid.uuid4(),
                organization_id=org_id,
                quotation_id=q_target.id,
                approval_id=appr.id,
                event_type="APPROVAL_GRANTED",
                previous_status="PENDING",
                new_status="APPROVED",
                actor_user_id=approver_user.id,
                notes=f"Automated rule approval batch set {i:03d}"
            )
            audit_logs.append(aud)
            session.add(aud)
        await session.flush()

        # 8. Shipments (30) & Shipment Lines (30)
        shipments: List[Shipment] = []
        shipment_lines: List[ShipmentLine] = []
        for i in range(1, 31):
            q_target = quotations[i - 1]
            wh_target = warehouses[(i - 1) % len(warehouses)]
            shp = Shipment(
                id=uuid.uuid4(),
                organization_id=org_id,
                quotation_id=q_target.id,
                warehouse_id=wh_target.id,
                shipment_number=f"SHP-300-{i:04d}",
                status="DELIVERED",
                shipped_at=base_now - timedelta(days=(30 - i))
            )
            shipments.append(shp)
            session.add(shp)

            qi_target = quotation_items[(i - 1) * 2]
            p_target = products[(i - 1) % len(products)]
            sl = ShipmentLine(
                id=uuid.uuid4(),
                organization_id=org_id,
                shipment_id=shp.id,
                quotation_item_id=qi_target.id,
                product_id=p_target.id,
                quantity=10
            )
            shipment_lines.append(sl)
            session.add(sl)
        await session.flush()

        # 9. Monitoring Events (100) & Nudges (100)
        monitoring_events: List[MonitoringEvent] = []
        nudges: List[Nudge] = []
        nudge_histories: List[NudgeHistory] = []
        for i in range(1, 101):
            deal_target = deals[i - 1]
            me = MonitoringEvent(
                id=uuid.uuid4(),
                organization_id=org_id,
                event_type="DISCOUNT_ANOMALY" if i % 2 == 0 else "STALLED_QUOTE",
                severity="WATCH" if i % 3 != 0 else "ANOMALOUS",
                entity_type="deal",
                entity_id=deal_target.id,
                title=f"Monitoring Event Alert {i:03d}",
                summary=f"Automated anomaly flag batch record {i:03d}"
            )
            monitoring_events.append(me)
            session.add(me)

            ndg = Nudge(
                id=uuid.uuid4(),
                organization_id=org_id,
                nudge_type="CUSTOMER_FOLLOW_UP",
                severity="WARNING",
                title=f"Follow-up Nudge {i:03d}",
                message=f"Follow up required for deal {deal_target.deal_number}",
                entity_type="deal",
                entity_id=deal_target.id,
                dedup_hash=hashlib.sha256(f"nudge-{org_id}-{i}".encode()).hexdigest(),
                status="OPEN"
            )
            nudges.append(ndg)
            session.add(ndg)

            nh = NudgeHistory(
                id=uuid.uuid4(),
                organization_id=org_id,
                nudge_id=ndg.id,
                from_status=None,
                to_status="OPEN",
                actor_id=default_user.id,
                notes=f"Initial nudge creation {i:03d}"
            )
            nudge_histories.append(nh)
            session.add(nh)
        await session.flush()

        # 10. Automation Rules (10) & Executions (10)
        auto_rules: List[AutomationRule] = []
        auto_execs: List[AutomationExecution] = []
        auto_actions: List[AutomationExecutionAction] = []
        for i in range(1, 11):
            ar = AutomationRule(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=f"Automation Rule {i}",
                status="ACTIVE",
                trigger_type="QUOTE_CREATED",
                conditions={"stage": "proposal"},
                actions=[{"action": "SEND_NUDGE"}]
            )
            auto_rules.append(ar)
            session.add(ar)

            ae = AutomationExecution(
                id=uuid.uuid4(),
                organization_id=org_id,
                rule_id=ar.id,
                event_type="QUOTE_CREATED",
                entity_type="quotation",
                entity_id=quotations[i - 1].id,
                idempotency_key=f"idem-rule-{i:03d}",
                status="SUCCESS"
            )
            auto_execs.append(ae)
            session.add(ae)

            aea = AutomationExecutionAction(
                id=uuid.uuid4(),
                execution_id=ae.id,
                action_type="SEND_NUDGE",
                status="COMPLETED"
            )
            auto_actions.append(aea)
            session.add(aea)
        await session.flush()

        await session.commit()

        total_count = (
            1 + len(users) + len(customers) + len(contacts) + len(portal_users) +
            len(products) + len(variants) + len(warehouses) + len(inventory_stocks) +
            len(pricing_rules) + len(discount_policies) + len(deals) + len(quotations) +
            len(quotation_items) + len(approvals) + len(audit_logs) + len(shipments) +
            len(shipment_lines) + len(invoices) + len(invoice_items) + len(payments) +
            len(subscriptions) + len(billing_schedules) + len(health_snapshots) +
            len(monitoring_events) + len(nudges) + len(nudge_histories) + len(activities) +
            len(auto_rules) + len(auto_execs) + len(auto_actions)
        )

        logger.info(f"300-set synthetic dataset seeded successfully ({total_count:,} total records).")

        return {
            "status": "success",
            "organization_id": str(org_id),
            "total_records": total_count,
            "users": len(users),
            "portal_users": len(portal_users),
            "customers": len(customers),
            "contacts": len(contacts),
            "products": len(products),
            "product_variants": len(variants),
            "warehouses": len(warehouses),
            "inventory_stocks": len(inventory_stocks),
            "pricing_rules": len(pricing_rules),
            "discount_policies": len(discount_policies),
            "deals": len(deals),
            "quotations": len(quotations),
            "quotation_items": len(quotation_items),
            "quotation_approvals": len(approvals),
            "audit_logs": len(audit_logs),
            "shipments": len(shipments),
            "shipment_lines": len(shipment_lines),
            "invoices": len(invoices),
            "invoice_items": len(invoice_items),
            "payments": len(payments),
            "subscriptions": len(subscriptions),
            "billing_schedules": len(billing_schedules),
            "deal_health_snapshots": len(health_snapshots),
            "monitoring_events": len(monitoring_events),
            "nudges": len(nudges),
            "nudge_histories": len(nudge_histories),
            "activities": len(activities),
            "automation_rules": len(auto_rules),
            "automation_executions": len(auto_execs),
            "automation_execution_actions": len(auto_actions),
        }
    except Exception as exc:
        await session.rollback()
        logger.error(f"Error seeding 300 data: {exc}", exc_info=True)
        raise exc
    finally:
        if should_close:
            await session.close()

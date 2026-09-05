"""
DealFlow360 — 200-Record Realistic Synthetic Data Seeder
=========================================================
This module provisions a realistic, relationally connected synthetic dataset of ~200+
records into the dedicated tenant 'DealFlow360 Analytics Lab' (`bulk-data-lab`).

It covers:
- 1 Organization, 4 Staff Users & 5 Portal Users
- 20 B2B Customers & 20 Customer Contacts
- 20 Products & 15 Product Variants
- 3 Warehouses & 15 Inventory Stock records
- 10 Pricing & Governance Rules
- 30 Quotations/Deals & 45+ Quotation Line Items
- 10 Approval & Portal Negotiation records
- 8 Fulfillment Shipments & Backorders
- 10 Invoices & 8 Payments
- 5 Subscriptions & 15 Billing Schedules
- 10 Deal Health Snapshots, 5 Monitoring Events & 10 Nudges
- 10 CRM Activities & 7 Automation Rule/Execution records
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

logger = logging.getLogger("dealflow360.seeder_200")

BULK_200_ORG_SLUG = "bulk-data-lab"
BULK_200_ORG_NAME = "DealFlow360 Analytics Lab"


def _d(val: Any) -> Decimal:
    """Helper to convert to 2-decimal rounded Decimal."""
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def reset_200_data(session: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """Safely resets records belonging strictly to 'bulk-data-lab'."""
    should_close = False
    if session is None:
        session = AsyncSessionLocal()
        should_close = True

    try:
        res = await session.execute(
            select(Organization.id).where(Organization.slug == BULK_200_ORG_SLUG)
        )
        org_ids = list(res.scalars().all())

        if not org_ids:
            return {"status": "no_op", "purged_organizations": 0}

        # 1. Automation Executions & Actions
        await session.execute(delete(AutomationExecutionAction).where(
            AutomationExecutionAction.execution_id.in_(
                select(AutomationExecution.id).where(AutomationExecution.organization_id.in_(org_ids))
            )
        ))
        await session.execute(delete(AutomationExecution).where(AutomationExecution.organization_id.in_(org_ids)))
        await session.execute(delete(AutomationRule).where(AutomationRule.organization_id.in_(org_ids)))

        # 2. CRM, Nudges, Monitoring & Deal Health
        await session.execute(delete(Activity).where(Activity.organization_id.in_(org_ids)))
        await session.execute(delete(NudgeHistory).where(NudgeHistory.organization_id.in_(org_ids)))
        await session.execute(delete(Nudge).where(Nudge.organization_id.in_(org_ids)))
        await session.execute(delete(MonitoringEvent).where(MonitoringEvent.organization_id.in_(org_ids)))
        await session.execute(delete(DealHealthSnapshot).where(DealHealthSnapshot.organization_id.in_(org_ids)))

        # 3. Subscriptions & Billing Schedules
        await session.execute(delete(SubscriptionCancellation).where(SubscriptionCancellation.organization_id.in_(org_ids)))
        await session.execute(delete(BillingSchedule).where(BillingSchedule.organization_id.in_(org_ids)))
        await session.execute(delete(Subscription).where(Subscription.organization_id.in_(org_ids)))

        # 4. Invoices & Payments
        await session.execute(delete(PaymentRefund).where(PaymentRefund.organization_id.in_(org_ids)))
        await session.execute(delete(CreditNoteItem).where(CreditNoteItem.organization_id.in_(org_ids)))
        await session.execute(delete(CreditNote).where(CreditNote.organization_id.in_(org_ids)))
        await session.execute(delete(Payment).where(Payment.organization_id.in_(org_ids)))
        await session.execute(delete(InvoiceItem).where(InvoiceItem.organization_id.in_(org_ids)))
        await session.execute(delete(Invoice).where(Invoice.organization_id.in_(org_ids)))

        # 5. Fulfillment & Inventory
        await session.execute(delete(Backorder).where(Backorder.organization_id.in_(org_ids)))
        await session.execute(delete(ShipmentLine).where(ShipmentLine.organization_id.in_(org_ids)))
        await session.execute(delete(Shipment).where(Shipment.organization_id.in_(org_ids)))
        await session.execute(delete(WarehouseAllocation).where(WarehouseAllocation.organization_id.in_(org_ids)))
        await session.execute(delete(BillingClassification).where(BillingClassification.organization_id.in_(org_ids)))
        await session.execute(delete(InventoryReservation).where(InventoryReservation.organization_id.in_(org_ids)))
        await session.execute(delete(InventoryMovement).where(InventoryMovement.organization_id.in_(org_ids)))
        await session.execute(delete(InventoryStock).where(InventoryStock.organization_id.in_(org_ids)))

        # 6. Quotation & Portal
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

        # 7. Deals, Rules, Master Entities
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
        await session.execute(delete(User).where(User.organization_id.in_(org_ids)))

        # 8. Organization
        await session.execute(delete(Organization).where(Organization.id.in_(org_ids)))
        await session.commit()
        logger.info("200-record dataset reset completed successfully.")
        return {"status": "success", "purged_organizations": len(org_ids)}
    except Exception as exc:
        await session.rollback()
        logger.error(f"Error resetting 200 data: {exc}", exc_info=True)
        raise exc
    finally:
        if should_close:
            await session.close()


async def seed_200_data(session: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """
    Populates ~200+ realistic, valid, relationally connected synthetic records
    under the 'bulk-data-lab' tenant.
    Idempotent: resets existing bulk tenant first before re-seeding.
    """
    should_close = False
    if session is None:
        session = AsyncSessionLocal()
        should_close = True

    rnd = random.Random(200)

    try:
        # Reset existing bulk tenant data first
        await reset_200_data(session)

        base_now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)

        # 1. Organization
        org = Organization(
            id=uuid.uuid4(),
            name=BULK_200_ORG_NAME,
            slug=BULK_200_ORG_SLUG,
            is_active=True
        )
        session.add(org)
        await session.flush()
        org_id = org.id

        # 2. Staff Users (4)
        p_hash = get_password_hash("BulkPass123!")
        users_def = [
            ("Lab Admin", "lab.admin@dealflow.test", True),
            ("Sales Director", "sales.director@dealflow.test", True),
            ("Senior Account Exec", "ae1@dealflow.test", False),
            ("Inventory Manager", "inventory.mgr@dealflow.test", False),
        ]
        users: List[User] = []
        for name, email, is_adm in users_def:
            u = User(
                id=uuid.uuid4(),
                organization_id=org_id,
                email=email,
                full_name=name,
                password_hash=p_hash,
                is_admin=is_adm,
                is_active=True
            )
            users.append(u)
            session.add(u)
        await session.flush()

        # 3. B2B Customers (20)
        customer_names = [
            ("Meridian Retail Solutions", "Mumbai", "Maharashtra"),
            ("Nova Home Systems", "Bangalore", "Karnataka"),
            ("UrbanEdge Furnishings", "Delhi", "NCR"),
            ("Vertex Hospitality Group", "Chennai", "Tamil Nadu"),
            ("GreenLeaf Commercial", "Hyderabad", "Telangana"),
            ("Horizon Office Networks", "Ahmedabad", "Gujarat"),
            ("BluePeak Interiors", "Pune", "Maharashtra"),
            ("Sterling Distribution", "Kolkata", "West Bengal"),
            ("Apex Workspace Solutions", "Gurugram", "Haryana"),
            ("Sunrise Retail Group", "Jaipur", "Rajasthan"),
            ("Zenith Logistics Ltd", "Surat", "Gujarat"),
            ("Trident Tech Infrastructure", "Noida", "Uttar Pradesh"),
            ("OmniCorp Systems", "Bengaluru", "Karnataka"),
            ("Kaveri Trading Co", "Kochi", "Kerala"),
            ("Vanguard Medical Supplies", "Chandigarh", "Punjab"),
            ("Pinnacle Energy Corp", "Vadodara", "Gujarat"),
            ("Matrix Global Services", "Indore", "Madhya Pradesh"),
            ("Starlight Hospitality", "Goa", "Goa"),
            ("Crestview Financials", "Mumbai", "Maharashtra"),
            ("Beacon Industrial Supplies", "Coimbatore", "Tamil Nadu"),
        ]

        customers: List[Customer] = []
        contacts: List[Contact] = []

        for idx, (c_name, city, state) in enumerate(customer_names, 1):
            c_slug = c_name.lower().replace(" ", "-").replace(".", "")
            c = Customer(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=c_name,
                email=f"contact@{c_slug}.example",
                phone=f"+91-98765{idx:05d}",
                city=city,
                state=state,
                country="India",
                is_active=True
            )
            customers.append(c)
            session.add(c)

            # Contact per customer
            ct = Contact(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=c.id,
                first_name=c_name.split()[0],
                last_name="Procurement",
                email=f"procurement@{c_slug}.example",
                phone=f"+91-98123{idx:05d}",
                job_title="Head of Procurement",
                is_primary=True
            )
            contacts.append(ct)
            session.add(ct)
        await session.flush()

        # Portal Users for negotiation testing (5)
        portal_users: List[PortalUser] = []
        for idx in range(5):
            c_target = customers[idx]
            ct_target = contacts[idx]
            pu = PortalUser(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=c_target.id,
                contact_id=ct_target.id,
                email=f"portal.{c_target.email}",
                hashed_password=p_hash,
                full_name=f"{ct_target.first_name} {ct_target.last_name}",
                is_active=True
            )
            portal_users.append(pu)
            session.add(pu)
        await session.flush()

        # 4. Products (20) & Variants (15)
        product_catalog = [
            ("Executive Desk 180cm", "FURN-DESK-01", 25000, 42000),
            ("Ergonomic Mesh Chair", "FURN-CHAIR-01", 12000, 22000),
            ("Conference Table 10-Seater", "FURN-TBL-01", 45000, 75000),
            ("Mobile Storage Cabinet", "FURN-CAB-01", 8000, 14000),
            ("Executive Visitor Chair", "FURN-CHAIR-02", 7000, 12500),
            ("4K Business Monitor 32-inch", "ELEC-MON-32", 28000, 45000),
            ("Enterprise Laptop i7 32GB", "ELEC-LAP-01", 65000, 98000),
            ("Thunderbolt 4 Docking Station", "ELEC-DOCK-01", 11000, 18500),
            ("Wi-Fi 6E Mesh Router", "ELEC-NET-01", 14000, 24000),
            ("4K Video Conference Bar", "ELEC-CAM-01", 35000, 58000),
            ("DealFlow360 CRM License (Annual)", "SAAS-CRM-01", 15000, 36000),
            ("Analytics & BI Suite", "SAAS-BI-01", 20000, 48000),
            ("Inventory Cloud Pro", "SAAS-INV-01", 18000, 42000),
            ("Sales Intelligence Copilot", "SAAS-AI-01", 25000, 60000),
            ("Workflow Automation Engine", "SAAS-AUTO-01", 12000, 28000),
            ("Heavy-Duty Steel Desk Frame", "COMP-FRAME-01", 4000, 7500),
            ("Teak Wood Desktop Panel 180cm", "COMP-PANEL-01", 6000, 11000),
            ("Aluminum Chair Base Class-4", "COMP-BASE-01", 2200, 4500),
            ("Dual Motor Standing Lift", "COMP-MTR-01", 9000, 16000),
            ("Smart Touch Control Unit", "COMP-CTRL-01", 3000, 5800),
        ]

        products: List[Product] = []
        for name, sku, cost, price in product_catalog:
            p = Product(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=name,
                sku=sku,
                unit_cost=_d(cost),
                unit_price=_d(price),
                is_active=True
            )
            products.append(p)
            session.add(p)
        await session.flush()

        # Product Variants (15)
        variants: List[ProductVariant] = []
        variant_specs = [
            (products[0], "Oak Wood Finish", "FURN-DESK-01-OAK", 44000),
            (products[0], "Walnut Dark Finish", "FURN-DESK-01-WAL", 46000),
            (products[1], "Black Mesh", "FURN-CHAIR-01-BLK", 22000),
            (products[1], "Grey Mesh", "FURN-CHAIR-01-GRY", 22500),
            (products[2], "Mahogany Finish", "FURN-TBL-01-MAH", 78000),
            (products[5], "32-inch Curved", "ELEC-MON-32-CRV", 48000),
            (products[5], "32-inch Flat IPS", "ELEC-MON-32-FLT", 45000),
            (products[6], "16-inch Touchscreen", "ELEC-LAP-01-TCH", 104000),
            (products[6], "14-inch Ultraportable", "ELEC-LAP-01-ULT", 98000),
            (products[10], "Standard 1-User", "SAAS-CRM-01-STD", 36000),
            (products[10], "Enterprise Team Pack", "SAAS-CRM-01-ENT", 180000),
            (products[15], "Matte Black Frame", "COMP-FRAME-01-BLK", 7500),
            (products[15], "Silver Anodized", "COMP-FRAME-01-SLV", 7800),
            (products[18], "Dual Motor Heavy", "COMP-MTR-01-HVY", 17500),
            (products[19], "Touch Memory Presets", "COMP-CTRL-01-MEM", 6200),
        ]

        for p_parent, v_name, v_sku, v_price in variant_specs:
            v = ProductVariant(
                id=uuid.uuid4(),
                organization_id=org_id,
                product_id=p_parent.id,
                name=v_name,
                sku=v_sku,
                unit_price_override=_d(v_price),
                is_active=True
            )
            variants.append(v)
            session.add(v)
        await session.flush()

        # 5. Warehouses (3)
        wh_specs = [
            ("Ahmedabad Central Warehouse", "WH-AMD-01"),
            ("Mumbai East Warehouse", "WH-BOM-01"),
            ("Bangalore West Warehouse", "WH-BLR-01"),
        ]
        warehouses: List[Warehouse] = []
        for w_name, w_code in wh_specs:
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

        # 6. Inventory Stocks (15)
        stocks: List[InventoryStock] = []
        for idx in range(15):
            p_target = products[idx % len(products)]
            w_target = warehouses[idx % len(warehouses)]
            on_hand = rnd.randint(30, 200)
            reserved = rnd.randint(5, 20)
            stk = InventoryStock(
                id=uuid.uuid4(),
                organization_id=org_id,
                product_id=p_target.id,
                warehouse_id=w_target.id,
                on_hand_quantity=on_hand,
                reserved_quantity=reserved,
                available_quantity=on_hand - reserved
            )
            stocks.append(stk)
            session.add(stk)
        await session.flush()

        # 7. Pricing Rules & Discount Policies (10)
        pricing_rules: List[PricingRule] = []
        for idx in range(5):
            pr = PricingRule(
                id=uuid.uuid4(),
                organization_id=org_id,
                product_id=products[idx].id,
                name=f"Volume Discount Tier {idx+1}",
                rule_type="volume",
                price_type="percentage_discount",
                value=_d((idx + 1) * 2.5),
                min_quantity=Decimal(str(5 * (idx + 1))),
                priority=10 * (idx + 1),
                is_active=True
            )
            pricing_rules.append(pr)
            session.add(pr)

        discount_policies: List[DiscountPolicy] = []
        for idx in range(5):
            dp = DiscountPolicy(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=f"Commercial Threshold Policy {idx+1}",
                scope="organization",
                max_discount_percent=_d(10 + idx * 2),
                priority=10 * (idx + 1),
                is_active=True
            )
            discount_policies.append(dp)
            session.add(dp)
        await session.flush()

        # 8. Deals & Quotations (30 Quotes with 45+ Items)
        quotation_statuses = ["draft", "priced", "sent", "accepted", "rejected", "expired", "converted"]
        deals: List[Deal] = []
        quotations: List[Quotation] = []
        quotation_items: List[QuotationItem] = []

        for q_idx in range(30):
            c_target = customers[q_idx % len(customers)]
            u_rep = users[q_idx % len(users)]
            status = quotation_statuses[q_idx % len(quotation_statuses)]
            q_date = base_now - timedelta(days=rnd.randint(1, 90))

            deal = Deal(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=c_target.id,
                deal_number=f"DEAL-2026-{q_idx+101:04d}",
                title=f"Deal — {c_target.name} Expansion Q3",
                stage="won" if status in ["accepted", "converted"] else "proposal",
                status="won" if status in ["accepted", "converted"] else "open",
                value=_d(rnd.randint(50000, 500000)),
                probability=90 if status in ["accepted", "converted"] else 50,
                created_at=q_date
            )
            deals.append(deal)
            session.add(deal)
            await session.flush()

            # Create quotation
            q_number = f"QT-2026-{q_idx+101:04d}"
            quotation = Quotation(
                id=uuid.uuid4(),
                organization_id=org_id,
                deal_id=deal.id,
                customer_id=c_target.id,
                created_by_user_id=u_rep.id,
                quotation_number=q_number,
                status=status,
                subtotal=_d(0),
                discount_amount=_d(0),
                tax_amount=_d(0),
                total_amount=_d(0),
                created_at=q_date,
                valid_until=q_date + timedelta(days=30)
            )

            # Generate 1 to 3 items per quotation
            num_items = rnd.randint(1, 3)
            subtotal = Decimal("0.00")
            disc_tot = Decimal("0.00")
            tax_tot = Decimal("0.00")

            for item_idx in range(num_items):
                p_item = products[(q_idx + item_idx) % len(products)]
                qty = Decimal(str(rnd.randint(2, 10)))
                unit_p = p_item.unit_price
                disc_pct = Decimal(str(rnd.choice([0, 5, 10, 15])))
                
                gross = (qty * unit_p).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                disc_amt = (gross * (disc_pct / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                net = gross - disc_amt
                tax_amt = (net * Decimal("0.18")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                line_total = net + tax_amt

                subtotal += gross
                disc_tot += disc_amt
                tax_tot += tax_amt

                q_item = QuotationItem(
                    id=uuid.uuid4(),
                    quotation_id=quotation.id,
                    product_id=p_item.id,
                    product_name=p_item.name,
                    sku=p_item.sku,
                    quantity=qty,
                    unit_price=unit_p,
                    unit_cost=p_item.unit_cost,
                    discount_percent=disc_pct,
                    discount_amount=disc_amt,
                    tax_rate=Decimal("18.00"),
                    tax_amount=tax_amt,
                    line_total=line_total
                )
                quotation_items.append(q_item)
                session.add(q_item)

            quotation.subtotal = subtotal
            quotation.discount_amount = disc_tot
            quotation.tax_amount = tax_tot
            quotation.total_amount = subtotal - disc_tot + tax_tot

            quotations.append(quotation)
            session.add(quotation)
        await session.flush()

        # 9. Approvals & Negotiations (10)
        approvals: List[QuotationApproval] = []
        approval_logs: List[ApprovalAuditLog] = []
        line_comments: List[QuotationLineComment] = []
        change_requests: List[QuotationChangeRequest] = []
        versions: List[QuotationVersion] = []

        for idx in range(5):
            q_target = quotations[idx * 2]
            q_item_target = quotation_items[idx * 2] if quotation_items else None

            appr = QuotationApproval(
                id=uuid.uuid4(),
                organization_id=org_id,
                quotation_id=q_target.id,
                requested_by_user_id=users[2].id,
                approved_by_user_id=users[0].id if idx % 2 == 0 else None,
                status="APPROVED" if idx % 2 == 0 else "PENDING",
                approval_level=1,
                reasons="High-volume enterprise deal approval required for discount",
                decision_note="Approved based on customer tier and annual commitment" if idx % 2 == 0 else None
            )
            approvals.append(appr)
            session.add(appr)

            log = ApprovalAuditLog(
                id=uuid.uuid4(),
                organization_id=org_id,
                quotation_id=q_target.id,
                approval_id=appr.id,
                event_type="APPROVED" if idx % 2 == 0 else "SUBMITTED",
                actor_user_id=users[0].id,
                actor_name=users[0].full_name,
                previous_status="PENDING" if idx % 2 == 0 else None,
                new_status="APPROVED" if idx % 2 == 0 else "PENDING",
                reason="Governance threshold review",
                notes="Evaluated commercial terms and margin rules"
            )
            approval_logs.append(log)
            session.add(log)

            if q_item_target:
                comment = QuotationLineComment(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    quotation_id=q_target.id,
                    quotation_item_id=q_item_target.id,
                    author_type="PORTAL_USER",
                    author_portal_user_id=portal_users[idx].id if idx < len(portal_users) else None,
                    author_name=portal_users[idx].full_name if idx < len(portal_users) else "Customer Representative",
                    comment_text="Can we get an additional 2% discount on bulk shipment?",
                    is_internal_only=False
                )
                line_comments.append(comment)
                session.add(comment)

                chg = QuotationChangeRequest(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    quotation_id=q_target.id,
                    quotation_item_id=q_item_target.id,
                    requested_by_portal_user_id=portal_users[idx].id if idx < len(portal_users) else portal_users[0].id,
                    change_type="DISCOUNT_REQUEST",
                    status="OPEN",
                    requested_discount_percent=_d(18.0),
                    request_details="Requesting volume discount matching Enterprise tier"
                )
                change_requests.append(chg)
                session.add(chg)

            ver = QuotationVersion(
                id=uuid.uuid4(),
                organization_id=org_id,
                quotation_id=q_target.id,
                version_number=1,
                subtotal=q_target.subtotal,
                discount_amount=q_target.discount_amount,
                tax_amount=q_target.tax_amount,
                total_amount=q_target.total_amount,
                gross_margin=_d(rnd.randint(10000, 50000)),
                margin_percent=_d(rnd.randint(25, 45)),
                change_reason="Initial customer quote draft",
                snapshot_payload={"subtotal": str(q_target.subtotal), "total": str(q_target.total_amount)},
                created_by_user_id=users[0].id
            )
            versions.append(ver)
            session.add(ver)
        await session.flush()

        # 10. Fulfillment: Shipments & Backorders (8)
        shipments: List[Shipment] = []
        shipment_lines: List[ShipmentLine] = []
        backorders: List[Backorder] = []

        for idx in range(5):
            q_target = quotations[idx]
            q_item_target = quotation_items[idx] if idx < len(quotation_items) else quotation_items[0]
            ship = Shipment(
                id=uuid.uuid4(),
                organization_id=org_id,
                quotation_id=q_target.id,
                warehouse_id=warehouses[0].id,
                shipment_number=f"SHP-2026-{idx+101:04d}",
                status="DELIVERED" if idx % 2 == 0 else "SHIPPED",
                shipped_at=base_now - timedelta(days=idx+1)
            )
            shipments.append(ship)
            session.add(ship)

            s_line = ShipmentLine(
                id=uuid.uuid4(),
                organization_id=org_id,
                shipment_id=ship.id,
                quotation_item_id=q_item_target.id,
                product_id=products[idx % len(products)].id,
                quantity=5
            )
            shipment_lines.append(s_line)
            session.add(s_line)

        for idx in range(3):
            q_target = quotations[idx]
            q_item_target = quotation_items[idx] if idx < len(quotation_items) else quotation_items[0]
            bo = Backorder(
                id=uuid.uuid4(),
                organization_id=org_id,
                backorder_number=f"BO-2026-{idx+101:04d}",
                quotation_id=q_target.id,
                quotation_item_id=q_item_target.id,
                customer_id=q_target.customer_id,
                product_id=products[idx].id,
                warehouse_id=warehouses[1].id,
                requested_quantity=15,
                fulfilled_quantity=10,
                remaining_quantity=5,
                status="PARTIALLY_FULFILLED"
            )
            backorders.append(bo)
            session.add(bo)
        await session.flush()

        # 11. Invoices (10) & Payments (8)
        invoices: List[Invoice] = []
        invoice_items: List[InvoiceItem] = []
        payments: List[Payment] = []

        for idx in range(10):
            q_target = quotations[idx]
            inv_number = f"INV-2026-{idx+101:04d}"
            inv_total = q_target.total_amount
            status = "PAID" if idx < 5 else ("PARTIALLY_PAID" if idx < 8 else "ISSUED")
            amt_paid = inv_total if status == "PAID" else (inv_total / Decimal("2") if status == "PARTIALLY_PAID" else Decimal("0.00"))
            amt_due = inv_total - amt_paid

            inv = Invoice(
                id=uuid.uuid4(),
                organization_id=org_id,
                quotation_id=q_target.id,
                customer_id=q_target.customer_id,
                invoice_number=inv_number,
                status=status,
                subtotal=q_target.subtotal,
                discount_total=q_target.discount_amount,
                tax_total=q_target.tax_amount,
                total=inv_total,
                amount_paid=amt_paid,
                amount_due=amt_due,
                invoice_date=(base_now - timedelta(days=20)).date(),
                due_date=(base_now + timedelta(days=10)).date()
            )
            invoices.append(inv)
            session.add(inv)

            # Invoice Item
            inv_item = InvoiceItem(
                id=uuid.uuid4(),
                organization_id=org_id,
                invoice_id=inv.id,
                product_id=products[idx % len(products)].id,
                description=products[idx % len(products)].name,
                quantity=Decimal("2"),
                unit_price=products[idx % len(products)].unit_price,
                line_subtotal=products[idx % len(products)].unit_price * Decimal("2"),
                line_total=products[idx % len(products)].unit_price * Decimal("2")
            )
            invoice_items.append(inv_item)
            session.add(inv_item)

            if amt_paid > Decimal("0.00"):
                pay = Payment(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    invoice_id=inv.id,
                    customer_id=inv.customer_id,
                    payment_reference=f"PAY-2026-{idx+101:04d}",
                    amount=amt_paid,
                    method="BANK_TRANSFER",
                    status="COMPLETED",
                    payment_date=(base_now - timedelta(days=5)).date()
                )
                payments.append(pay)
                session.add(pay)
        await session.flush()

        # 12. Subscriptions (5) & Billing Schedules (15)
        subscriptions: List[Subscription] = []
        schedules: List[BillingSchedule] = []

        for idx in range(5):
            sub = Subscription(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=customers[idx].id,
                product_id=products[10 + idx].id,  # SaaS products
                subscription_number=f"SUB-2026-{idx+101:04d}",
                plan_name=f"Enterprise {products[10+idx].name}",
                billing_interval="MONTHLY",
                unit_price=products[10+idx].unit_price,
                status="ACTIVE",
                start_date=(base_now - timedelta(days=60)).date(),
                next_billing_date=(base_now + timedelta(days=30)).date()
            )
            subscriptions.append(sub)
            session.add(sub)

            for sched_idx in range(3):
                s_start = (base_now + timedelta(days=30 * sched_idx)).date()
                s_end = s_start + timedelta(days=30)
                bs = BillingSchedule(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    subscription_id=sub.id,
                    billing_period_start=s_start,
                    billing_period_end=s_end,
                    billing_date=s_start,
                    amount=sub.unit_price,
                    status="PAID" if sched_idx == 0 else "SCHEDULED"
                )
                schedules.append(bs)
                session.add(bs)
        await session.flush()

        # 13. Deal Health (10), Monitoring (5), Nudges (10)
        health_snapshots: List[DealHealthSnapshot] = []
        for idx in range(10):
            d_target = deals[idx]
            status_h = "HEALTHY" if idx < 5 else ("AT_RISK" if idx < 8 else "CRITICAL")
            score = rnd.randint(80, 95) if status_h == "HEALTHY" else (rnd.randint(50, 75) if status_h == "AT_RISK" else rnd.randint(15, 45))
            dh = DealHealthSnapshot(
                id=uuid.uuid4(),
                organization_id=org_id,
                deal_id=d_target.id,
                score=score,
                status=status_h,
                positive_drivers=["Strong executive engagement", "Fast response times"] if status_h == "HEALTHY" else ["High potential contract value"],
                negative_drivers=["Slow response time to proposal"] if status_h != "HEALTHY" else []
            )
            health_snapshots.append(dh)
            session.add(dh)

        monitoring_events: List[MonitoringEvent] = []
        for idx in range(5):
            me = MonitoringEvent(
                id=uuid.uuid4(),
                organization_id=org_id,
                event_type="DISCOUNT_ANOMALY" if idx % 2 == 0 else "STALLED_QUOTE",
                severity="WATCH" if idx % 2 == 0 else "ANOMALOUS",
                entity_type="quotation",
                entity_id=quotations[idx].id,
                title=f"Monitoring Alert — Quotation {quotations[idx].quotation_number}",
                summary=f"Automated anomaly flag for quotation QT-2026-{idx+101:04d}",
                evidence={"quote_index": idx}
            )
            monitoring_events.append(me)
            session.add(me)

        nudges: List[Nudge] = []
        nudge_histories: List[NudgeHistory] = []
        for idx in range(5):
            ndg = Nudge(
                id=uuid.uuid4(),
                organization_id=org_id,
                nudge_type="QUOTE_STALLED",
                severity="WARNING",
                title=f"Follow up with {customers[idx].name}",
                message="Quotation sent over 7 days ago without customer response.",
                entity_type="quotation",
                entity_id=quotations[idx].id,
                dedup_hash=hashlib.sha256(f"nudge_200_{idx}".encode()).hexdigest()[:16],
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
                actor_id=users[0].id,
                actor_name=users[0].full_name,
                notes="Automated nudge creation"
            )
            nudge_histories.append(nh)
            session.add(nh)
        await session.flush()

        # 14. CRM Activities (10) & Automation Rules/Executions (7)
        activities: List[Activity] = []
        for idx in range(10):
            act = Activity(
                id=uuid.uuid4(),
                organization_id=org_id,
                deal_id=deals[idx % len(deals)].id,
                customer_id=customers[idx % len(customers)].id,
                created_by_user_id=users[idx % len(users)].id,
                activity_type="CALL" if idx % 2 == 0 else "MEETING",
                title=f"Commercial alignment discussion #{idx+1}",
                description="Follow up on commercial terms and delivery timelines",
                status="completed",
                priority="medium"
            )
            activities.append(act)
            session.add(act)

        auto_rules: List[AutomationRule] = []
        auto_execs: List[AutomationExecution] = []
        auto_actions: List[AutomationExecutionAction] = []

        rule = AutomationRule(
            id=uuid.uuid4(),
            organization_id=org_id,
            name="High Value Deal Follow-up Automation",
            trigger_type="DEAL_CREATED",
            status="ACTIVE",
            priority=1,
            conditions={"min_deal_value": 50000},
            actions=[{"action_type": "CREATE_NUDGE"}]
        )
        auto_rules.append(rule)
        session.add(rule)
        await session.flush()

        for idx in range(6):
            ae = AutomationExecution(
                id=uuid.uuid4(),
                organization_id=org_id,
                rule_id=rule.id,
                event_type="DEAL_CREATED",
                entity_type="deal",
                entity_id=deals[idx].id,
                status="SUCCESS",
                idempotency_key=f"idemp_200_exec_{idx}",
                conditions_matched=True,
                actions_total=1,
                actions_succeeded=1,
                actions_failed=0
            )
            auto_execs.append(ae)
            session.add(ae)

            act_exec = AutomationExecutionAction(
                id=uuid.uuid4(),
                execution_id=ae.id,
                action_type="CREATE_NUDGE",
                status="SUCCESS",
                result_payload={"nudge_created": True}
            )
            auto_actions.append(act_exec)
            session.add(act_exec)
        await session.flush()

        # Calculate Total Records Inserted
        total_records = (
            1 + len(users) + len(portal_users) + len(customers) + len(contacts) +
            len(products) + len(variants) + len(warehouses) + len(stocks) +
            len(pricing_rules) + len(discount_policies) + len(deals) +
            len(quotations) + len(quotation_items) + len(approvals) +
            len(approval_logs) + len(line_comments) + len(change_requests) +
            len(versions) + len(shipments) + len(shipment_lines) + len(backorders) +
            len(invoices) + len(invoice_items) + len(payments) + len(subscriptions) +
            len(schedules) + len(health_snapshots) + len(monitoring_events) +
            len(nudges) + len(nudge_histories) + len(activities) +
            len(auto_rules) + len(auto_execs) + len(auto_actions)
        )

        await session.commit()
        logger.info(f"200-record dataset seeding completed successfully with {total_records} records!")

        return {
            "status": "success",
            "total_records": total_records,
            "organization": BULK_200_ORG_NAME,
            "organization_slug": BULK_200_ORG_SLUG,
            "users": len(users),
            "portal_users": len(portal_users),
            "customers": len(customers),
            "contacts": len(contacts),
            "products": len(products),
            "product_variants": len(variants),
            "warehouses": len(warehouses),
            "inventory_stocks": len(stocks),
            "pricing_rules": len(pricing_rules),
            "discount_policies": len(discount_policies),
            "deals": len(deals),
            "quotations": len(quotations),
            "quotation_items": len(quotation_items),
            "quotation_approvals": len(approvals),
            "approval_audit_logs": len(approval_logs),
            "shipments": len(shipments),
            "shipment_lines": len(shipment_lines),
            "backorders": len(backorders),
            "invoices": len(invoices),
            "invoice_items": len(invoice_items),
            "payments": len(payments),
            "subscriptions": len(subscriptions),
            "billing_schedules": len(schedules),
            "deal_health_snapshots": len(health_snapshots),
            "monitoring_events": len(monitoring_events),
            "nudges": len(nudges),
            "activities": len(activities),
            "automation_rules": len(auto_rules),
            "automation_executions": len(auto_execs),
            "automation_actions": len(auto_actions)
        }

    except Exception as exc:
        await session.rollback()
        logger.error(f"Error in 200 data seeder: {exc}", exc_info=True)
        raise exc
    finally:
        if should_close:
            await session.close()

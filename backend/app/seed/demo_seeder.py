"""
DealFlow360 - Deterministic Demo Data Seeder & Showcase Scenarios (Phase 78)
===========================================================================
This module provides a reproducible, isolated, and idempotent demo data environment
for DealFlow360 presentations, customer evaluations, and architectural verification.

It provisions:
1. Demo Enterprise Tenant (`demo-enterprise`) and Isolation Tenant (`acme-global`).
2. Persona Users (Admin, Sales, Purchase, Manufacturing, Inventory, Business Owner) + Portal User.
3. Multi-Tiered Product Catalog with Raw Material Component Hierarchy.
4. Multi-Warehouse Stock Distributions with Reservation Tracking.
5. 10 End-to-End Enterprise Showcase Scenarios executed strictly via real application services:
   - Scenario 1: Healthy Sales & Revenue Cycle (Quotation -> Accepted -> Converted -> Invoiced -> Paid -> Won)
   - Scenario 2: High Discount Approval Flow (20% commercial discount -> Governance threshold -> Owner approval)
   - Scenario 3: Customer Portal Interactive Negotiation (Live comments -> Counter-discount change request -> Approval)
   - Scenario 4: Real-time Stock Availability & Shortage Detection (Zero available stock -> Shortage warning)
   - Scenario 5: Manufacturing & Component Assembly Flow (Raw material consumption -> Finished good receipt)
   - Scenario 6: Multi-Warehouse Split Delivery & Backorder Handling (Partial fulfillment from East -> Backorder fulfillment)
   - Scenario 7: Billing Milestone & Split Payment Lifecycle (Multi-item invoice -> Milestone partial payment -> Settle balance)
   - Scenario 8: Subscription Billing & Mid-Cycle Prorated Cancellation (Enterprise SaaS recurring cycle -> Proration)
   - Scenario 9: AI Telemetry & Predictive Risk Detection (Healthy vs At-risk deals -> Health telemetry scan)
   - Scenario 10: Deterministic Automation Rule & Event Triggering (High-value deal trigger -> Auto task creation)
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from typing import Dict, Any, Optional

from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.user import User
from app.models.customer import Customer
from app.models.contact import Contact
from app.models.product import Product
from app.models.pricing_rule import PricingRule
from app.models.discount_policy import DiscountPolicy
from app.models.product_recommendation_rule import ProductRecommendationRule
from app.models.warehouses import Warehouse, ProductVariant
from app.models.inventory import InventoryStock, InventoryMovement, InventoryReservation
from app.models.deal import Deal
from app.models.quotation import Quotation, QuotationItem
from app.models.quotation_state import QuotationStateHistory
from app.models.approval_rule import ApprovalRule
from app.models.quotation_approval import QuotationApproval
from app.models.approval_audit_log import ApprovalAuditLog
from app.models.quotation_line_comment import QuotationLineComment
from app.models.quotation_change_request import QuotationChangeRequest
from app.models.quotation_version import QuotationVersion
from app.models.portal_user import PortalUser
from app.models.fulfillment import Shipment, ShipmentLine, Backorder
from app.models.invoice import Invoice, InvoiceItem
from app.models.credit_note import CreditNote, CreditNoteItem
from app.models.payment import Payment
from app.models.subscription import Subscription, BillingSchedule, SubscriptionProration, SubscriptionCancellation
from app.models.activity import Activity
from app.models.automation_rule import AutomationRule
from app.models.automation_execution import AutomationExecution, AutomationExecutionAction

from app.schemas.quotation import QuotationCreate, QuotationItemCreate
from app.schemas.payments import PaymentCreateRequest
from app.schemas.subscriptions import SubscriptionCreateRequest, SubscriptionCancellationRequest
from app.schemas.negotiation import LineCommentCreate, ChangeRequestCreate
from app.schemas.automation import AutomationRuleCreate, AutomationConditionGroup, AutomationCondition, AutomationAction, EventContext

from app.services.deal_health_engine import DealHealthEngine
from app.services.stalled_quote_engine import StalledQuoteEngine
from app.services.discount_anomaly_engine import DiscountAnomalyEngine

from app.services import (
    quotations,
    quotation_state,
    approval_engine,
    invoices,
    payments,
    subscriptions,
    cancellations,
    inventory,
    reservations,
    portal_quotations,
    negotiation,
    automation_engine,
)

logger = logging.getLogger(__name__)


async def reset_demo_data(session: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """
    Safely and idempotently wipes all records belonging to demo tenants in strict dependency order.
    """
    should_close = False
    if session is None:
        session = AsyncSessionLocal()
        should_close = True

    demo_slugs = ["demo-enterprise", "acme-global", "demo-org"]

    try:
        # Find organization IDs
        stmt = select(Organization.id).where(Organization.slug.in_(demo_slugs))
        res = await session.execute(stmt)
        org_ids = list(res.scalars().all())

        if org_ids:
            logger.info(f"Purging demo data for organization IDs: {org_ids}")

            # 1. Automation Executions & Actions
            await session.execute(delete(AutomationExecutionAction).where(
                AutomationExecutionAction.execution_id.in_(
                    select(AutomationExecution.id).where(AutomationExecution.organization_id.in_(org_ids))
                )
            ))
            await session.execute(delete(AutomationExecution).where(AutomationExecution.organization_id.in_(org_ids)))
            await session.execute(delete(AutomationRule).where(AutomationRule.organization_id.in_(org_ids)))

            # 2. Portal entities & Negotiation
            await session.execute(delete(QuotationLineComment).where(QuotationLineComment.organization_id.in_(org_ids)))
            await session.execute(delete(QuotationChangeRequest).where(QuotationChangeRequest.organization_id.in_(org_ids)))
            await session.execute(delete(QuotationVersion).where(QuotationVersion.organization_id.in_(org_ids)))
            await session.execute(delete(PortalUser).where(PortalUser.organization_id.in_(org_ids)))

            # 3. Payments, Credit Notes & Invoices
            await session.execute(delete(Payment).where(Payment.organization_id.in_(org_ids)))
            await session.execute(delete(CreditNoteItem).where(CreditNoteItem.organization_id.in_(org_ids)))
            await session.execute(delete(CreditNote).where(CreditNote.organization_id.in_(org_ids)))
            await session.execute(delete(InvoiceItem).where(InvoiceItem.organization_id.in_(org_ids)))
            await session.execute(delete(Invoice).where(Invoice.organization_id.in_(org_ids)))

            # 4. Subscriptions
            await session.execute(delete(SubscriptionCancellation).where(SubscriptionCancellation.organization_id.in_(org_ids)))
            await session.execute(delete(SubscriptionProration).where(SubscriptionProration.organization_id.in_(org_ids)))
            await session.execute(delete(BillingSchedule).where(BillingSchedule.organization_id.in_(org_ids)))
            await session.execute(delete(Subscription).where(Subscription.organization_id.in_(org_ids)))

            # 5. Shipments & Backorders
            await session.execute(delete(ShipmentLine).where(ShipmentLine.organization_id.in_(org_ids)))
            await session.execute(delete(Shipment).where(Shipment.organization_id.in_(org_ids)))
            await session.execute(delete(Backorder).where(Backorder.organization_id.in_(org_ids)))

            # 6. Approvals & Rules
            await session.execute(delete(ApprovalAuditLog).where(ApprovalAuditLog.organization_id.in_(org_ids)))
            await session.execute(delete(QuotationApproval).where(QuotationApproval.organization_id.in_(org_ids)))
            await session.execute(delete(ApprovalRule).where(ApprovalRule.organization_id.in_(org_ids)))

            # 7. Inventory
            await session.execute(delete(InventoryReservation).where(InventoryReservation.organization_id.in_(org_ids)))
            await session.execute(delete(InventoryMovement).where(InventoryMovement.organization_id.in_(org_ids)))
            await session.execute(delete(InventoryStock).where(InventoryStock.organization_id.in_(org_ids)))

            # 8. Quotations
            await session.execute(delete(QuotationStateHistory).where(QuotationStateHistory.organization_id.in_(org_ids)))
            await session.execute(delete(QuotationItem).where(
                QuotationItem.quotation_id.in_(
                    select(Quotation.id).where(Quotation.organization_id.in_(org_ids))
                )
            ))
            await session.execute(delete(Quotation).where(Quotation.organization_id.in_(org_ids)))

            # 9. Activities & Deals
            await session.execute(delete(Activity).where(Activity.organization_id.in_(org_ids)))
            await session.execute(delete(Deal).where(Deal.organization_id.in_(org_ids)))

            # 10. Contacts & Customers
            await session.execute(delete(Contact).where(Contact.organization_id.in_(org_ids)))
            await session.execute(delete(Customer).where(Customer.organization_id.in_(org_ids)))

            # 11. Pricing Rules, Discount Policies, Recommendation Rules
            await session.execute(delete(PricingRule).where(PricingRule.organization_id.in_(org_ids)))
            await session.execute(delete(DiscountPolicy).where(DiscountPolicy.organization_id.in_(org_ids)))
            await session.execute(delete(ProductRecommendationRule).where(ProductRecommendationRule.organization_id.in_(org_ids)))

            # 12. Products & Variants & Warehouses
            await session.execute(delete(ProductVariant).where(
                ProductVariant.product_id.in_(
                    select(Product.id).where(Product.organization_id.in_(org_ids))
                )
            ))
            await session.execute(delete(Product).where(Product.organization_id.in_(org_ids)))
            await session.execute(delete(Warehouse).where(Warehouse.organization_id.in_(org_ids)))

            # 13. Users
            await session.execute(delete(User).where(User.organization_id.in_(org_ids)))

            # 14. Organizations
            await session.execute(delete(Organization).where(Organization.id.in_(org_ids)))

            await session.commit()
            logger.info("Demo data reset completed successfully.")

        return {"status": "success", "purged_organizations": len(org_ids)}

    except Exception as e:
        await session.rollback()
        logger.error(f"Error during demo data reset: {e}", exc_info=True)
        raise e
    finally:
        if should_close:
            await session.close()


async def seed_demo_data(session: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """
    Provisions a comprehensive, realistic demo environment and executes 10 controlled showcase scenarios.
    """
    should_close = False
    if session is None:
        session = AsyncSessionLocal()
        should_close = True

    try:
        # First reset existing demo data
        await reset_demo_data(session)

        now = datetime.now(timezone.utc)
        db = session

        # =========================================================================
        # 1. ORGANIZATIONS (Demo Tenant + Tenant Isolation Org)
        # =========================================================================
        org_demo = Organization(
            id=uuid.uuid4(),
            name="DealFlow360 Demo Enterprise",
            slug="demo-enterprise",
            is_active=True
        )
        org_acme = Organization(
            id=uuid.uuid4(),
            name="Acme Global Systems",
            slug="acme-global",
            is_active=True
        )
        db.add_all([org_demo, org_acme])
        await db.commit()

        # =========================================================================
        # 2. USERS (Roles & Personas)
        # =========================================================================
        users_def = [
            ("Admin User", "admin_demo-enterprise@dealflow360.com", True, org_demo.id, "admin"),
            ("Sarah Jenkins", "sales_demo-enterprise@dealflow360.com", False, org_demo.id, "sales"),
            ("Ian Wright", "inventory_demo-enterprise@dealflow360.com", False, org_demo.id, "inventory"),
            ("Billing Controller", "billing_demo-enterprise@dealflow360.com", False, org_demo.id, "billing"),
            ("Admin User (Legacy)", "admin@dealflow.demo", True, org_demo.id, "admin_legacy"),
            ("Sarah Jenkins (Legacy)", "sales@dealflow.demo", False, org_demo.id, "sales_legacy"),
            ("Paul Miller", "purchase@dealflow.demo", False, org_demo.id, "purchase"),
            ("Mark Davis", "manufacturing@dealflow.demo", False, org_demo.id, "manufacturing"),
            ("Ian Wright (Legacy)", "inventory@dealflow.demo", False, org_demo.id, "inventory_legacy"),
            ("Robert Vance", "owner@dealflow.demo", True, org_demo.id, "business_owner"),
            ("Acme Sales Rep", "rep@acme.demo", False, org_acme.id, "sales_acme"),
        ]
        users: Dict[str, User] = {}
        for full_name, email, is_admin, o_id, key in users_def:
            u = User(
                id=uuid.uuid4(),
                organization_id=o_id,
                email=email,
                full_name=full_name,
                password_hash=get_password_hash("DemoPass123!"),
                is_admin=is_admin,
                is_active=True
            )
            db.add(u)
            if o_id == org_demo.id:
                users[key] = u

        await db.commit()

        # =========================================================================
        # 3. CUSTOMERS & CONTACTS
        # =========================================================================
        customers_def = [
            ("Nova Living Concepts", "orders@novaliving.com", "+1-555-0101", "New York", "USA"),
            ("Apex Hospitality Group", "procurement@apexhospitality.com", "+1-555-0102", "Chicago", "USA"),
            ("Horizon Tech Labs", "hardware@horizontech.io", "+1-555-0103", "San Francisco", "USA"),
            ("Starlight Healthcare Systems", "facilities@starlighthealth.org", "+1-555-0104", "Boston", "USA"),
            ("Cyberdyne Systems", "procure@cyberdyne.net", "+1-555-0105", "Austin", "USA"),
        ]
        customers: Dict[str, Customer] = {}
        contacts: Dict[str, Contact] = {}

        for name, email, phone, city, country in customers_def:
            c = Customer(
                id=uuid.uuid4(),
                organization_id=org_demo.id,
                name=name,
                email=email,
                phone=phone,
                city=city,
                country=country,
                is_active=True
            )
            db.add(c)
            key = name.split()[0].lower()
            customers[key] = c

        await db.commit()

        # Contacts for Customers
        c_nova = Contact(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            customer_id=customers["nova"].id,
            first_name="Elena",
            last_name="Rostova",
            email="elena@novaliving.com",
            phone="+1-555-0111",
            is_primary=True
        )
        c_apex = Contact(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            customer_id=customers["apex"].id,
            first_name="Marcus",
            last_name="Vance",
            email="marcus@apexhospitality.com",
            phone="+1-555-0112",
            is_primary=True
        )
        c_horizon = Contact(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            customer_id=customers["horizon"].id,
            first_name="Sarah",
            last_name="Lin",
            email="slin@horizontech.io",
            phone="+1-555-0113",
            is_primary=True
        )
        c_starlight = Contact(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            customer_id=customers["starlight"].id,
            first_name="Julian",
            last_name="Hayes",
            email="jhayes@starlighthealth.org",
            phone="+1-555-0114",
            is_primary=True
        )
        db.add_all([c_nova, c_apex, c_horizon, c_starlight])
        contacts["nova_elena"] = c_nova
        contacts["apex_marcus"] = c_apex
        contacts["horizon_sarah"] = c_horizon
        contacts["starlight_julian"] = c_starlight

        # Portal User for Customer Portal showcase
        portal_user = PortalUser(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            customer_id=customers["nova"].id,
            email="portal@novafurniture.demo",
            full_name="Elena Rostova (Portal)",
            hashed_password=get_password_hash("PortalDemo123!"),
            is_active=True
        )
        db.add(portal_user)
        await db.commit()

        # =========================================================================
        # 4. PRODUCTS & VARIANTS
        # =========================================================================
        products_def = [
            ("Executive Standing Desk", "PROD-DSK-001", Decimal("1250.00"), Decimal("650.00")),
            ("Ergonomic Mesh Chair", "PROD-CHR-002", Decimal("450.00"), Decimal("210.00")),
            ("Acoustic Meeting Pod", "PROD-POD-003", Decimal("4800.00"), Decimal("2400.00")),
            ("Conference Table 10-Seater", "PROD-TBL-004", Decimal("2500.00"), Decimal("1100.00")),
            ("Modular Credenza 4-Door", "PROD-CRD-005", Decimal("850.00"), Decimal("380.00")),
            ("DealFlow Enterprise SaaS Plan", "SAAS-ENT-001", Decimal("2000.00"), Decimal("150.00")),
            ("Premium Walnut Slab", "RAW-WNT-001", Decimal("350.00"), Decimal("180.00")),
            ("Heavy-Duty Steel Pod Frame", "RAW-FRM-002", Decimal("800.00"), Decimal("420.00")),
            ("Assembly Fastener Kit", "RAW-FST-003", Decimal("45.00"), Decimal("18.00")),
        ]

        sku_map = {
            "PROD-DSK-001": "desk",
            "PROD-CHR-002": "chair",
            "PROD-POD-003": "pod",
            "PROD-TBL-004": "table",
            "PROD-CRD-005": "credenza",
            "SAAS-ENT-001": "saas",
            "RAW-WNT-001": "raw_slab",
            "RAW-FRM-002": "raw_frame",
            "RAW-FST-003": "raw_fastener",
        }

        products: Dict[str, Product] = {}
        for name, sku, price, cost in products_def:
            p = Product(
                id=uuid.uuid4(),
                organization_id=org_demo.id,
                sku=sku,
                name=name,
                description=f"Enterprise grade {name}",
                unit_price=price,
                unit_cost=cost,
                currency="USD",
                is_active=True
            )
            db.add(p)
            if sku in sku_map:
                products[sku_map[sku]] = p

        await db.commit()

        # =========================================================================
        # 5. WAREHOUSES & INITIAL STOCK DISTRIBUTION
        # =========================================================================
        wh_main = Warehouse(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            code="W-MAIN",
            name="Main Distribution Center",
            address="100 Logistics Blvd, Newark, NJ",
            is_active=True
        )
        wh_east = Warehouse(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            code="W-EAST",
            name="East Coast Regional Hub",
            address="500 Industrial Pkwy, Scranton, PA",
            is_active=True
        )
        wh_west = Warehouse(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            code="W-REGIONAL",
            name="Midwest Fulfillment Center",
            address="300 Cargo Way, Columbus, OH",
            is_active=True
        )
        db.add_all([wh_main, wh_east, wh_west])
        await db.commit()

        warehouses = {"main": wh_main, "east": wh_east, "west": wh_west}

        # Seed initial stock
        stock_allocations = [
            (wh_main, products["desk"], 25, 5, 20),
            (wh_east, products["desk"], 15, 0, 15),
            (wh_main, products["chair"], 8, 0, 8),
            (wh_east, products["chair"], 35, 0, 35),
            (wh_main, products["pod"], 0, 0, 0),       # Intentionally zero for MTO/Shortage scenario
            (wh_main, products["table"], 10, 2, 8),
            (wh_main, products["credenza"], 18, 0, 18),
            (wh_main, products["raw_slab"], 40, 0, 40),
            (wh_main, products["raw_frame"], 20, 0, 20),
            (wh_main, products["raw_fastener"], 100, 0, 100),
        ]

        for wh, prod, on_hand, res_qty, avail in stock_allocations:
            st = InventoryStock(
                id=uuid.uuid4(),
                organization_id=org_demo.id,
                warehouse_id=wh.id,
                product_id=prod.id,
                location_code="AISLE-A1",
                on_hand_quantity=on_hand,
                reserved_quantity=res_qty,
                available_quantity=avail
            )
            db.add(st)
        await db.commit()

        # =========================================================================
        # SHOWCASE SCENARIO 1: Healthy Sales Cycle (Converted -> Invoiced -> Paid)
        # =========================================================================
        d1 = Deal(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            customer_id=customers["horizon"].id,
            contact_id=contacts["horizon_sarah"].id,
            deal_number="DEAL-2026-000001",
            title="Horizon Labs Engineering Expansion",
            stage="negotiation",
            status="open",
            value=Decimal("15250.00"),
            probability=90,
            expected_close_date=now.date() + timedelta(days=7)
        )
        db.add(d1)
        await db.commit()

        q1_payload = QuotationCreate(
            customer_id=customers["horizon"].id,
            contact_id=contacts["horizon_sarah"].id,
            deal_id=d1.id,
            currency="USD",
            notes="Standard commercial order for 10x Standing Desks & 6x Chairs.",
            terms="Net 30. Standard commercial delivery.",
            items=[
                QuotationItemCreate(
                    product_id=products["desk"].id,
                    quantity=Decimal("10.00"),
                    unit_price=Decimal("1250.00"),
                    discount_percent=Decimal("5.00")
                ),
                QuotationItemCreate(
                    product_id=products["chair"].id,
                    quantity=Decimal("6.00"),
                    unit_price=Decimal("450.00"),
                    discount_percent=Decimal("0.00")
                )
            ]
        )
        q1 = await quotations.create_quotation(db, org_demo.id, q1_payload, users["sales"].id)
        q1 = await quotation_state.transition_quotation(db, org_demo.id, q1.id, "sent", current_user_id=users["sales"].id)
        q1 = await quotation_state.transition_quotation(db, org_demo.id, q1.id, "accepted", current_user_id=users["sales"].id)
        q1 = await quotation_state.transition_quotation(db, org_demo.id, q1.id, "converted", current_user_id=users["sales"].id)

        # Generate Invoice & Settle Full Payment
        inv1 = await invoices.create_invoice_from_quotation(db, org_demo.id, q1.id)
        inv1 = await invoices.issue_invoice(db, org_demo.id, inv1.id)
        pay1_req = PaymentCreateRequest(
            invoice_id=inv1.id,
            amount=inv1.total,
            method="BANK_TRANSFER",
            notes="Full settlement wire"
        )
        await payments.record_payment(db, org_demo.id, pay1_req, current_user=users["sales"])
        await db.commit()

        # =========================================================================
        # SHOWCASE SCENARIO 2: High Discount Approval Flow (Governance & Margin Protection)
        # =========================================================================
        # Create an ApprovalRule for high discount (>15%)
        app_rule = ApprovalRule(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            name="High Commercial Discount Rule (>15%)",
            is_active=True,
            priority=1,
            min_discount_percent=Decimal("15.00"),
            approval_level=1
        )
        db.add(app_rule)
        await db.commit()

        q2_payload = QuotationCreate(
            customer_id=customers["cyberdyne"].id,
            currency="USD",
            notes="Cyberdyne bulk workstation procurement. Requires 20% executive discount.",
            items=[
                QuotationItemCreate(
                    product_id=products["desk"].id,
                    quantity=Decimal("20.00"),
                    unit_price=Decimal("1250.00"),
                    discount_percent=Decimal("20.00")
                )
            ]
        )
        q2 = await quotations.create_quotation(db, org_demo.id, q2_payload, users["sales"].id)
        
        # Submit approval request
        approval_obj = QuotationApproval(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            quotation_id=q2.id,
            approval_rule_id=app_rule.id,
            requested_by_user_id=users["sales"].id,
            status="PENDING",
            approval_level=1,
            reasons="Discount 20.00% exceeds policy threshold of 15.00%"
        )
        db.add(approval_obj)
        await db.commit()

        # Owner records decision
        await approval_engine.record_approval_decision(
            db, org_demo.id, q2.id,
            current_user=users["business_owner"],
            decision="APPROVED",
            note="Approved subject to 50% advance payment terms."
        )
        await db.commit()

        # =========================================================================
        # SHOWCASE SCENARIO 3: Customer Portal Negotiation & Interaction
        # =========================================================================
        d3 = Deal(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            customer_id=customers["nova"].id,
            contact_id=contacts["nova_elena"].id,
            deal_number="DEAL-2026-000002",
            title="Nova Manhattan Studio Outfitting",
            stage="proposal",
            status="open",
            value=Decimal("8500.00"),
            probability=80,
            expected_close_date=now.date() + timedelta(days=10)
        )
        db.add(d3)
        await db.commit()

        q3_payload = QuotationCreate(
            customer_id=customers["nova"].id,
            contact_id=contacts["nova_elena"].id,
            deal_id=d3.id,
            currency="USD",
            notes="Nova executive studio desks and credenzas.",
            items=[
                QuotationItemCreate(
                    product_id=products["desk"].id,
                    quantity=Decimal("4.00"),
                    unit_price=Decimal("1250.00"),
                    discount_percent=Decimal("0.00")
                ),
                QuotationItemCreate(
                    product_id=products["credenza"].id,
                    quantity=Decimal("4.00"),
                    unit_price=Decimal("850.00"),
                    discount_percent=Decimal("0.00")
                )
            ]
        )
        q3 = await quotations.create_quotation(db, org_demo.id, q3_payload, users["sales"].id)
        q3 = await quotation_state.transition_quotation(db, org_demo.id, q3.id, "sent", current_user_id=users["sales"].id)

        # Portal interaction: add comment and request counter-discount
        q3_items = (await db.execute(select(QuotationItem).where(QuotationItem.quotation_id == q3.id))).scalars().all()
        target_item = q3_items[0]

        await negotiation.create_line_comment(
            db, org_demo.id, q3.id,
            LineCommentCreate(
                quotation_item_id=target_item.id,
                comment_text="Could we get a 10% discount on the executive desks for our showroom?"
            ),
            author_portal_user=portal_user
        )
        await negotiation.create_change_request(
            db, portal_user, q3.id,
            ChangeRequestCreate(
                quotation_item_id=target_item.id,
                change_type="counter_discount",
                requested_discount_percent=Decimal("10.00"),
                request_details="Requesting 10% discount across all desk units."
            )
        )
        # Portal customer accepts
        await portal_quotations.accept_portal_quotation(db, portal_user, q3.id, reason="Approved terms after discussion")
        await db.commit()

        # =========================================================================
        # SHOWCASE SCENARIO 4: Inventory Shortage & Operational Alert
        # =========================================================================
        q4_payload = QuotationCreate(
            customer_id=customers["starlight"].id,
            contact_id=contacts["starlight_julian"].id,
            currency="USD",
            notes="Starlight Clinic quiet pod installation (MTO Shortage).",
            items=[
                QuotationItemCreate(
                    product_id=products["pod"].id,
                    quantity=Decimal("2.00"),
                    unit_price=Decimal("4800.00"),
                    discount_percent=Decimal("0.00")
                )
            ]
        )
        q4 = await quotations.create_quotation(db, org_demo.id, q4_payload, users["sales"].id)
        # Check stock availability -> 0 available
        await inventory.calculate_quotation_availability(db, org_demo.id, q4.id)

        # =========================================================================
        # SHOWCASE SCENARIO 5: Manufacturing / Assembly Flow
        # =========================================================================
        # Consume raw materials to assemble 2 Meeting Pods
        for raw_item, qty in [(products["raw_slab"], 2), (products["raw_frame"], 2), (products["raw_fastener"], 4)]:
            st_raw_q = await db.execute(select(InventoryStock).where(InventoryStock.warehouse_id == warehouses["main"].id, InventoryStock.product_id == raw_item.id))
            st_raw = st_raw_q.scalar_one()
            st_raw.on_hand_quantity -= qty
            st_raw.available_quantity -= qty
            mv_out = InventoryMovement(
                id=uuid.uuid4(),
                organization_id=org_demo.id,
                warehouse_id=warehouses["main"].id,
                product_id=raw_item.id,
                movement_type="CONSUMPTION",
                quantity=-qty,
                reference_type="MANUAL",
                notes=f"Raw material consumed for 2x {products['pod'].name} assembly"
            )
            db.add(mv_out)

        # Receive 2 assembled finished Meeting Pods into Main Warehouse
        st_pod_q = await db.execute(select(InventoryStock).where(InventoryStock.warehouse_id == warehouses["main"].id, InventoryStock.product_id == products["pod"].id))
        st_pod = st_pod_q.scalar_one()
        st_pod.on_hand_quantity += 2
        st_pod.available_quantity += 2
        mv_in = InventoryMovement(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            warehouse_id=warehouses["main"].id,
            product_id=products["pod"].id,
            movement_type="RECEIPT",
            quantity=2,
            reference_type="MANUAL",
            notes="Finished goods receipt from Shop Floor assembly"
        )
        db.add(mv_in)
        await db.commit()

        # =========================================================================
        # SHOWCASE SCENARIO 6: Partial Delivery & Backorder Flow
        # =========================================================================
        # Order 20 Chairs (8 in Main, 12 in East)
        q6_payload = QuotationCreate(
            customer_id=customers["nova"].id,
            contact_id=contacts["nova_elena"].id,
            currency="USD",
            notes="Nova showroom 20-chair order with multi-warehouse split delivery.",
            items=[
                QuotationItemCreate(
                    product_id=products["chair"].id,
                    quantity=Decimal("20.00"),
                    unit_price=Decimal("450.00"),
                    discount_percent=Decimal("0.00")
                )
            ]
        )
        q6 = await quotations.create_quotation(db, org_demo.id, q6_payload, users["sales"].id)
        q6 = await quotation_state.transition_quotation(db, org_demo.id, q6.id, "sent", current_user_id=users["sales"].id)
        q6 = await quotation_state.transition_quotation(db, org_demo.id, q6.id, "accepted", current_user_id=users["sales"].id)
        q6 = await quotation_state.transition_quotation(db, org_demo.id, q6.id, "converted", current_user_id=users["sales"].id)

        # Reserve initial 8 units in Main Warehouse
        await reservations.reserve_stock_for_quotation(db, org_demo.id, q6.id, actor_id=users["inventory"].id, actor_name=users["inventory"].full_name)

        q6_items = (await db.execute(select(QuotationItem).where(QuotationItem.quotation_id == q6.id))).scalars().all()
        q6_chair_item = q6_items[0]

        # Shipment 1: 8 chairs from Main Warehouse
        shp1 = Shipment(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            quotation_id=q6.id,
            warehouse_id=warehouses["main"].id,
            shipment_number="SHP-2026-000001",
            status="DELIVERED",
            carrier="FedEx Freight",
            tracking_number="TRK-881920-MAIN",
            shipped_at=now - timedelta(days=2),
            actual_delivery_date=(now - timedelta(days=1)).date()
        )
        db.add(shp1)
        db.add(ShipmentLine(id=uuid.uuid4(), organization_id=org_demo.id, shipment_id=shp1.id, quotation_item_id=q6_chair_item.id, product_id=products["chair"].id, quantity=8))

        # Backorder for remaining 12 chairs
        bko1 = Backorder(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            quotation_id=q6.id,
            quotation_item_id=q6_chair_item.id,
            customer_id=customers["nova"].id,
            product_id=products["chair"].id,
            backorder_number="BKO-2026-000001",
            status="FULFILLED",
            requested_quantity=20,
            fulfilled_quantity=20,
            remaining_quantity=0,
            warehouse_id=warehouses["east"].id
        )
        db.add(bko1)

        # Shipment 2: 12 chairs fulfilled from East Hub transfer
        shp2 = Shipment(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            quotation_id=q6.id,
            warehouse_id=warehouses["east"].id,
            shipment_number="SHP-2026-000002",
            status="DELIVERED",
            carrier="DHL Express",
            tracking_number="TRK-881921-EAST",
            shipped_at=now - timedelta(days=1),
            actual_delivery_date=now.date()
        )
        db.add(shp2)
        db.add(ShipmentLine(id=uuid.uuid4(), organization_id=org_demo.id, shipment_id=shp2.id, quotation_item_id=q6_chair_item.id, product_id=products["chair"].id, quantity=12))
        await db.commit()

        # =========================================================================
        # SHOWCASE SCENARIO 7: Billing & Payment Lifecycle
        # =========================================================================
        q7_payload = QuotationCreate(
            customer_id=customers["apex"].id,
            contact_id=contacts["apex_marcus"].id,
            currency="USD",
            notes="Apex conference tables order with milestone payments.",
            items=[
                QuotationItemCreate(
                    product_id=products["table"].id,
                    quantity=Decimal("2.00"),
                    unit_price=Decimal("2500.00"),
                    discount_percent=Decimal("0.00")
                ),
                QuotationItemCreate(
                    product_id=products["credenza"].id,
                    quantity=Decimal("2.00"),
                    unit_price=Decimal("850.00"),
                    discount_percent=Decimal("0.00")
                )
            ]
        )
        q7 = await quotations.create_quotation(db, org_demo.id, q7_payload, users["sales"].id)
        q7 = await quotation_state.transition_quotation(db, org_demo.id, q7.id, "sent", current_user_id=users["sales"].id)
        q7 = await quotation_state.transition_quotation(db, org_demo.id, q7.id, "accepted", current_user_id=users["sales"].id)
        q7 = await quotation_state.transition_quotation(db, org_demo.id, q7.id, "converted", current_user_id=users["sales"].id)

        inv7 = await invoices.create_invoice_from_quotation(db, org_demo.id, q7.id)
        inv7 = await invoices.issue_invoice(db, org_demo.id, inv7.id)
        # Payment 1: Partial $3,000
        pay7_1 = PaymentCreateRequest(
            invoice_id=inv7.id,
            amount=Decimal("3000.00"),
            method="CARD",
            notes="Partial milestone deposit"
        )
        await payments.record_payment(db, org_demo.id, pay7_1, current_user=users["sales"])

        # Payment 2: Remaining balance
        inv7_updated = await db.get(Invoice, inv7.id)
        pay7_2 = PaymentCreateRequest(
            invoice_id=inv7.id,
            amount=inv7_updated.amount_due,
            method="BANK_TRANSFER",
            notes="Final settlement wire"
        )
        await payments.record_payment(db, org_demo.id, pay7_2, current_user=users["sales"])
        await db.commit()

        # =========================================================================
        # SHOWCASE SCENARIO 8: Subscription Billing & Proration
        # =========================================================================
        # Sub 1: Active Monthly SaaS Plan (Apex Hospitality)
        sub_req_apex = SubscriptionCreateRequest(
            customer_id=customers["apex"].id,
            product_id=products["saas"].id,
            plan_name="DealFlow360 Enterprise SaaS Subscription",
            billing_interval="MONTHLY",
            quantity=Decimal("5.00"),
            unit_price=Decimal("12500.00"),
            start_date=now.date() - timedelta(days=90)
        )
        sub_apex = await subscriptions.create_subscription(db, org_demo.id, sub_req_apex)
        sub_apex.next_billing_date = now.date() - timedelta(days=2)  # Due for billing schedule generation
        
        # Sub 2: Active Quarterly Infrastructure Hosting (Horizon Tech)
        sub_req_horizon = SubscriptionCreateRequest(
            customer_id=customers["horizon"].id,
            product_id=products["pod"].id,
            plan_name="High-Performance Acoustic Pod Managed Service",
            billing_interval="QUARTERLY",
            quantity=Decimal("2.00"),
            unit_price=Decimal("45000.00"),
            start_date=now.date() - timedelta(days=120)
        )
        sub_horizon = await subscriptions.create_subscription(db, org_demo.id, sub_req_horizon)
        sub_horizon.next_billing_date = now.date() - timedelta(days=1)

        # Sub 3: Active Monthly Support SLA (Starlight Healthcare)
        sub_req_starlight = SubscriptionCreateRequest(
            customer_id=customers["starlight"].id,
            product_id=products["saas"].id,
            plan_name="24/7 Platinum SLA & Dedicated TAM Support",
            billing_interval="MONTHLY",
            quantity=Decimal("1.00"),
            unit_price=Decimal("8500.00"),
            start_date=now.date() - timedelta(days=30)
        )
        await subscriptions.create_subscription(db, org_demo.id, sub_req_starlight)

        # Sub 4: Historic Cancelled Plan (Nova Living)
        sub_req = SubscriptionCreateRequest(
            customer_id=customers["nova"].id,
            product_id=products["saas"].id,
            plan_name="DealFlow Legacy Starter Plan",
            billing_interval="MONTHLY",
            quantity=Decimal("1.00"),
            unit_price=Decimal("2000.00"),
            start_date=now.date() - timedelta(days=60)
        )
        sub8 = await subscriptions.create_subscription(db, org_demo.id, sub_req)
        # Cancel subscription mid-cycle
        cancel_req = SubscriptionCancellationRequest(
            cancellation_type="IMMEDIATE",
            reason="Re-evaluating internal software budgets for Q4",
            notes="Cancelled mid-cycle"
        )
        await cancellations.cancel_subscription(
            db, org_demo.id, sub8.id,
            payload=cancel_req,
            current_user=users["sales"]
        )
        await db.commit()

        # =========================================================================
        # SHOWCASE SCENARIO 9: Deal Health & Telemetry Anomaly Detection
        # =========================================================================
        # Healthy Deal (Score ~85)
        d_healthy = Deal(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            customer_id=customers["nova"].id,
            contact_id=contacts["nova_elena"].id,
            deal_number="DEAL-2026-000003",
            title="Nova Q4 Showroom Furnishing",
            stage="proposal",
            status="open",
            value=Decimal("45000.00"),
            probability=75,
            expected_close_date=now.date() + timedelta(days=14)
        )
        # At-Risk Deal (Stalled, low activity)
        d_at_risk = Deal(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            customer_id=customers["starlight"].id,
            contact_id=contacts["starlight_julian"].id,
            deal_number="DEAL-2026-000004",
            title="Starlight Medical Wing Outfitting",
            stage="qualified",
            status="open",
            value=Decimal("68000.00"),
            probability=25,
            expected_close_date=now.date() + timedelta(days=30)
        )
        db.add_all([d_healthy, d_at_risk])
        await db.commit()

        # Activities for Healthy vs At-Risk
        act_healthy = Activity(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            customer_id=customers["nova"].id,
            deal_id=d_healthy.id,
            created_by_user_id=users["sales"].id,
            assigned_to_user_id=users["sales"].id,
            activity_type="meeting",
            title="Executive showroom design review",
            status="completed",
            priority="high",
            due_at=now - timedelta(days=1)
        )
        act_at_risk = Activity(
            id=uuid.uuid4(),
            organization_id=org_demo.id,
            customer_id=customers["starlight"].id,
            deal_id=d_at_risk.id,
            created_by_user_id=users["sales"].id,
            assigned_to_user_id=users["sales"].id,
            activity_type="call",
            title="Stalled follow-up on clinic budget",
            status="pending",
            priority="urgent",
            due_at=now - timedelta(days=18) # Stale overdue
        )
        db.add_all([act_healthy, act_at_risk])
        await db.commit()

        # Evaluate Deal Health & Telemetry Scans
        await DealHealthEngine.evaluate_deal_health(db, org_demo.id, d_healthy.id)
        await DealHealthEngine.evaluate_deal_health(db, org_demo.id, d_at_risk.id)
        await StalledQuoteEngine.detect_stalled_quotes(db, org_demo.id)
        await DiscountAnomalyEngine.monitor_discount_anomalies(db, org_demo.id)
        await db.commit()

        # =========================================================================
        # SHOWCASE SCENARIO 10: AI Advisory & Deterministic Automation
        # =========================================================================
        rule_payload = AutomationRuleCreate(
            name="High-Value Deal Executive Notification",
            trigger_type="DEAL_CREATED",
            priority=100,
            conditions=AutomationConditionGroup(
                logical_operator="AND",
                conditions=[
                    AutomationCondition(field="deal.value", operator="greater_than_or_equal", value=50000.0)
                ]
            ),
            actions=[
                AutomationAction(
                    action_type="CREATE_ACTIVITY",
                    parameters={
                        "title": "Executive Sponsor Outreach - High Value Deal",
                        "activity_type": "task",
                        "priority": "urgent",
                        "due_in_days": 2
                    }
                )
            ]
        )
        auto_rule = await automation_engine.create_automation_rule(db, org_demo.id, users["admin"].id, rule_payload)
        await automation_engine.set_rule_status(db, org_demo.id, users["admin"].id, auto_rule.id, "ACTIVE")

        # Trigger Automation Event for a $68,000 deal
        await automation_engine.evaluate_event_triggers(
            db, org_demo.id,
            EventContext(
                organization_id=org_demo.id,
                event_type="DEAL_CREATED",
                entity_type="deal",
                entity_id=d_at_risk.id,
                actor_user_id=users["sales"].id,
                payload={
                    "deal": {
                        "id": str(d_at_risk.id),
                        "value": 68000.0,
                        "title": d_at_risk.title,
                        "customer_id": str(customers["starlight"].id)
                    }
                }
            )
        )
        await db.commit()

        # Final commit and success confirmation
        await db.commit()
        return {
            "status": "success",
            "demo_organization": org_demo.name,
            "demo_slug": org_demo.slug,
            "users_created": len(users),
            "customers_created": len(customers),
            "products_created": len(products),
            "warehouses_created": len(warehouses),
            "scenarios_executed": 10
        }

    except Exception as e:
        await session.rollback()
        logger.error(f"Error during demo data seeding: {e}", exc_info=True)
        raise e
    finally:
        if should_close:
            await session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = asyncio.run(seed_demo_data())
    print("Demo Data Seeder Finished Successfully:", res)

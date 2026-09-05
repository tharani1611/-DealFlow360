"""
DealFlow360 — Resized Medium-Volume Bulk Data Seeder & Analytics Dataset (~3,500 Records)
======================================================================================
This module generates a rich, realistic, interconnected, and deterministic dataset
containing approximately 100–200 records for major business entities (customers: 120,
products: 120, deals: 120, quotations: 120) under the dedicated tenant:
'DealFlow360 Analytics Lab' (`bulk-data-lab`).

It exercises the complete commercial lifecycle:
- 2 Tenants (Primary Analytics Lab + Secondary Isolation Testing Lab)
- 20 Persona & Staff Users + 20 Portal Users
- 120 B2B Customers & ~180 Customer Contacts
- 120 Products (Office Furniture, Equipment, Hospitality, Software, Services, Components)
- 240 Product Variants
- 10 Regional Warehouses
- 100 Pricing Rules (Contract, Volume, Tiered, Promotional)
- 60 Discount Governance Policies
- 80 Product Upsell/Cross-sell Recommendation Rules
- 4 Multi-tier Approval Rules
- 120 Sales Deals
- 120 Quotations with ~360 Line Items (Exact Decimal precision calculations)
- 120 Quotation State History Audit Logs
- ~35 Quotation Approval Requests & Audit Logs
- ~40 Negotiation Comments & ~40 Counter-Discount Change Requests
- 120 Quotation Snapshot Versions
- ~125 Warehouse Item Allocations & 120 Commercial Billing Classifications
- ~360 Multi-Warehouse Stock Distributions & ~360 Stock Movements
- ~125 Stock Reservations
- ~50 Physical Shipments & ~125 Shipment Line Items
- ~10 Backorder Shortfall Records & ~50 Delivery Promise SLA Trackers
- ~50 Invoices & ~125 Invoice Line Items
- ~40 Completed Payments
- ~5 Credit Notes & Items, ~5 Payment Cash Refunds
- ~30 Recurring Subscriptions & ~120 Billing Schedules
- ~6 Subscription Cancellation Audits
- 120 Deal Health Historical Snapshots & ~35 Anomaly Monitoring Events
- ~35 Nudges & Transition Histories
- 120 CRM Activities
- 5 Automation Workflow Rules & 80 Executions & 80 Action Logs
"""

import asyncio
import hashlib
import logging
import random
import uuid
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple

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
from app.models.fulfillment import (
    WarehouseAllocation,
    Shipment,
    ShipmentLine,
    Backorder,
    DeliveryPromise,
    BillingClassification,
    FulfillmentOverrideAudit,
)
from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import Payment
from app.models.credit_note import CreditNote, CreditNoteItem, PaymentRefund
from app.models.subscription import (
    Subscription,
    BillingSchedule,
    SubscriptionProration,
    SubscriptionCancellation,
)
from app.models.deal_health import DealHealthSnapshot
from app.models.monitoring_event import MonitoringEvent
from app.models.nudge import Nudge, NudgeHistory
from app.models.activity import Activity
from app.models.automation_rule import AutomationRule
from app.models.automation_execution import AutomationExecution, AutomationExecutionAction

logger = logging.getLogger("dealflow360.bulk_seeder")

BULK_ORG_SLUG = "bulk-data-lab"
BULK_ORG_NAME = "DealFlow360 Analytics Lab"
BULK_ISOLATION_SLUG = "bulk-isolation-lab"
BULK_ISOLATION_NAME = "DealFlow360 Isolation Testing Lab"

TARGET_BULK_SLUGS = [BULK_ORG_SLUG, BULK_ISOLATION_SLUG]

DEFAULT_BULK_CONFIG: Dict[str, Any] = {
    "customers": 120,
    "products": 120,
    "deals": 120,
    "quotations": 120,
    "portal_users": 20,
    "pricing_rules": 100,
    "discount_policies": 60,
    "recommendation_rules": 80,
    "activities": 120,
    "automation_executions": 80,
}


def _d(val: Any) -> Decimal:
    """Helper to convert to 2-decimal rounded Decimal."""
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def reset_bulk_data(
    session: Optional[AsyncSession] = None,
    target_slugs: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Safely and idempotently wipes all records belonging strictly to bulk dataset tenants:
    - 'bulk-data-lab'
    - 'bulk-isolation-lab'
    Preserves 'demo-enterprise', 'acme-global', and all other tenants intact.
    """
    should_close = False
    if session is None:
        session = AsyncSessionLocal()
        should_close = True

    slugs_to_purge = target_slugs or TARGET_BULK_SLUGS

    try:
        stmt = select(Organization.id).where(Organization.slug.in_(slugs_to_purge))
        res = await session.execute(stmt)
        org_ids = list(res.scalars().all())

        if not org_ids:
            logger.info("No bulk organizations found to purge.")
            return {"status": "success", "purged_organizations": 0}

        logger.info(f"Purging bulk dataset for organization IDs: {org_ids}")

        # 1. Automation Executions & Actions
        await session.execute(delete(AutomationExecutionAction).where(
            AutomationExecutionAction.execution_id.in_(
                select(AutomationExecution.id).where(AutomationExecution.organization_id.in_(org_ids))
            )
        ))
        await session.execute(delete(AutomationExecution).where(AutomationExecution.organization_id.in_(org_ids)))
        await session.execute(delete(AutomationRule).where(AutomationRule.organization_id.in_(org_ids)))

        # 2. Nudges, Monitoring Events & Deal Health
        await session.execute(delete(NudgeHistory).where(NudgeHistory.organization_id.in_(org_ids)))
        await session.execute(delete(Nudge).where(Nudge.organization_id.in_(org_ids)))
        await session.execute(delete(MonitoringEvent).where(MonitoringEvent.organization_id.in_(org_ids)))
        await session.execute(delete(DealHealthSnapshot).where(DealHealthSnapshot.organization_id.in_(org_ids)))

        # 3. Portal, Negotiation & Comments
        await session.execute(delete(QuotationLineComment).where(QuotationLineComment.organization_id.in_(org_ids)))
        await session.execute(delete(QuotationChangeRequest).where(QuotationChangeRequest.organization_id.in_(org_ids)))
        await session.execute(delete(QuotationVersion).where(QuotationVersion.organization_id.in_(org_ids)))
        await session.execute(delete(PortalUser).where(PortalUser.organization_id.in_(org_ids)))

        # 4. Payments, Refunds, Credit Notes & Invoices
        await session.execute(delete(PaymentRefund).where(PaymentRefund.organization_id.in_(org_ids)))
        await session.execute(delete(Payment).where(Payment.organization_id.in_(org_ids)))
        await session.execute(delete(CreditNoteItem).where(CreditNoteItem.organization_id.in_(org_ids)))
        await session.execute(delete(CreditNote).where(CreditNote.organization_id.in_(org_ids)))
        await session.execute(delete(InvoiceItem).where(InvoiceItem.organization_id.in_(org_ids)))
        await session.execute(delete(Invoice).where(Invoice.organization_id.in_(org_ids)))

        # 5. Subscriptions
        await session.execute(delete(SubscriptionCancellation).where(SubscriptionCancellation.organization_id.in_(org_ids)))
        await session.execute(delete(SubscriptionProration).where(SubscriptionProration.organization_id.in_(org_ids)))
        await session.execute(delete(BillingSchedule).where(BillingSchedule.organization_id.in_(org_ids)))
        await session.execute(delete(Subscription).where(Subscription.organization_id.in_(org_ids)))

        # 6. Fulfillment, Shipments, Backorders & Allocations
        await session.execute(delete(DeliveryPromise).where(DeliveryPromise.organization_id.in_(org_ids)))
        await session.execute(delete(ShipmentLine).where(ShipmentLine.organization_id.in_(org_ids)))
        await session.execute(delete(Shipment).where(Shipment.organization_id.in_(org_ids)))
        await session.execute(delete(Backorder).where(Backorder.organization_id.in_(org_ids)))
        await session.execute(delete(BillingClassification).where(BillingClassification.organization_id.in_(org_ids)))
        await session.execute(delete(WarehouseAllocation).where(WarehouseAllocation.organization_id.in_(org_ids)))
        await session.execute(delete(FulfillmentOverrideAudit).where(FulfillmentOverrideAudit.organization_id.in_(org_ids)))

        # 7. Approvals & Rules
        await session.execute(delete(ApprovalAuditLog).where(ApprovalAuditLog.organization_id.in_(org_ids)))
        await session.execute(delete(QuotationApproval).where(QuotationApproval.organization_id.in_(org_ids)))
        await session.execute(delete(ApprovalRule).where(ApprovalRule.organization_id.in_(org_ids)))

        # 8. Inventory Stocks, Movements & Reservations
        await session.execute(delete(InventoryReservation).where(InventoryReservation.organization_id.in_(org_ids)))
        await session.execute(delete(InventoryMovement).where(InventoryMovement.organization_id.in_(org_ids)))
        await session.execute(delete(InventoryStock).where(InventoryStock.organization_id.in_(org_ids)))

        # 9. Quotations & Items
        await session.execute(delete(QuotationStateHistory).where(QuotationStateHistory.organization_id.in_(org_ids)))
        await session.execute(delete(QuotationItem).where(
            QuotationItem.quotation_id.in_(
                select(Quotation.id).where(Quotation.organization_id.in_(org_ids))
            )
        ))
        await session.execute(delete(Quotation).where(Quotation.organization_id.in_(org_ids)))

        # 10. Activities & Deals
        await session.execute(delete(Activity).where(Activity.organization_id.in_(org_ids)))
        await session.execute(delete(Deal).where(Deal.organization_id.in_(org_ids)))

        # 11. Contacts & Customers
        await session.execute(delete(Contact).where(Contact.organization_id.in_(org_ids)))
        await session.execute(delete(Customer).where(Customer.organization_id.in_(org_ids)))

        # 12. Rules (Pricing, Discount, Recommendations)
        await session.execute(delete(PricingRule).where(PricingRule.organization_id.in_(org_ids)))
        await session.execute(delete(DiscountPolicy).where(DiscountPolicy.organization_id.in_(org_ids)))
        await session.execute(delete(ProductRecommendationRule).where(ProductRecommendationRule.organization_id.in_(org_ids)))

        # 13. Products, Variants & Warehouses
        await session.execute(delete(ProductVariant).where(
            ProductVariant.product_id.in_(
                select(Product.id).where(Product.organization_id.in_(org_ids))
            )
        ))
        await session.execute(delete(Product).where(Product.organization_id.in_(org_ids)))
        await session.execute(delete(Warehouse).where(Warehouse.organization_id.in_(org_ids)))

        # 14. Users
        await session.execute(delete(User).where(User.organization_id.in_(org_ids)))

        # 15. Organizations
        await session.execute(delete(Organization).where(Organization.id.in_(org_ids)))

        await session.commit()
        logger.info("Bulk dataset reset completed successfully.")
        return {"status": "success", "purged_organizations": len(org_ids)}

    except Exception as exc:
        await session.rollback()
        logger.error(f"Error resetting bulk data: {exc}", exc_info=True)
        raise exc
    finally:
        if should_close:
            await session.close()


async def seed_bulk_data(
    session: Optional[AsyncSession] = None,
    config: Optional[Dict[str, Any]] = None,
    target_records: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generates deterministic bulk data (~3,500 records total; 120 for major entities like
    customers, products, deals, quotations) under the 'bulk-data-lab' tenant.
    Idempotent: resets existing bulk tenant first before re-seeding.
    """
    should_close = False
    if session is None:
        session = AsyncSessionLocal()
        should_close = True

    cfg = DEFAULT_BULK_CONFIG.copy()
    if config:
        cfg.update(config)

    # Seed random generator deterministically
    rnd = random.Random(42)

    try:
        # 1. Reset existing bulk data if present
        await reset_bulk_data(session)

        base_now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
        start_history = datetime(2025, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        total_days_span = (base_now - start_history).days

        # =========================================================================
        # 1. ORGANIZATIONS (Primary Bulk Lab + Isolation Lab)
        # =========================================================================
        org_bulk = Organization(
            id=uuid.uuid4(),
            name=BULK_ORG_NAME,
            slug=BULK_ORG_SLUG,
            is_active=True
        )
        org_iso = Organization(
            id=uuid.uuid4(),
            name=BULK_ISOLATION_NAME,
            slug=BULK_ISOLATION_SLUG,
            is_active=True
        )
        session.add_all([org_bulk, org_iso])
        await session.flush()
        org_id = org_bulk.id
        iso_id = org_iso.id

        # =========================================================================
        # 2. USERS (Staff & Admin Personas)
        # =========================================================================
        user_roles_def = [
            ("Lab Admin", "lab.admin@dealflow.test", True),
            ("Operations Director", "ops.director@dealflow.test", True),
            ("Commercial VP", "commercial.vp@dealflow.test", True),
            ("Finance Controller", "finance.controller@dealflow.test", True),
            ("Sales Lead North", "sales.north@dealflow.test", False),
            ("Sales Lead West", "sales.west@dealflow.test", False),
            ("Sales Lead South", "sales.south@dealflow.test", False),
            ("Sales Lead East", "sales.east@dealflow.test", False),
            ("Senior Account Exec 1", "ae1@dealflow.test", False),
            ("Senior Account Exec 2", "ae2@dealflow.test", False),
            ("Senior Account Exec 3", "ae3@dealflow.test", False),
            ("Senior Account Exec 4", "ae4@dealflow.test", False),
            ("Inside Sales Rep 1", "isr1@dealflow.test", False),
            ("Inside Sales Rep 2", "isr2@dealflow.test", False),
            ("Inventory Manager", "inventory.mgr@dealflow.test", False),
            ("Warehouse Dispatch Lead", "dispatch.lead@dealflow.test", False),
            ("Fulfillment Specialist", "fulfillment.spec@dealflow.test", False),
            ("Billing Specialist", "billing.spec@dealflow.test", False),
            ("Collections Officer", "collections@dealflow.test", False),
            ("Customer Success Lead", "csm.lead@dealflow.test", False),
        ]
        users: List[User] = []
        p_hash = get_password_hash("BulkPass123!")
        for name, email, is_adm in user_roles_def:
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

        # Isolation tenant user
        u_iso = User(
            id=uuid.uuid4(),
            organization_id=iso_id,
            email="iso.user@dealflow.test",
            full_name="Isolation User",
            password_hash=p_hash,
            is_admin=True,
            is_active=True
        )
        users.append(u_iso)
        session.add_all(users)
        await session.flush()
        primary_admin = users[0]
        sales_users = [u for u in users if not u.is_admin and ("sales" in u.email or "ae" in u.email or "isr" in u.email)]

        # =========================================================================
        # 3. WAREHOUSES (10 Regional Hubs)
        # =========================================================================
        warehouses_def = [
            ("WH-MUM", "Mumbai Central Logistics Park", "Bhiwandi, Thane, Mumbai, Maharashtra", 1),
            ("WH-BLR", "Bengaluru Tech Park Depot", "Electronic City Phase 1, Bengaluru, Karnataka", 2),
            ("WH-DEL", "Delhi NCR Distribution Center", "Udyog Vihar Phase IV, Gurugram, Haryana", 3),
            ("WH-HYD", "Hyderabad Fulfillment Gateway", "HITEC City Logistics, Hyderabad, Telangana", 4),
            ("WH-PUN", "Pune Industrial Storage Hub", "Chakan Industrial Zone, Pune, Maharashtra", 5),
            ("WH-AMD", "Ahmedabad Western Facility", "Sanand Industrial Estate, Ahmedabad, Gujarat", 6),
            ("WH-CHE", "Chennai Port Corridor Depot", "Sriperumbudur Hub, Chennai, Tamil Nadu", 7),
            ("WH-CCU", "Kolkata Eastern Hub", "Dankuni Logistics Park, Kolkata, West Bengal", 8),
            ("WH-JAI", "Jaipur Northern Depot", "Sitapura Industrial Area, Jaipur, Rajasthan", 9),
            ("WH-BLR2", "Bengaluru Whitefield Fulfillment", "Whitefield EPIP Zone, Bengaluru, Karnataka", 10),
        ]
        warehouses: List[Warehouse] = []
        for code, name, addr, prio in warehouses_def:
            wh = Warehouse(
                id=uuid.uuid4(),
                organization_id=org_id,
                code=code,
                name=name,
                address=addr,
                priority=prio,
                is_active=True
            )
            warehouses.append(wh)
        session.add_all(warehouses)
        await session.flush()

        # =========================================================================
        # 4. CUSTOMERS & CONTACTS (Configurable: ~120 Customers, ~180 Contacts)
        # =========================================================================
        cities_data = [
            ("Mumbai", "Maharashtra", "400001", "India"),
            ("Bengaluru", "Karnataka", "560001", "India"),
            ("New Delhi", "Delhi", "110001", "India"),
            ("Hyderabad", "Telangana", "500081", "India"),
            ("Pune", "Maharashtra", "411001", "India"),
            ("Ahmedabad", "Gujarat", "380001", "India"),
            ("Chennai", "Tamil Nadu", "600001", "India"),
            ("Kolkata", "West Bengal", "700001", "India"),
            ("Jaipur", "Rajasthan", "302001", "India"),
            ("Gurugram", "Haryana", "122001", "India"),
        ]

        prefixes = ["Apex", "Vertex", "Quantum", "Nexus", "Starlight", "Horizon", "BluePeak", "Nova", "Titan", "Zenith",
                    "Elevate", "Aura", "Matrix", "Vanguard", "Pinnacle", "Synergy", "Pulse", "Stratum", "Beacon", "Crest"]
        sectors = ["Technologies", "Commercial Systems", "Enterprises", "Solutions", "Healthcare", "Hospitality Group",
                   "Retail Networks", "Logistics", "Workspace Labs", "Industrial Automation", "Financial Services", "Media & Infra"]

        customers: List[Customer] = []
        contacts: List[Contact] = []
        cust_idx = 1
        cust_limit = cfg.get("customers", 120)

        for pfx in prefixes:
            for sct in sectors:
                city_info = cities_data[(cust_idx - 1) % len(cities_data)]
                c_name = f"{pfx} {sct} {cust_idx:03d}"
                c_email = f"procure.{pfx.lower()}{cust_idx}@dealflow.test"
                c_phone = f"+91-98{rnd.randint(10000000, 99999999)}"
                cust = Customer(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    name=c_name,
                    email=c_email,
                    phone=c_phone,
                    address=f"Suite {rnd.randint(100, 900)}, {pfx} Business Tower, Commercial Ring Road",
                    city=city_info[0],
                    state=city_info[1],
                    country=city_info[3],
                    postal_code=city_info[2],
                    is_active=True
                )
                customers.append(cust)

                # Add 1 or 2 contacts per customer
                first_names = ["Aarav", "Pooja", "Vikram", "Neha", "Rahul", "Sneha", "Aditya", "Rohan", "Ananya", "Rhea"]
                last_names = ["Sharma", "Patel", "Mehta", "Iyer", "Nair", "Verma", "Reddy", "Chopra", "Gupta", "Deshmukh"]

                cnt_count = 1 if cust_idx % 2 == 0 else 2
                for i in range(cnt_count):
                    fn = rnd.choice(first_names)
                    ln = rnd.choice(last_names)
                    cnt = Contact(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        customer_id=cust.id,
                        first_name=fn,
                        last_name=ln,
                        email=f"{fn.lower()}.{ln.lower()}{cust_idx}_{i+1}@dealflow.test",
                        phone=f"+91-97{rnd.randint(10000000, 99999999)}",
                        job_title="Head of Procurement" if i == 0 else "Operations Manager",
                        is_primary=(i == 0)
                    )
                    contacts.append(cnt)

                cust_idx += 1
                if len(customers) >= cust_limit:
                    break
            if len(customers) >= cust_limit:
                break

        session.add_all(customers)
        session.add_all(contacts)
        await session.flush()

        # =========================================================================
        # 5. PORTAL USERS (Configurable: 20 Customer Portal Users)
        # =========================================================================
        portal_user_count = min(cfg.get("portal_users", 20), len(customers))
        portal_users: List[PortalUser] = []
        for i in range(portal_user_count):
            c_target = customers[i]
            c_contact = [cnt for cnt in contacts if cnt.customer_id == c_target.id][0]
            pu = PortalUser(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=c_target.id,
                contact_id=c_contact.id,
                email=f"portal.user{i+1:02d}@dealflow.test",
                hashed_password=p_hash,
                full_name=f"{c_contact.first_name} {c_contact.last_name}",
                is_active=True,
                last_login_at=base_now - timedelta(days=rnd.randint(1, 45))
            )
            portal_users.append(pu)
        session.add_all(portal_users)
        await session.flush()

        # =========================================================================
        # 6. PRODUCTS & PRODUCT VARIANTS (Configurable: ~120 Products, ~240 Variants)
        # =========================================================================
        categories_products = [
            # Office Furniture
            ("Executive Ergonomic Mesh Chair", "DF-FUR-CHR", Decimal("18500.00"), Decimal("11000.00"), ["Black Mesh", "Grey Mesh"]),
            ("Dual-Motor Height Adjustable Standing Desk (150x75cm)", "DF-FUR-DSK", Decimal("34000.00"), Decimal("21000.00"), ["Walnut Top", "Oak Top"]),
            ("Conference Pod 4-Seater Soundproof Booth", "DF-FUR-POD", Decimal("285000.00"), Decimal("175000.00"), ["Standard Glass", "Frosted Acoustic Glass"]),
            ("Modular Collaborative L-Shaped Workstation", "DF-FUR-WSK", Decimal("52000.00"), Decimal("31000.00"), ["2-Person Pod", "4-Person Cluster"]),
            ("Heavy-Duty Steel Lateral Filing Cabinet", "DF-FUR-CAB", Decimal("14500.00"), Decimal("8500.00"), ["3-Drawer White", "4-Drawer Charcoal"]),
            ("Executive Wooden Credenza with Soft-Close Doors", "DF-FUR-CRD", Decimal("27500.00"), Decimal("16000.00"), ["Dark Walnut", "Natural Teak"]),
            ("High-Back Leatherette Boardroom Chair", "DF-FUR-BDR", Decimal("22000.00"), Decimal("13000.00"), ["Cognac Brown", "Obsidian Black"]),
            ("Acoustic Hanging Baffle Sound Absorption Panel", "DF-FUR-ACU", Decimal("4800.00"), Decimal("2400.00"), ["Charcoal Grey", "Ocean Blue"]),

            # Workspace Equipment & IT
            ("Dual Gas-Spring Heavy Aluminum Monitor Arm", "DF-EQP-MAR", Decimal("7200.00"), Decimal("3800.00"), ["Dual VESA 32-inch", "Triple VESA Heavy"]),
            ("Universal Thunderbolt 4 Quad-Display Docking Hub", "DF-EQP-DCK", Decimal("16500.00"), Decimal("9500.00"), ["100W PD Edition", "140W Dual-Host"]),
            ("Smart Interactive 75-inch UHD 4K Digital Whiteboard", "DF-EQP-SBD", Decimal("195000.00"), Decimal("125000.00"), ["Wall-Mount Standard", "Mobile Cart Bundle"]),
            ("Desk-Integrated Wireless Fast Charging Grommet", "DF-EQP-WCG", Decimal("2400.00"), Decimal("1100.00"), ["65W USB-C GaN", "100W Hub"]),
            ("Under-Desk Steel Cable Management Spine Tray", "DF-EQP-CBL", Decimal("1800.00"), Decimal("800.00"), ["Silver Metallic", "Matte Black"]),
            ("Commercial Air Quality CO2 & VOC Smart Sensor Hub", "DF-EQP-SEN", Decimal("12500.00"), Decimal("6500.00"), ["Zigbee Enterprise", "WiFi 6 Cloud"]),

            # Hospitality & Lounge
            ("Lounge Reception 3-Seater Minimalist Fabric Sofa", "DF-HSP-SOF", Decimal("48000.00"), Decimal("28000.00"), ["Nordic Grey", "Forest Green"]),
            ("Solid Oak Coffee Table with Brass Accent Frame", "DF-HSP-CFT", Decimal("18500.00"), Decimal("10500.00"), ["Round 90cm", "Rectangular 120cm"]),
            ("Commercial High-Top Café Bar Stool (Set of 2)", "DF-HSP-BST", Decimal("11500.00"), Decimal("6200.00"), ["Walnut Finish", "Brushed Brass"]),
            ("Modular Upholstered Privacy Lounge Booth", "DF-HSP-BTH", Decimal("78000.00"), Decimal("45000.00"), ["High-Back 2-Seat", "Enclosed 4-Seat"]),

            # Software Subscriptions & Digital Services
            ("DealFlow360 Enterprise CRM License (Per User / Year)", "DF-SFT-ENT", Decimal("36000.00"), Decimal("6000.00"), ["Standard SLA", "24/7 Dedicated CSM"]),
            ("Revenue Analytics & AI Forecasting Engine Add-on", "DF-SFT-AI", Decimal("72000.00"), Decimal("12000.00"), ["Annual Tier 1", "Annual Tier 2"]),
            ("Automated Multi-Warehouse Inventory Sync Module", "DF-SFT-INV", Decimal("45000.00"), Decimal("8000.00"), ["10-Warehouse Cloud", "Unlimited Enterprise"]),
            ("Customer Self-Service Negotiation Portal Gateway", "DF-SFT-PRT", Decimal("28000.00"), Decimal("4000.00"), ["Custom Branded Domain", "Multi-Tenant SLA"]),

            # Annual Maintenance & Services
            ("Comprehensive Annual Maintenance Contract (Furniture)", "DF-SRV-AMC", Decimal("25000.00"), Decimal("8000.00"), ["Standard Quarterly", "Priority Monthly"]),
            ("Commercial Facility Ergonomic Audit & Layout Design", "DF-SRV-AUD", Decimal("35000.00"), Decimal("10000.00"), ["Floorplan 5000 sqft", "Floorplan 20000 sqft"]),
            ("Turnkey White-Glove On-site Delivery & Installation", "DF-SRV-INS", Decimal("18000.00"), Decimal("6000.00"), ["Metro Standard", "Express Weekend"]),

            # Raw Material & Assembly Components
            ("Cold-Rolled Steel Desk Leg Framework Set", "DF-RAW-STL", Decimal("6500.00"), Decimal("4200.00"), ["Black Powder-Coat", "White Powder-Coat"]),
            ("Industrial Dual Electric Synchronized Motor Cylinder", "DF-RAW-MTR", Decimal("8200.00"), Decimal("5500.00"), ["3-Stage Heavy Duty", "2-Stage Standard"]),
            ("Pre-Drilled European Solid Birch Veneer Desktop (160x80cm)", "DF-RAW-TOP", Decimal("7800.00"), Decimal("4800.00"), ["Birch Natural", "Smoked Oak"]),
            ("Cast Aluminum 5-Star Chair Base with PU Casters", "DF-RAW-BAS", Decimal("3200.00"), Decimal("1900.00"), ["Polished Chrome", "Matte Black"]),
            ("Class-4 Heavy Gas-Lift Pneumatic Cylinder 120mm", "DF-RAW-GAS", Decimal("1500.00"), Decimal("850.00"), ["Standard Travel", "High-Stool Travel"]),
        ]

        products: List[Product] = []
        product_variants: List[ProductVariant] = []
        prod_limit = cfg.get("products", 120)

        p_counter = 1
        while len(products) < prod_limit:
            for base_name, sku_prefix, price, cost, var_names in categories_products:
                p_sku = f"{sku_prefix}-{p_counter:04d}"
                prod = Product(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    name=f"{base_name} #{p_counter}",
                    sku=p_sku,
                    description=f"Commercial-grade {base_name.lower()} engineered for enterprise high-reliability deployment.",
                    unit_price=price,
                    unit_cost=cost,
                    currency="USD",
                    is_active=True
                )
                products.append(prod)

                # Add variants
                for v_idx, v_name in enumerate(var_names, 1):
                    v_suffix = "".join(c for c in v_name if c.isalnum())[:4].upper()
                    v_sku = f"{p_sku}-V{v_idx:02d}-{v_suffix}"
                    override_price = price + Decimal(str(rnd.choice([0, 500, 1200, 2500])))
                    var = ProductVariant(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        product_id=prod.id,
                        sku=v_sku,
                        name=f"{prod.name} ({v_name})",
                        unit_price_override=override_price,
                        is_active=True
                    )
                    product_variants.append(var)

                p_counter += 1
                if len(products) >= prod_limit:
                    break

        session.add_all(products)
        await session.flush()
        session.add_all(product_variants)
        await session.flush()

        # =========================================================================
        # 7. INVENTORY STOCKS & MOVEMENTS (~360 Stock Locations Across Warehouses)
        # =========================================================================
        inventory_stocks: List[InventoryStock] = []
        inventory_movements: List[InventoryMovement] = []

        for p_idx, prod in enumerate(products):
            # Select 3-4 warehouses for each product
            assigned_whs = rnd.sample(warehouses, rnd.randint(3, 4))
            for wh in assigned_whs:
                stock_scenario = rnd.choice(["HEALTHY", "HEALTHY", "HEALTHY", "LOW", "ZERO", "RESERVED"])
                if stock_scenario == "HEALTHY":
                    on_hand = rnd.randint(50, 400)
                    reserved = rnd.randint(0, min(30, on_hand))
                elif stock_scenario == "LOW":
                    on_hand = rnd.randint(5, 15)
                    reserved = rnd.randint(0, 3)
                elif stock_scenario == "ZERO":
                    on_hand = 0
                    reserved = 0
                else:  # RESERVED
                    on_hand = rnd.randint(30, 100)
                    reserved = min(on_hand, rnd.randint(20, on_hand))

                avail = max(0, on_hand - reserved)

                stk = InventoryStock(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    warehouse_id=wh.id,
                    product_id=prod.id,
                    variant_id=None,
                    location_code="MAIN-RACK",
                    on_hand_quantity=on_hand,
                    reserved_quantity=reserved,
                    available_quantity=avail
                )
                inventory_stocks.append(stk)

                if on_hand > 0:
                    mvt = InventoryMovement(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        warehouse_id=wh.id,
                        product_id=prod.id,
                        variant_id=None,
                        quantity=on_hand,
                        movement_type="RECEIPT",
                        reference_type="PO_INITIAL",
                        reference_id=None,
                        actor_id=primary_admin.id,
                        actor_name=primary_admin.full_name,
                        notes=f"Initial stock replenishment into {wh.code}"
                    )
                    inventory_movements.append(mvt)

        session.add_all(inventory_stocks)
        session.add_all(inventory_movements)
        await session.flush()

        # =========================================================================
        # 8. PRICING RULES, DISCOUNT POLICIES & RECOMMENDATION RULES
        # =========================================================================
        pricing_rule_count = cfg.get("pricing_rules", 100)
        pricing_rules: List[PricingRule] = []
        for i in range(pricing_rule_count):
            p = products[i % len(products)]
            c = customers[i % len(customers)] if i % 3 == 0 else None
            r_type = rnd.choice(["volume", "volume", "contract", "promotion"])
            p_type = rnd.choice(["override_price", "percentage_discount", "fixed_discount"])

            if p_type == "percentage_discount":
                val = _d(rnd.randint(5, 25))
            elif p_type == "fixed_discount":
                val = _d(rnd.randint(500, 3000))
            else:
                val = _d(p.unit_price * Decimal("0.85"))

            p_rule = PricingRule(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=f"Rule: {r_type.title()} Pricing for {p.sku}",
                rule_type=r_type,
                product_id=p.id,
                customer_id=c.id if c else None,
                min_quantity=_d(rnd.choice([5, 10, 20, 50])),
                max_quantity=_d(rnd.choice([100, 500, 1000])) if rnd.random() > 0.5 else None,
                price_type=p_type,
                value=val,
                priority=rnd.randint(1, 100),
                is_active=True,
                description=f"Deterministic commercial pricing rule for {p.name}"
            )
            pricing_rules.append(p_rule)
        session.add_all(pricing_rules)

        discount_policy_count = cfg.get("discount_policies", 60)
        discount_policies: List[DiscountPolicy] = []
        for i in range(discount_policy_count):
            p = products[i % len(products)] if i % 2 == 0 else None
            c = customers[i % len(customers)] if i % 3 == 0 else None
            dp = DiscountPolicy(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=f"Policy: Max Commercial Margin Tier {i+1}",
                description=f"Governance threshold for discount caps.",
                scope=rnd.choice(["organization", "role", "customer", "product"]),
                product_id=p.id if p else None,
                customer_id=c.id if c else None,
                role="sales" if i % 4 == 0 else None,
                max_discount_percent=_d(rnd.choice([10, 15, 20, 25])),
                minimum_margin_percent=_d(rnd.choice([15, 20, 25, 30])),
                priority=rnd.randint(1, 50),
                is_active=True
            )
            discount_policies.append(dp)
        session.add_all(discount_policies)

        rec_rule_count = cfg.get("recommendation_rules", 80)
        rec_rules: List[ProductRecommendationRule] = []
        for i in range(rec_rule_count):
            src_p = products[i % len(products)]
            tgt_p = products[(i + 7) % len(products)]
            if src_p.id != tgt_p.id:
                rec_rule = ProductRecommendationRule(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    source_product_id=src_p.id,
                    target_product_id=tgt_p.id,
                    rule_type=rnd.choice(["upsell", "cross_sell"]),
                    priority=rnd.randint(1, 10),
                    is_active=True,
                    description=f"Suggest {tgt_p.sku} when purchasing {src_p.sku}"
                )
                rec_rules.append(rec_rule)
        session.add_all(rec_rules)

        approval_rules: List[ApprovalRule] = []
        appr_thresholds = [
            ("Tier 1: Standard Manager Approval (>10% Discount)", Decimal("10.00"), Decimal("15.00"), 1, "admin", Decimal("100000.00")),
            ("Tier 2: Commercial Director Approval (>15% Discount)", Decimal("15.01"), Decimal("22.00"), 2, "admin", Decimal("250000.00")),
            ("Tier 3: VP Commercial Approval (>22% Discount)", Decimal("22.01"), Decimal("30.00"), 3, "admin", Decimal("500000.00")),
            ("Tier 4: CEO / Owner High-Value Governance Approval", Decimal("30.01"), Decimal("50.00"), 4, "admin", Decimal("1000000.00")),
        ]
        for name, min_d, max_d, lvl, req_role, val_thresh in appr_thresholds:
            ar = ApprovalRule(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=name,
                description=f"Automated commercial authorization rule level {lvl}",
                is_active=True,
                priority=lvl * 10,
                min_discount_percent=min_d,
                max_discount_percent=max_d,
                min_margin_percent=Decimal("15.00"),
                risk_level="HIGH" if lvl >= 3 else "MEDIUM",
                quotation_value_threshold=val_thresh,
                approval_level=lvl,
                required_role=req_role
            )
            approval_rules.append(ar)
        session.add_all(approval_rules)
        await session.flush()

        # =========================================================================
        # 9. DEALS & QUOTATIONS & WORKFLOWS (120 Deals, 120 Quotations, ~360 Items)
        # =========================================================================
        deals: List[Deal] = []
        quotations: List[Quotation] = []
        quotation_items: List[QuotationItem] = []
        quotation_state_histories: List[QuotationStateHistory] = []
        quotation_approvals: List[QuotationApproval] = []
        approval_audit_logs: List[ApprovalAuditLog] = []
        quotation_comments: List[QuotationLineComment] = []
        quotation_changes: List[QuotationChangeRequest] = []
        quotation_versions: List[QuotationVersion] = []
        warehouse_allocations: List[WarehouseAllocation] = []
        billing_classifications: List[BillingClassification] = []

        inventory_reservations: List[InventoryReservation] = []
        shipments: List[Shipment] = []
        shipment_lines: List[ShipmentLine] = []
        backorders: List[Backorder] = []
        delivery_promises: List[DeliveryPromise] = []

        invoices: List[Invoice] = []
        invoice_items: List[InvoiceItem] = []
        payments: List[Payment] = []
        credit_notes: List[CreditNote] = []
        credit_note_items: List[CreditNoteItem] = []
        payment_refunds: List[PaymentRefund] = []

        subscriptions: List[Subscription] = []
        billing_schedules: List[BillingSchedule] = []
        subscription_prorations: List[SubscriptionProration] = []
        subscription_cancellations: List[SubscriptionCancellation] = []

        deal_health_snapshots: List[DealHealthSnapshot] = []
        monitoring_events: List[MonitoringEvent] = []
        nudges: List[Nudge] = []
        nudge_histories: List[NudgeHistory] = []
        activities: List[Activity] = []

        q_status_weights = [
            ("draft", 12),
            ("priced", 18),
            ("sent", 24),
            ("accepted", 32),
            ("rejected", 12),
            ("expired", 10),
            ("cancelled", 4),
            ("converted", 8),
        ]
        status_pool: List[str] = []
        for st, count in q_status_weights:
            status_pool.extend([st] * count)

        quote_limit = min(cfg.get("quotations", 120), cfg.get("deals", 120))
        for q_idx in range(1, quote_limit + 1):
            cust = customers[(q_idx - 1) % len(customers)]
            cust_contacts = [cnt for cnt in contacts if cnt.customer_id == cust.id]
            contact = cust_contacts[0] if cust_contacts else None
            assigned_rep = rnd.choice(sales_users)

            # Historical date distribution
            days_ago = rnd.randint(5, total_days_span)
            q_date = base_now - timedelta(days=days_ago, hours=rnd.randint(1, 8))
            q_status = status_pool[(q_idx - 1) % len(status_pool)]

            deal_stage_map = {
                "draft": ("new", "open", 20),
                "priced": ("qualifying", "open", 40),
                "sent": ("proposal", "open", 60),
                "accepted": ("won", "won", 100),
                "converted": ("won", "won", 100),
                "rejected": ("lost", "lost", 0),
                "expired": ("lost", "lost", 0),
                "cancelled": ("lost", "lost", 0),
            }
            d_stage, d_status, d_prob = deal_stage_map.get(q_status, ("proposal", "open", 50))

            deal_num = f"DL-2025-{q_idx:05d}"
            deal = Deal(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=cust.id,
                contact_id=contact.id if contact else None,
                quotation_id=None,
                title=f"Commercial Workspace Fitout - {cust.name}",
                description=f"Turnkey enterprise procurement and licensing cycle for {cust.name}.",
                deal_number=deal_num,
                stage=d_stage,
                status=d_status,
                value=Decimal("0.00"),  # will update after quote calc
                probability=d_prob,
                expected_close_date=(q_date + timedelta(days=30)).date(),
                lost_reason="Budget constraint" if d_status == "lost" else None,
                notes=f"Key stakeholder: {contact.first_name if contact else 'Director'}"
            )
            deals.append(deal)

            # Create Quotation
            q_num = f"QT-2025-{q_idx:05d}"
            quote = Quotation(
                id=uuid.uuid4(),
                organization_id=org_id,
                customer_id=cust.id,
                contact_id=contact.id if contact else None,
                deal_id=deal.id,
                title=f"Proposal for {cust.name} ({q_num})",
                quotation_number=q_num,
                status=q_status,
                currency="USD",
                quotation_date=q_date,
                valid_until=q_date + timedelta(days=30),
                notes="Delivery timeline 10-14 business days from confirmation.",
                terms="Net 30 days. Standard 3-year warranty included.",
                created_by_user_id=assigned_rep.id,
                updated_by_user_id=assigned_rep.id,
                subtotal=Decimal("0.00"),
                discount_amount=Decimal("0.00"),
                tax_amount=Decimal("0.00"),
                total_amount=Decimal("0.00")
            )
            quotations.append(quote)

            # Add 2 to 4 Line Items
            item_count = rnd.randint(2, 4)
            q_subtotal = Decimal("0.00")
            q_discount = Decimal("0.00")
            q_tax = Decimal("0.00")

            selected_prods = rnd.sample(products, item_count)
            for seq, p in enumerate(selected_prods, 1):
                qty = _d(rnd.choice([2, 5, 10, 20, 50]))
                u_price = p.unit_price
                u_cost = p.unit_cost

                # Discount logic
                disc_pct = Decimal(str(rnd.choice([0, 5, 10, 15, 20, 25])))
                line_sub = (qty * u_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                line_disc = (line_sub * disc_pct / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                tax_rate = Decimal("18.00")
                taxable = line_sub - line_disc
                line_tax = (taxable * tax_rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                line_tot = taxable + line_tax

                q_subtotal += line_sub
                q_discount += line_disc
                q_tax += line_tax

                q_item = QuotationItem(
                    id=uuid.uuid4(),
                    quotation_id=quote.id,
                    product_id=p.id,
                    product_variant_id=None,
                    product_name=p.name,
                    sku=p.sku,
                    description=p.description,
                    sequence=seq,
                    quantity=qty,
                    unit_price=u_price,
                    unit_cost=u_cost,
                    discount_percent=disc_pct,
                    discount_amount=line_disc,
                    tax_rate=tax_rate,
                    tax_amount=line_tax,
                    line_total=line_tot
                )
                quotation_items.append(q_item)

            quote.subtotal = q_subtotal
            quote.discount_amount = q_discount
            quote.tax_amount = q_tax
            quote.total_amount = q_subtotal - q_discount + q_tax
            deal.value = quote.total_amount

            # Audit State History
            qsh = QuotationStateHistory(
                id=uuid.uuid4(),
                organization_id=org_id,
                quotation_id=quote.id,
                from_status=None,
                to_status=q_status,
                changed_by_user_id=assigned_rep.id,
                reason=f"Transitioned to {q_status} during business workflow"
            )
            quotation_state_histories.append(qsh)

            # Snapshot Version
            qv = QuotationVersion(
                id=uuid.uuid4(),
                organization_id=org_id,
                quotation_id=quote.id,
                version_number=1,
                subtotal=quote.subtotal,
                discount_amount=quote.discount_amount,
                tax_amount=quote.tax_amount,
                total_amount=quote.total_amount,
                gross_margin=quote.subtotal - quote.discount_amount,
                margin_percent=Decimal("35.00"),
                change_reason="Initial formal quotation creation",
                snapshot_payload={"items_count": item_count, "currency": "USD"},
                created_by_user_id=assigned_rep.id,
                created_at=q_date
            )
            quotation_versions.append(qv)

            # Commercial Billing Classification
            bc = BillingClassification(
                id=uuid.uuid4(),
                organization_id=org_id,
                quotation_id=quote.id,
                commercial_model="ONE_TIME" if q_idx % 4 != 0 else "HYBRID",
                one_time_total=quote.total_amount,
                recurring_monthly_total=Decimal("4500.00") if q_idx % 4 == 0 else Decimal("0.00"),
                billing_frequency="MONTHLY",
                line_classifications={"model": "STANDARD"}
            )
            billing_classifications.append(bc)

            # Approvals for High Discount Quotations (>=15%)
            if q_discount > Decimal("0.00") and (q_discount / q_subtotal) >= Decimal("0.15"):
                appr = QuotationApproval(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    quotation_id=quote.id,
                    approval_rule_id=approval_rules[1].id,
                    requested_by_user_id=assigned_rep.id,
                    approved_by_user_id=primary_admin.id if q_status in ["accepted", "converted", "sent"] else None,
                    status="APPROVED" if q_status in ["accepted", "converted", "sent"] else ("REJECTED" if q_status == "rejected" else "PENDING"),
                    approval_level=2,
                    reasons="Discount exceeds standard 15% threshold.",
                    decision_note="Approved based on strategic account expansion potential." if q_status in ["accepted", "converted"] else None
                )
                quotation_approvals.append(appr)

                aal = ApprovalAuditLog(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    quotation_id=quote.id,
                    approval_id=appr.id,
                    event_type="DECISION_RECORDED",
                    actor_user_id=primary_admin.id,
                    actor_name=primary_admin.full_name,
                    previous_status="PENDING",
                    new_status=appr.status,
                    reason="Commercial review completed",
                    approval_rule_id=approval_rules[1].id,
                    approval_level=2,
                    created_at=q_date + timedelta(hours=4)
                )
                approval_audit_logs.append(aal)

            # Negotiation Comments & Change Requests for 1 in 3 quotes
            if q_idx % 3 == 0 and len(portal_users) > 0:
                target_portal_user = portal_users[(q_idx - 1) % len(portal_users)]
                first_item = [it for it in quotation_items if it.quotation_id == quote.id][0]

                qlc = QuotationLineComment(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    quotation_id=quote.id,
                    quotation_item_id=first_item.id,
                    author_type="PORTAL_USER",
                    author_user_id=None,
                    author_portal_user_id=target_portal_user.id,
                    author_name=target_portal_user.full_name,
                    comment_text="Can we get an additional 5% discount if we increase the volume to 50 units?",
                    is_internal_only=False,
                    created_at=q_date + timedelta(hours=12)
                )
                quotation_comments.append(qlc)

                qcr = QuotationChangeRequest(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    quotation_id=quote.id,
                    quotation_item_id=first_item.id,
                    requested_by_portal_user_id=target_portal_user.id,
                    change_type="DISCOUNT_REQUEST",
                    status="APPROVED" if q_status in ["accepted", "converted"] else "OPEN",
                    requested_discount_percent=Decimal("5.00"),
                    requested_quantity=Decimal("50.00"),
                    request_details="Volume discount counter-proposal via Customer Portal.",
                    response_note="Approved by Commercial Lead" if q_status in ["accepted", "converted"] else None,
                    reviewed_by_user_id=assigned_rep.id if q_status in ["accepted", "converted"] else None,
                    reviewed_at=q_date + timedelta(days=1) if q_status in ["accepted", "converted"] else None
                )
                quotation_changes.append(qcr)

            # Downstream Fulfillment & Billing for Accepted/Converted Quotes
            if q_status in ["accepted", "converted"]:
                target_wh = warehouses[(q_idx - 1) % len(warehouses)]
                q_items_for_q = [it for it in quotation_items if it.quotation_id == quote.id]

                for itm in q_items_for_q:
                    # Warehouse Allocation
                    walloc = WarehouseAllocation(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        quotation_id=quote.id,
                        quotation_item_id=itm.id,
                        warehouse_id=target_wh.id,
                        allocated_quantity=int(itm.quantity),
                        allocation_strategy="SINGLE_WAREHOUSE",
                        status="FULFILLED" if q_status == "converted" else "ALLOCATED"
                    )
                    warehouse_allocations.append(walloc)

                    # Stock Reservation
                    resv = InventoryReservation(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        quotation_id=quote.id,
                        quotation_item_id=itm.id,
                        product_id=itm.product_id,
                        variant_id=None,
                        warehouse_id=target_wh.id,
                        quantity=int(itm.quantity),
                        status="CONSUMED" if q_status == "converted" else "ACTIVE",
                        expires_at=q_date + timedelta(days=14)
                    )
                    inventory_reservations.append(resv)

                # Physical Shipment
                ship_status = "DELIVERED" if days_ago > 30 else ("SHIPPED" if days_ago > 10 else "READY")
                shpm = Shipment(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    shipment_number=f"SHP-2025-{q_idx:05d}",
                    quotation_id=quote.id,
                    warehouse_id=target_wh.id,
                    status=ship_status,
                    carrier=rnd.choice(["BlueDart Express", "Delhivery Surface", "FedEx Freight", "DHL Express"]),
                    tracking_number=f"TRK{rnd.randint(100000000, 999999999)}IN",
                    shipped_at=q_date + timedelta(days=3),
                    expected_delivery_date=(q_date + timedelta(days=8)).date(),
                    actual_delivery_date=(q_date + timedelta(days=7)).date() if ship_status == "DELIVERED" else None
                )
                shipments.append(shpm)

                for itm in q_items_for_q:
                    s_line = ShipmentLine(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        shipment_id=shpm.id,
                        quotation_item_id=itm.id,
                        product_id=itm.product_id,
                        variant_id=None,
                        quantity=int(itm.quantity)
                    )
                    shipment_lines.append(s_line)

                # Delivery Promise SLA tracker
                dp = DeliveryPromise(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    quotation_id=quote.id,
                    shipment_id=shpm.id,
                    backorder_id=None,
                    promised_date=(q_date + timedelta(days=10)).date(),
                    expected_date=(q_date + timedelta(days=8)).date(),
                    actual_date=(q_date + timedelta(days=7)).date() if ship_status == "DELIVERED" else None,
                    status="DELIVERED" if ship_status == "DELIVERED" else "ON_TRACK",
                    slippage_days=0,
                    notes="On-time fulfillment SLA met"
                )
                delivery_promises.append(dp)

                # Backorder scenario for 1 in 8 orders
                if q_idx % 8 == 0 and len(q_items_for_q) > 1:
                    bo_item = q_items_for_q[-1]
                    bo = Backorder(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        backorder_number=f"BO-2025-{q_idx:04d}",
                        quotation_id=quote.id,
                        quotation_item_id=bo_item.id,
                        customer_id=cust.id,
                        product_id=bo_item.product_id,
                        variant_id=None,
                        requested_quantity=int(bo_item.quantity),
                        fulfilled_quantity=int(bo_item.quantity) // 2,
                        remaining_quantity=int(bo_item.quantity) - (int(bo_item.quantity) // 2),
                        warehouse_id=target_wh.id,
                        status="OPEN" if ship_status != "DELIVERED" else "FULFILLED",
                        promised_delivery_date=(q_date + timedelta(days=21)).date()
                    )
                    backorders.append(bo)

                # Invoices & Payments
                inv_status = "PAID" if ship_status == "DELIVERED" else ("ISSUED" if days_ago > 15 else "PARTIALLY_PAID")
                inv_num = f"INV-2025-{q_idx:05d}"
                paid_amt = quote.total_amount if inv_status == "PAID" else (quote.total_amount / Decimal("2") if inv_status == "PARTIALLY_PAID" else Decimal("0.00"))
                due_amt = quote.total_amount - paid_amt

                inv = Invoice(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    invoice_number=inv_num,
                    customer_id=cust.id,
                    quotation_id=quote.id,
                    currency="USD",
                    invoice_date=q_date.date(),
                    due_date=(q_date + timedelta(days=30)).date(),
                    subtotal=quote.subtotal,
                    discount_total=quote.discount_amount,
                    tax_total=quote.tax_amount,
                    total=quote.total_amount,
                    amount_paid=paid_amt,
                    amount_due=due_amt,
                    status=inv_status
                )
                invoices.append(inv)

                for itm in q_items_for_q:
                    inv_item = InvoiceItem(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        invoice_id=inv.id,
                        product_id=itm.product_id,
                        product_variant_id=None,
                        quotation_item_id=itm.id,
                        description=itm.product_name,
                        quantity=itm.quantity,
                        unit_price=itm.unit_price,
                        discount_amount=itm.discount_amount,
                        tax_amount=itm.tax_amount,
                        line_subtotal=itm.quantity * itm.unit_price,
                        line_total=itm.line_total,
                        billing_type="ONE_TIME"
                    )
                    invoice_items.append(inv_item)

                # Payments for Paid/Partially Paid invoices
                if paid_amt > Decimal("0.00"):
                    pay = Payment(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        payment_reference=f"PAY-2025-{q_idx:05d}",
                        invoice_id=inv.id,
                        customer_id=cust.id,
                        payment_date=(q_date + timedelta(days=15)).date(),
                        amount=paid_amt,
                        method=rnd.choice(["BANK_TRANSFER", "CARD", "UPI", "CHEQUE"]),
                        status="COMPLETED",
                        notes="Automated settlement via Payment Gateway",
                        created_by_user_id=primary_admin.id
                    )
                    payments.append(pay)

                    # Occasional Credit Note & Refund for 1 in 10 paid invoices
                    if q_idx % 10 == 0 and inv_status == "PAID":
                        cn_amt = _d(quote.total_amount * Decimal("0.10"))
                        cn = CreditNote(
                            id=uuid.uuid4(),
                            organization_id=org_id,
                            credit_note_number=f"CN-2025-{q_idx:04d}",
                            invoice_id=inv.id,
                            customer_id=cust.id,
                            reason="Early payment commercial rebate / goodwill adjustment",
                            subtotal=cn_amt,
                            tax_total=Decimal("0.00"),
                            total=cn_amt,
                            status="ISSUED",
                            created_by_user_id=primary_admin.id
                        )
                        credit_notes.append(cn)

                        cn_item = CreditNoteItem(
                            id=uuid.uuid4(),
                            organization_id=org_id,
                            credit_note_id=cn.id,
                            description="Commercial settlement rebate credit",
                            quantity=Decimal("1.00"),
                            unit_price=cn_amt,
                            amount=cn_amt
                        )
                        credit_note_items.append(cn_item)

                        pref = PaymentRefund(
                            id=uuid.uuid4(),
                            organization_id=org_id,
                            refund_number=f"REF-2025-{q_idx:04d}",
                            payment_id=pay.id,
                            credit_note_id=cn.id,
                            amount=cn_amt,
                            reason="Rebate reimbursement payout",
                            refund_date=(q_date + timedelta(days=20)).date(),
                            status="COMPLETED",
                            created_by_user_id=primary_admin.id
                        )
                        payment_refunds.append(pref)

            # Subscriptions for 1 in 4 quotations
            if q_idx % 4 == 0:
                sub_prod = products[min(18, len(products) - 1)]
                sub_num = f"SUB-2025-{q_idx:04d}"
                sub_status = rnd.choice(["ACTIVE", "ACTIVE", "ACTIVE", "PAUSED", "CANCELLED"])
                sub_start = (q_date - timedelta(days=rnd.randint(30, 180))).date()
                sub = Subscription(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    subscription_number=sub_num,
                    customer_id=cust.id,
                    quotation_id=quote.id,
                    quotation_item_id=None,
                    product_id=sub_prod.id,
                    variant_id=None,
                    plan_name="DealFlow360 Cloud Platform Annual Subscription",
                    quantity=Decimal("10.00"),
                    unit_price=Decimal("3600.00"),
                    billing_interval="MONTHLY",
                    start_date=sub_start,
                    next_billing_date=base_now.date() + timedelta(days=15),
                    end_date=None if sub_status != "CANCELLED" else base_now.date(),
                    status=sub_status
                )
                subscriptions.append(sub)

                # Recurring billing schedules
                for s_i in range(1, 5):
                    sched_start = sub_start + timedelta(days=(s_i - 1) * 30)
                    sched_end = sched_start + timedelta(days=29)
                    sched_amt = Decimal("36000.00")
                    sched = BillingSchedule(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        subscription_id=sub.id,
                        billing_period_start=sched_start,
                        billing_period_end=sched_end,
                        billing_date=sched_start,
                        amount=sched_amt,
                        status="PAID" if sched_start < base_now.date() else "SCHEDULED",
                        invoice_id=None
                    )
                    billing_schedules.append(sched)

                if sub_status == "CANCELLED":
                    sc = SubscriptionCancellation(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        subscription_id=sub.id,
                        cancellation_type="END_OF_PERIOD",
                        reason="Corporate restructuring / consolidated billing",
                        requested_by_user_id=primary_admin.id,
                        effective_date=base_now.date(),
                        notes="Customer confirmed cancellation"
                    )
                    subscription_cancellations.append(sc)

            # Deal Health Snapshot & Monitoring Anomaly
            health_score = rnd.randint(20, 95)
            health_status = "HEALTHY" if health_score >= 75 else ("ATTENTION" if health_score >= 50 else ("AT_RISK" if health_score >= 30 else "CRITICAL"))
            dhs = DealHealthSnapshot(
                id=uuid.uuid4(),
                organization_id=org_id,
                deal_id=deal.id,
                score=health_score,
                status=health_status,
                positive_drivers=["Strong executive engagement", "Healthy gross margins", "Clear procurement timeline"] if health_score >= 60 else ["Standard catalog products"],
                negative_drivers=["Negotiation stalled >14 days", "High discount pressure"] if health_score < 60 else [],
                metrics_snapshot={"score": health_score, "days_in_stage": rnd.randint(3, 40)},
                calculated_at=q_date + timedelta(days=5),
                calculation_version="1.0"
            )
            deal_health_snapshots.append(dhs)

            if health_score < 50:
                me = MonitoringEvent(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    event_type=rnd.choice(["STALLED_QUOTE", "DISCOUNT_ANOMALY", "DELIVERY_SLIPPAGE"]),
                    severity="ANOMALOUS" if health_score < 35 else "WATCH",
                    entity_type="deal",
                    entity_id=deal.id,
                    title=f"Anomaly Alert: Deal {deal.deal_number} Requires Attention",
                    summary=f"Commercial risk telemetry triggered for {cust.name}.",
                    evidence={"health_score": health_score, "deal_value": str(deal.value)}
                )
                monitoring_events.append(me)

                # Nudge
                dedup_str = f"{org_id}:{deal.id}:{q_idx}"
                dedup_h = hashlib.sha256(dedup_str.encode()).hexdigest()
                ndg = Nudge(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    nudge_type="DEAL_STALLED",
                    severity="WARNING" if health_score < 35 else "INFO",
                    title=f"Follow up with {cust.name}",
                    message=f"Deal {deal.deal_number} has been inactive. Recommended next action: Schedule executive alignment call.",
                    entity_type="deal",
                    entity_id=deal.id,
                    dedup_hash=dedup_h,
                    status="OPEN",
                    assigned_user_id=assigned_rep.id,
                    acknowledged_at=None,
                    completed_at=None,
                    dismissed_at=None,
                    escalated_at=None,
                    action_payload={"deal_number": deal.deal_number, "customer_name": cust.name}
                )
                nudges.append(ndg)

                ndg_hist = NudgeHistory(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    nudge_id=ndg.id,
                    from_status=None,
                    to_status="OPEN",
                    actor_id=primary_admin.id,
                    actor_name=primary_admin.full_name,
                    notes="Generated automatically by Deal Health Telemetry Engine"
                )
                nudge_histories.append(ndg_hist)

            # CRM Activities
            act = Activity(
                id=uuid.uuid4(),
                organization_id=org_id,
                activity_type=rnd.choice(["call", "meeting", "email", "task", "follow_up"]),
                title=f"Client interaction with {cust.name}",
                description=f"Commercial alignment and requirement review regarding {deal.deal_number}.",
                status="completed" if days_ago > 10 else "pending",
                priority=rnd.choice(["low", "medium", "high", "urgent"]),
                customer_id=cust.id,
                contact_id=contact.id if contact else None,
                deal_id=deal.id,
                quotation_id=quote.id,
                assigned_to_user_id=assigned_rep.id,
                created_by_user_id=assigned_rep.id,
                due_at=q_date + timedelta(days=2),
                completed_at=q_date + timedelta(days=2) if days_ago > 10 else None
            )
            activities.append(act)

        # Batch Insert All Commercial & Workflow Entities in strict dependency order
        session.add_all(deals)
        await session.flush()

        session.add_all(quotations)
        await session.flush()

        for d, q in zip(deals, quotations):
            d.quotation_id = q.id
        await session.flush()

        session.add_all(quotation_items)
        session.add_all(quotation_state_histories)
        session.add_all(quotation_versions)
        session.add_all(billing_classifications)
        await session.flush()

        session.add_all(quotation_approvals)
        session.add_all(quotation_comments)
        session.add_all(quotation_changes)
        session.add_all(warehouse_allocations)
        session.add_all(inventory_reservations)
        session.add_all(shipments)
        await session.flush()

        session.add_all(approval_audit_logs)
        session.add_all(shipment_lines)
        session.add_all(backorders)
        session.add_all(delivery_promises)
        session.add_all(invoices)
        await session.flush()

        session.add_all(invoice_items)
        session.add_all(payments)
        await session.flush()

        session.add_all(credit_notes)
        session.add_all(subscriptions)
        await session.flush()

        session.add_all(credit_note_items)
        session.add_all(payment_refunds)
        session.add_all(billing_schedules)
        session.add_all(subscription_cancellations)
        session.add_all(deal_health_snapshots)
        session.add_all(monitoring_events)
        session.add_all(nudges)
        await session.flush()

        session.add_all(nudge_histories)
        session.add_all(activities)
        await session.flush()

        # =========================================================================
        # 10. AUTOMATION RULES & EXECUTIONS (5 Rules, 80 Executions, 80 Actions)
        # =========================================================================
        automation_rules: List[AutomationRule] = []
        automation_execs: List[AutomationExecution] = []
        automation_actions: List[AutomationExecutionAction] = []

        auto_rule_templates = [
            ("High-Value Deal Executive Alert", "DEAL_CREATED", {"field": "value", "operator": "gte", "value": 500000}, [{"action": "NOTIFY_EXECUTIVE", "channel": "SLACK"}]),
            ("Quotation Stalled Auto-Nudge", "QUOTATION_STALLED", {"field": "days_idle", "operator": "gte", "value": 7}, [{"action": "CREATE_NUDGE", "severity": "WARNING"}]),
            ("Auto-Invoice on Shipment Delivery", "SHIPMENT_DELIVERED", {"field": "status", "operator": "eq", "value": "DELIVERED"}, [{"action": "GENERATE_INVOICE", "auto_send": True}]),
            ("Overdue Payment Escalation", "INVOICE_OVERDUE", {"field": "days_overdue", "operator": "gte", "value": 15}, [{"action": "CREATE_COLLECTION_TASK", "priority": "HIGH"}]),
            ("At-Risk Deal Health Mitigation Trigger", "HEALTH_DROPPED", {"field": "score", "operator": "lt", "value": 40}, [{"action": "ASSIGN_CSM", "notify": "SALES_LEAD"}]),
        ]

        for i, (r_name, trig, cond, acts) in enumerate(auto_rule_templates, 1):
            ar = AutomationRule(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=r_name,
                description=f"Deterministic enterprise workflow automation rule #{i}",
                status="ACTIVE",
                priority=i * 10,
                trigger_type=trig,
                conditions=cond,
                actions=acts,
                created_by_user_id=primary_admin.id,
                updated_by_user_id=primary_admin.id
            )
            automation_rules.append(ar)

        session.add_all(automation_rules)
        await session.flush()

        auto_exec_count = cfg.get("automation_executions", 80)
        for i in range(auto_exec_count):
            r = automation_rules[i % len(automation_rules)]
            target_deal = deals[i % len(deals)]
            e_status = rnd.choice(["SUCCESS", "SUCCESS", "SUCCESS", "FAILED", "PARTIAL_SUCCESS"])
            exec_idempotency = f"exec:{r.id}:{target_deal.id}:{i}"

            exec_record = AutomationExecution(
                id=uuid.uuid4(),
                organization_id=org_id,
                rule_id=r.id,
                event_type=r.trigger_type,
                entity_type="deal",
                entity_id=target_deal.id,
                status=e_status,
                idempotency_key=exec_idempotency,
                conditions_matched=True,
                actions_total=len(r.actions),
                actions_succeeded=len(r.actions) if e_status == "SUCCESS" else 0,
                actions_failed=0 if e_status == "SUCCESS" else len(r.actions),
                error_message="Simulated endpoint timeout in action handler" if e_status == "FAILED" else None,
                retry_count=0 if e_status == "SUCCESS" else 2,
                trigger_context={"deal_id": str(target_deal.id), "deal_number": target_deal.deal_number},
                started_at=base_now - timedelta(days=rnd.randint(1, 60)),
                completed_at=base_now - timedelta(days=rnd.randint(1, 60))
            )
            automation_execs.append(exec_record)

            act_record = AutomationExecutionAction(
                id=uuid.uuid4(),
                execution_id=exec_record.id,
                action_type=r.actions[0]["action"],
                status="SUCCESS" if e_status == "SUCCESS" else "FAILED",
                result_payload={"dispatched": True, "target": target_deal.deal_number},
                error_message="Action failed" if e_status == "FAILED" else None,
                executed_at=exec_record.started_at
            )
            automation_actions.append(act_record)

        session.add_all(automation_execs)
        await session.flush()
        session.add_all(automation_actions)

        # Commit Entire Bulk Dataset
        await session.commit()

        # =========================================================================
        # 11. CALCULATE FINAL TOTALS & VALIDATION
        # =========================================================================
        summary = {
            "tenants": 2,
            "users": len(users),
            "customers": len(customers),
            "contacts": len(contacts),
            "portal_users": len(portal_users),
            "products": len(products),
            "product_variants": len(product_variants),
            "warehouses": len(warehouses),
            "inventory_stocks": len(inventory_stocks),
            "inventory_movements": len(inventory_movements),
            "pricing_rules": len(pricing_rules),
            "discount_policies": len(discount_policies),
            "recommendation_rules": len(rec_rules),
            "approval_rules": len(approval_rules),
            "deals": len(deals),
            "quotations": len(quotations),
            "quotation_items": len(quotation_items),
            "quotation_state_histories": len(quotation_state_histories),
            "quotation_approvals": len(quotation_approvals),
            "approval_audit_logs": len(approval_audit_logs),
            "quotation_comments": len(quotation_comments),
            "quotation_changes": len(quotation_changes),
            "quotation_versions": len(quotation_versions),
            "warehouse_allocations": len(warehouse_allocations),
            "billing_classifications": len(billing_classifications),
            "inventory_reservations": len(inventory_reservations),
            "shipments": len(shipments),
            "shipment_lines": len(shipment_lines),
            "backorders": len(backorders),
            "delivery_promises": len(delivery_promises),
            "invoices": len(invoices),
            "invoice_items": len(invoice_items),
            "payments": len(payments),
            "credit_notes": len(credit_notes),
            "credit_note_items": len(credit_note_items),
            "payment_refunds": len(payment_refunds),
            "subscriptions": len(subscriptions),
            "billing_schedules": len(billing_schedules),
            "subscription_cancellations": len(subscription_cancellations),
            "deal_health_snapshots": len(deal_health_snapshots),
            "monitoring_events": len(monitoring_events),
            "nudges": len(nudges),
            "nudge_histories": len(nudge_histories),
            "activities": len(activities),
            "automation_rules": len(automation_rules),
            "automation_executions": len(automation_execs),
            "automation_execution_actions": len(automation_actions),
        }
        total_records = sum(summary.values())
        summary["total_records"] = total_records
        logger.info(f"Resized bulk data seeding completed successfully! Total records: {total_records}")
        return summary

    except Exception as exc:
        await session.rollback()
        logger.error(f"Error seeding bulk data: {exc}", exc_info=True)
        raise exc
    finally:
        if should_close:
            await session.close()

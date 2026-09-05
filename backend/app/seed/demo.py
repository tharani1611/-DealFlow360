import asyncio
import uuid
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from sqlalchemy import select, and_

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User
from app.models.customer import Customer
from app.models.contact import Contact
from app.models.product import Product
from app.models.quotation import Quotation, QuotationItem
from app.models.deal import Deal
from app.models.activity import Activity
from app.models.product_recommendation_rule import ProductRecommendationRule


async def seed_demo_data():
    """Seeds synthetic demo organization data safely and idempotently."""
    if settings.APP_ENV == "production":
        print("[ERROR] Demo seeding is strictly disabled in production environments.")
        return

    async with AsyncSessionLocal() as db:
        print("[SEED] Seeding DealFlow360 Demo Enterprise Telemetry...")

        # 1. Check or create demo org
        org_q = await db.execute(select(Organization).where(Organization.slug == "demo-org"))
        org = org_q.scalar_one_or_none()

        if not org:
            org = Organization(
                id=uuid.uuid4(),
                name="Demo Enterprise Systems",
                slug="demo-org",
                is_active=True
            )
            db.add(org)
            await db.commit()
            await db.refresh(org)
            print(f"[OK] Created Demo Organization: {org.name} ({org.slug})")
        else:
            print(f"[INFO] Demo Organization exists: {org.name}")

        # 2. Check or create demo user
        user_q = await db.execute(select(User).where(User.email == "demo@dealflow360.com"))
        user = user_q.scalar_one_or_none()

        if not user:
            user = User(
                id=uuid.uuid4(),
                organization_id=org.id,
                email="demo@dealflow360.com",
                full_name="Alex Mercer (Demo Lead)",
                password_hash=hash_password("Demo123!"),
                is_active=True,
                is_admin=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print("[OK] Created Demo User: demo@dealflow360.com (Password: Demo123!)")

        # 3. Create synthetic customers if empty
        cust_q = await db.execute(select(Customer).where(Customer.organization_id == org.id))
        existing_custs = list(cust_q.scalars().all())

        if len(existing_custs) == 0:
            acme = Customer(id=uuid.uuid4(), organization_id=org.id, name="Acme Industries", email="info@acme.com", phone="+1 555 0192", city="New York", country="USA")
            nova = Customer(id=uuid.uuid4(), organization_id=org.id, name="Nova Retail Group", email="contact@novaretail.com", phone="+1 555 0184", city="Chicago", country="USA")
            orbit = Customer(id=uuid.uuid4(), organization_id=org.id, name="Orbit Cloud Systems", email="hello@orbitsystems.io", phone="+1 555 0177", city="San Francisco", country="USA")
            vertex = Customer(id=uuid.uuid4(), organization_id=org.id, name="Vertex Global Solutions", email="sales@vertex.com", phone="+1 555 0161", city="Austin", country="USA")

            db.add_all([acme, nova, orbit, vertex])
            await db.commit()
            print("[OK] Created 4 Synthetic Customer Accounts.")

            # Add Contacts
            c1 = Contact(id=uuid.uuid4(), organization_id=org.id, customer_id=acme.id, first_name="Robert", last_name="Vance", email="r.vance@acme.com", job_title="VP Procurement", is_primary=True)
            c2 = Contact(id=uuid.uuid4(), organization_id=org.id, customer_id=nova.id, first_name="Sarah", last_name="Connor", email="s.connor@novaretail.com", job_title="Director Operations", is_primary=True)
            c3 = Contact(id=uuid.uuid4(), organization_id=org.id, customer_id=orbit.id, first_name="David", last_name="Miller", email="d.miller@orbitsystems.io", job_title="CTO", is_primary=True)

            db.add_all([c1, c2, c3])

            # Add Products
            p0 = Product(id=uuid.uuid4(), organization_id=org.id, name="Standard Cloud CRM", sku="SKU-CLOUD-STD", unit_price=Decimal("10000.00"), currency="USD")
            p1 = Product(id=uuid.uuid4(), organization_id=org.id, name="Enterprise Cloud Platform", sku="SKU-CLOUD-ENT", unit_price=Decimal("25000.00"), currency="USD")
            p2 = Product(id=uuid.uuid4(), organization_id=org.id, name="AI Analytics Suite Addon", sku="SKU-AI-ADDON", unit_price=Decimal("7500.00"), currency="USD")

            db.add_all([p0, p1, p2])
            await db.commit()

            # Add Recommendation Rules
            r1 = ProductRecommendationRule(
                id=uuid.uuid4(),
                organization_id=org.id,
                source_product_id=p0.id,
                target_product_id=p1.id,
                rule_type="upsell",
                priority=1,
                is_active=True,
                description="Upgrade from Standard to Enterprise Cloud Platform for expanded capacity."
            )
            r2 = ProductRecommendationRule(
                id=uuid.uuid4(),
                organization_id=org.id,
                source_product_id=p0.id,
                target_product_id=p2.id,
                rule_type="cross_sell",
                priority=2,
                is_active=True,
                description="Complementary AI analytics suite for predictive pipeline forecasting."
            )
            r3 = ProductRecommendationRule(
                id=uuid.uuid4(),
                organization_id=org.id,
                source_product_id=p1.id,
                target_product_id=p2.id,
                rule_type="cross_sell",
                priority=1,
                is_active=True,
                description="Complementary AI analytics package for Enterprise clients."
            )
            db.add_all([r1, r2, r3])
            await db.commit()

            # Add Quotation
            q1 = Quotation(
                id=uuid.uuid4(),
                organization_id=org.id,
                customer_id=acme.id,
                quotation_number="QT-000001",
                status="accepted",
                subtotal=Decimal("10000.00"),
                discount_amount=Decimal("0.00"),
                tax_amount=Decimal("0.00"),
                total_amount=Decimal("10000.00"),
                notes="Standard enterprise commercial terms."
            )
            db.add(q1)
            await db.commit()

            qi1 = QuotationItem(
                id=uuid.uuid4(),
                quotation_id=q1.id,
                product_id=p0.id,
                product_name=p0.name,
                quantity=Decimal("1.00"),
                unit_price=Decimal("10000.00"),
                line_total=Decimal("10000.00")
            )
            db.add(qi1)

            # Add Deals
            now = datetime.now(timezone.utc)
            d1 = Deal(
                id=uuid.uuid4(),
                organization_id=org.id,
                customer_id=acme.id,
                contact_id=c1.id,
                quotation_id=q1.id,
                deal_number="DEAL-000001",
                title="Acme Digital Transformation Contract",
                stage="proposal",
                status="open",
                value=Decimal("75000.00"),
                probability=70,
                expected_close_date=now.date() + timedelta(days=12)
            )
            d2 = Deal(
                id=uuid.uuid4(),
                organization_id=org.id,
                customer_id=nova.id,
                contact_id=c2.id,
                deal_number="DEAL-000002",
                title="Nova Retail Expansion Opportunity",
                stage="qualified",
                status="open",
                value=Decimal("45000.00"),
                probability=40,
                expected_close_date=now.date() + timedelta(days=5)
            )
            d3 = Deal(
                id=uuid.uuid4(),
                organization_id=org.id,
                customer_id=orbit.id,
                contact_id=c3.id,
                deal_number="DEAL-000003",
                title="Orbit Cloud Platform Upgrade",
                stage="won",
                status="won",
                value=Decimal("120000.00"),
                probability=100
            )

            db.add_all([d1, d2, d3])
            await db.commit()

            # Add Activities (including overdue)
            a1 = Activity(
                id=uuid.uuid4(),
                organization_id=org.id,
                customer_id=acme.id,
                deal_id=d1.id,
                activity_type="call",
                title="Follow up on Acme proposal review",
                priority="high",
                status="pending",
                due_at=now - timedelta(days=2)  # Overdue
            )
            a2 = Activity(
                id=uuid.uuid4(),
                organization_id=org.id,
                customer_id=nova.id,
                deal_id=d2.id,
                activity_type="meeting",
                title="Technical review meeting with Sarah",
                priority="urgent",
                status="pending",
                due_at=now + timedelta(days=1)
            )
            a3 = Activity(
                id=uuid.uuid4(),
                organization_id=org.id,
                customer_id=orbit.id,
                deal_id=d3.id,
                activity_type="task",
                title="Onboarding kickoff session",
                priority="medium",
                status="completed"
            )

            db.add_all([a1, a2, a3])
            await db.commit()
            print("[OK] Created synthetic deals, quotations, and activity telemetry.")

        print("[SUCCESS] Demo Enterprise Seed Complete! Log in with: demo@dealflow360.com / Demo123!")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())

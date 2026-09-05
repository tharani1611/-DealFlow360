import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import Numeric, ForeignKeyConstraint, UniqueConstraint, CheckConstraint
from app.core.database import Base
from app.models.organization import Organization
from app.models.user import User
from app.models.customer import Customer
from app.models.contact import Contact
from app.models.product import Product


def test_models_metadata_registered():
    """Verify all 5 core models are registered in Base.metadata."""
    table_names = list(Base.metadata.tables.keys())
    assert "organizations" in table_names
    assert "users" in table_names
    assert "customers" in table_names
    assert "contacts" in table_names
    assert "products" in table_names


def test_organization_model_structure():
    """Verify Organization table columns, constraints, and defaults."""
    table = Organization.__table__
    assert table.name == "organizations"
    assert "id" in table.columns
    assert "name" in table.columns
    assert "slug" in table.columns
    assert "is_active" in table.columns

    # Verify column defaults
    assert table.columns["is_active"].default.arg is True

    # Test instantiation
    org = Organization(name="Acme Corp", slug="acme-corp", is_active=True)
    assert org.name == "Acme Corp"
    assert org.slug == "acme-corp"
    assert org.is_active is True


def test_user_model_structure_and_tenant_constraints():
    """Verify User model foreign keys, unique constraint per org, and attributes."""
    table = User.__table__
    assert table.name == "users"
    assert "organization_id" in table.columns
    assert "email" in table.columns
    assert "password_hash" in table.columns
    assert "is_admin" in table.columns

    # Verify column defaults
    assert table.columns["is_active"].default.arg is True
    assert table.columns["is_admin"].default.arg is False

    # Verify composite unique constraint (organization_id, email)
    uq_names = [c.name for c in table.constraints if isinstance(c, UniqueConstraint)]
    assert "uq_users_organization_id_email" in uq_names

    # Test instantiation
    org_id = uuid.uuid4()
    user = User(
        organization_id=org_id,
        email="alice@acme.com",
        full_name="Alice Smith",
        password_hash="$2b$12$e...",
        is_admin=False,
        is_active=True
    )
    assert user.organization_id == org_id
    assert user.email == "alice@acme.com"
    assert user.is_admin is False
    assert user.is_active is True


def test_customer_and_contact_models_structure():
    """Verify Customer and Contact relationships and field constraints."""
    customer_table = Customer.__table__
    contact_table = Contact.__table__

    assert customer_table.name == "customers"
    assert contact_table.name == "contacts"

    # Instantiate Customer and Contact
    org_id = uuid.uuid4()
    cust_id = uuid.uuid4()

    customer = Customer(
        id=cust_id,
        organization_id=org_id,
        name="Global Logistics Inc",
        email="info@globallogistics.com"
    )
    assert customer.organization_id == org_id
    assert customer.name == "Global Logistics Inc"

    contact = Contact(
        organization_id=org_id,
        customer_id=cust_id,
        first_name="Bob",
        last_name="Johnson",
        email="b.johnson@globallogistics.com",
        is_primary=True
    )
    assert contact.organization_id == org_id
    assert contact.customer_id == cust_id
    assert contact.first_name == "Bob"
    assert contact.is_primary is True


def test_product_model_monetary_precision_and_constraints():
    """Verify Product decimal unit_price, SKU unique constraint per org, and non-negative check constraint."""
    table = Product.__table__
    assert table.name == "products"
    
    # Check unit_price column is Numeric/Decimal
    assert isinstance(table.columns["unit_price"].type, Numeric)
    
    # Check composite unique constraint (organization_id, sku)
    uq_names = [c.name for c in table.constraints if isinstance(c, UniqueConstraint)]
    assert "uq_products_organization_id_sku" in uq_names

    # Check non-negative unit_price constraint
    ck_names = [c.name for c in table.constraints if isinstance(c, CheckConstraint)]
    assert "ck_products_unit_price_non_negative" in ck_names

    # Test instantiation
    org_id = uuid.uuid4()
    prod = Product(
        organization_id=org_id,
        name="Enterprise Server X1",
        sku="SERVER-X1",
        unit_price=Decimal("4999.99"),
        currency="USD"
    )
    assert prod.organization_id == org_id
    assert prod.sku == "SERVER-X1"
    assert isinstance(prod.unit_price, Decimal)
    assert prod.unit_price == Decimal("4999.99")
    assert prod.currency == "USD"


def test_relationships_linking():
    """Verify model relationship mappings work in memory."""
    org = Organization(id=uuid.uuid4(), name="Test Org", slug="test-org")
    user = User(organization_id=org.id, email="user@test.org", password_hash="hash")
    customer = Customer(organization_id=org.id, name="Test Customer")
    contact = Contact(organization_id=org.id, customer=customer, first_name="John")
    product = Product(organization_id=org.id, name="Widget", sku="W-01", unit_price=Decimal("10.00"))

    org.users.append(user)
    org.customers.append(customer)
    org.products.append(product)

    assert len(org.users) == 1
    assert org.users[0].email == "user@test.org"
    assert len(org.customers) == 1
    assert len(org.products) == 1
    assert contact.customer.name == "Test Customer"

"""Add core organization, user, customer, contact, and product models

Revision ID: 000000000001
Revises: 000000000000
Create Date: 2026-09-05 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000000000001'
down_revision: Union[str, None] = '000000000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_organizations')),
        sa.UniqueConstraint('slug', name=op.f('uq_organizations_slug'))
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    # 2. Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_admin', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_users_organization_id_organizations'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('organization_id', 'email', name=op.f('uq_users_organization_id_email'))
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)

    # 3. Create customers table
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_customers_organization_id_organizations'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_customers'))
    )
    op.create_index(op.f('ix_customers_id'), 'customers', ['id'], unique=False)
    op.create_index(op.f('ix_customers_organization_id'), 'customers', ['organization_id'], unique=False)
    op.create_index('ix_customers_organization_id_name', 'customers', ['organization_id', 'name'], unique=False)

    # 4. Create contacts table
    op.create_table(
        'contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=False),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('job_title', sa.String(length=255), nullable=True),
        sa.Column('is_primary', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], name=op.f('fk_contacts_customer_id_customers'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_contacts_organization_id_organizations'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_contacts'))
    )
    op.create_index(op.f('ix_contacts_customer_id'), 'contacts', ['customer_id'], unique=False)
    op.create_index(op.f('ix_contacts_id'), 'contacts', ['id'], unique=False)
    op.create_index(op.f('ix_contacts_organization_id'), 'contacts', ['organization_id'], unique=False)
    op.create_index('ix_contacts_organization_id_customer_id', 'contacts', ['organization_id', 'customer_id'], unique=False)

    # 5. Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('unit_price >= 0', name=op.f('ck_products_unit_price_non_negative')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_products_organization_id_organizations'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_products')),
        sa.UniqueConstraint('organization_id', 'sku', name=op.f('uq_products_organization_id_sku'))
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_organization_id'), 'products', ['organization_id'], unique=False)
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=False)
    op.create_index('ix_products_organization_id_sku', 'products', ['organization_id', 'sku'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_products_organization_id_sku', table_name='products')
    op.drop_index(op.f('ix_products_sku'), table_name='products')
    op.drop_index(op.f('ix_products_organization_id'), table_name='products')
    op.drop_index(op.f('ix_products_id'), table_name='products')
    op.drop_table('products')

    op.drop_index('ix_contacts_organization_id_customer_id', table_name='contacts')
    op.drop_index(op.f('ix_contacts_organization_id'), table_name='contacts')
    op.drop_index(op.f('ix_contacts_id'), table_name='contacts')
    op.drop_index(op.f('ix_contacts_customer_id'), table_name='contacts')
    op.drop_table('contacts')

    op.drop_index('ix_customers_organization_id_name', table_name='customers')
    op.drop_index(op.f('ix_customers_organization_id'), table_name='customers')
    op.drop_index(op.f('ix_customers_id'), table_name='customers')
    op.drop_table('customers')

    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')

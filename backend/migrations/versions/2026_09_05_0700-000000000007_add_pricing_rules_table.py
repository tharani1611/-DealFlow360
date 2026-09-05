"""Add pricing_rules table for Quotation Pricing Engine (Phase 20)

Revision ID: 000000000007
Revises: 000000000006
Create Date: 2026-09-05 07:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '000000000007'
down_revision: Union[str, None] = '000000000006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pricing_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('min_quantity', sa.Numeric(precision=10, scale=2), server_default='1.00', nullable=False),
        sa.Column('max_quantity', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('price_type', sa.String(length=50), server_default='override_price', nullable=False),
        sa.Column('value', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='100', nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.CheckConstraint('min_quantity > 0', name='ck_pricing_rules_min_quantity_positive'),
        sa.CheckConstraint('value >= 0', name='ck_pricing_rules_value_non_negative'),
        sa.CheckConstraint('priority > 0', name='ck_pricing_rules_priority_positive'),
        sa.CheckConstraint("rule_type IN ('contract', 'customer', 'volume', 'promotion')", name='ck_pricing_rules_rule_type_valid'),
        sa.CheckConstraint("price_type IN ('override_price', 'percentage_discount', 'fixed_discount')", name='ck_pricing_rules_price_type_valid')
    )

    op.create_index('ix_pricing_rules_organization_id', 'pricing_rules', ['organization_id'])
    op.create_index('ix_pricing_rules_product_id', 'pricing_rules', ['product_id'])
    op.create_index('ix_pricing_rules_customer_id', 'pricing_rules', ['customer_id'])
    op.create_index('ix_pricing_rules_org_product', 'pricing_rules', ['organization_id', 'product_id'])
    op.create_index('ix_pricing_rules_org_customer', 'pricing_rules', ['organization_id', 'customer_id'])
    op.create_index('ix_pricing_rules_org_active', 'pricing_rules', ['organization_id', 'is_active'])
    op.create_index('ix_pricing_rules_lookup', 'pricing_rules', ['organization_id', 'product_id', 'is_active', 'priority'])


def downgrade() -> None:
    op.drop_index('ix_pricing_rules_lookup', table_name='pricing_rules')
    op.drop_index('ix_pricing_rules_org_active', table_name='pricing_rules')
    op.drop_index('ix_pricing_rules_org_customer', table_name='pricing_rules')
    op.drop_index('ix_pricing_rules_org_product', table_name='pricing_rules')
    op.drop_index('ix_pricing_rules_customer_id', table_name='pricing_rules')
    op.drop_index('ix_pricing_rules_product_id', table_name='pricing_rules')
    op.drop_index('ix_pricing_rules_organization_id', table_name='pricing_rules')
    op.drop_table('pricing_rules')

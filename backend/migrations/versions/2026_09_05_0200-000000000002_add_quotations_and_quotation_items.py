"""Add quotations and quotation_items models

Revision ID: 000000000002
Revises: 000000000001
Create Date: 2026-09-05 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '000000000002'
down_revision: Union[str, None] = '000000000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create quotations table
    op.create_table(
        'quotations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quotation_number', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='draft', nullable=False),
        sa.Column('quotation_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('subtotal >= 0', name=op.f('ck_quotations_subtotal_non_negative')),
        sa.CheckConstraint('discount_amount >= 0', name=op.f('ck_quotations_discount_non_negative')),
        sa.CheckConstraint('tax_amount >= 0', name=op.f('ck_quotations_tax_non_negative')),
        sa.CheckConstraint('total_amount >= 0', name=op.f('ck_quotations_total_non_negative')),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], name=op.f('fk_quotations_customer_id_customers'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_quotations_organization_id_organizations'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_quotations')),
        sa.UniqueConstraint('organization_id', 'quotation_number', name=op.f('uq_quotations_organization_id_quotation_number'))
    )
    op.create_index(op.f('ix_quotations_customer_id'), 'quotations', ['customer_id'], unique=False)
    op.create_index(op.f('ix_quotations_id'), 'quotations', ['id'], unique=False)
    op.create_index(op.f('ix_quotations_organization_id'), 'quotations', ['organization_id'], unique=False)
    op.create_index(op.f('ix_quotations_quotation_number'), 'quotations', ['quotation_number'], unique=False)
    op.create_index('ix_quotations_org_status', 'quotations', ['organization_id', 'status'], unique=False)

    # 2. Create quotation_items table
    op.create_table(
        'quotation_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('line_total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('quantity > 0', name=op.f('ck_quotation_items_quantity_positive')),
        sa.CheckConstraint('unit_price >= 0', name=op.f('ck_quotation_items_price_non_negative')),
        sa.CheckConstraint('line_total >= 0', name=op.f('ck_quotation_items_line_total_non_negative')),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name=op.f('fk_quotation_items_product_id_products'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], name=op.f('fk_quotation_items_quotation_id_quotations'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_quotation_items'))
    )
    op.create_index(op.f('ix_quotation_items_id'), 'quotation_items', ['id'], unique=False)
    op.create_index(op.f('ix_quotation_items_product_id'), 'quotation_items', ['product_id'], unique=False)
    op.create_index(op.f('ix_quotation_items_quotation_id'), 'quotation_items', ['quotation_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_quotation_items_quotation_id'), table_name='quotation_items')
    op.drop_index(op.f('ix_quotation_items_product_id'), table_name='quotation_items')
    op.drop_index(op.f('ix_quotation_items_id'), table_name='quotation_items')
    op.drop_table('quotation_items')

    op.drop_index('ix_quotations_org_status', table_name='quotations')
    op.drop_index(op.f('ix_quotations_quotation_number'), table_name='quotations')
    op.drop_index(op.f('ix_quotations_customer_id'), table_name='quotations')
    op.drop_index(op.f('ix_quotations_organization_id'), table_name='quotations')
    op.drop_index(op.f('ix_quotations_id'), table_name='quotations')
    op.drop_table('quotations')

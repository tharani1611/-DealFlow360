"""Enhance quotation and quotation_items data model for Phase 18

Revision ID: 000000000006
Revises: 000000000005
Create Date: 2026-09-05 06:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '000000000006'
down_revision: Union[str, None] = '000000000005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enhance quotations table
    op.add_column('quotations', sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('quotations', sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('quotations', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('quotations', sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False))
    op.add_column('quotations', sa.Column('terms', sa.Text(), nullable=True))
    op.add_column('quotations', sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('quotations', sa.Column('updated_by_user_id', postgresql.UUID(as_uuid=True), nullable=True))

    op.create_foreign_key(op.f('fk_quotations_contact_id_contacts'), 'quotations', 'contacts', ['contact_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(op.f('fk_quotations_deal_id_deals'), 'quotations', 'deals', ['deal_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(op.f('fk_quotations_created_by_user_id_users'), 'quotations', 'users', ['created_by_user_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(op.f('fk_quotations_updated_by_user_id_users'), 'quotations', 'users', ['updated_by_user_id'], ['id'], ondelete='SET NULL')

    op.create_index(op.f('ix_quotations_contact_id'), 'quotations', ['contact_id'], unique=False)
    op.create_index(op.f('ix_quotations_deal_id'), 'quotations', ['deal_id'], unique=False)
    op.create_index(op.f('ix_quotations_created_by_user_id'), 'quotations', ['created_by_user_id'], unique=False)
    op.create_index(op.f('ix_quotations_updated_by_user_id'), 'quotations', ['updated_by_user_id'], unique=False)

    # 2. Enhance quotation_items table
    op.add_column('quotation_items', sa.Column('product_variant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('quotation_items', sa.Column('sku', sa.String(length=100), nullable=True))
    op.add_column('quotation_items', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('quotation_items', sa.Column('sequence', sa.Integer(), server_default='0', nullable=False))
    op.add_column('quotation_items', sa.Column('discount_percent', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False))
    op.add_column('quotation_items', sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False))
    op.add_column('quotation_items', sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False))
    op.add_column('quotation_items', sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False))

    op.create_index(op.f('ix_quotation_items_product_variant_id'), 'quotation_items', ['product_variant_id'], unique=False)

    op.create_check_constraint('ck_quotation_items_discount_percent_range', 'quotation_items', 'discount_percent >= 0 AND discount_percent <= 100')
    op.create_check_constraint('ck_quotation_items_discount_amount_non_negative', 'quotation_items', 'discount_amount >= 0')
    op.create_check_constraint('ck_quotation_items_tax_rate_non_negative', 'quotation_items', 'tax_rate >= 0')
    op.create_check_constraint('ck_quotation_items_tax_amount_non_negative', 'quotation_items', 'tax_amount >= 0')


def downgrade() -> None:
    # 2. Downgrade quotation_items
    op.drop_constraint('ck_quotation_items_tax_amount_non_negative', 'quotation_items', type_='check')
    op.drop_constraint('ck_quotation_items_tax_rate_non_negative', 'quotation_items', type_='check')
    op.drop_constraint('ck_quotation_items_discount_amount_non_negative', 'quotation_items', type_='check')
    op.drop_constraint('ck_quotation_items_discount_percent_range', 'quotation_items', type_='check')

    op.drop_index(op.f('ix_quotation_items_product_variant_id'), table_name='quotation_items')

    op.drop_column('quotation_items', 'tax_amount')
    op.drop_column('quotation_items', 'tax_rate')
    op.drop_column('quotation_items', 'discount_amount')
    op.drop_column('quotation_items', 'discount_percent')
    op.drop_column('quotation_items', 'sequence')
    op.drop_column('quotation_items', 'description')
    op.drop_column('quotation_items', 'sku')
    op.drop_column('quotation_items', 'product_variant_id')

    # 1. Downgrade quotations
    op.drop_index(op.f('ix_quotations_updated_by_user_id'), table_name='quotations')
    op.drop_index(op.f('ix_quotations_created_by_user_id'), table_name='quotations')
    op.drop_index(op.f('ix_quotations_deal_id'), table_name='quotations')
    op.drop_index(op.f('ix_quotations_contact_id'), table_name='quotations')

    op.drop_constraint(op.f('fk_quotations_updated_by_user_id_users'), 'quotations', type_='foreignkey')
    op.drop_constraint(op.f('fk_quotations_created_by_user_id_users'), 'quotations', type_='foreignkey')
    op.drop_constraint(op.f('fk_quotations_deal_id_deals'), 'quotations', type_='foreignkey')
    op.drop_constraint(op.f('fk_quotations_contact_id_contacts'), 'quotations', type_='foreignkey')

    op.drop_column('quotations', 'updated_by_user_id')
    op.drop_column('quotations', 'created_by_user_id')
    op.drop_column('quotations', 'terms')
    op.drop_column('quotations', 'currency')
    op.drop_column('quotations', 'title')
    op.drop_column('quotations', 'deal_id')
    op.drop_column('quotations', 'contact_id')

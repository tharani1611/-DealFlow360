"""Add unit_cost to products and quotation_items for Real-time Margin Engine (Phase 21)

Revision ID: 000000000008
Revises: 000000000007
Create Date: 2026-09-05 08:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '000000000008'
down_revision: Union[str, None] = '000000000007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add unit_cost to products
    op.add_column('products', sa.Column('unit_cost', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False))
    op.create_check_constraint('unit_cost_non_negative', 'products', 'unit_cost >= 0')

    # 2. Add unit_cost to quotation_items
    op.add_column('quotation_items', sa.Column('unit_cost', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False))
    op.create_check_constraint('ck_quotation_items_cost_non_negative', 'quotation_items', 'unit_cost >= 0')


def downgrade() -> None:
    op.drop_constraint('ck_quotation_items_cost_non_negative', 'quotation_items', type_='check')
    op.drop_column('quotation_items', 'unit_cost')

    op.drop_constraint('unit_cost_non_negative', 'products', type_='check')
    op.drop_column('products', 'unit_cost')

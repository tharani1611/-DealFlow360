"""Add product recommendation rules table

Revision ID: 000000000005
Revises: 000000000004
Create Date: 2026-09-05 05:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '000000000005'
down_revision: Union[str, None] = '000000000004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'product_recommendation_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='5', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('min_customer_deal_count', sa.Integer(), nullable=True),
        sa.Column('min_customer_pipeline_value', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('min_customer_activity_count', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('source_product_id != target_product_id', name='check_source_ne_target'),
        sa.CheckConstraint("rule_type IN ('upsell', 'cross_sell')", name='check_valid_rule_type'),
        sa.CheckConstraint('priority > 0', name='check_priority_positive'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_product_recommendation_rules_organization_id_organizations'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_product_id'], ['products.id'], name=op.f('fk_product_recommendation_rules_source_product_id_products'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_product_id'], ['products.id'], name=op.f('fk_product_recommendation_rules_target_product_id_products'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_product_recommendation_rules')),
        sa.UniqueConstraint('organization_id', 'source_product_id', 'target_product_id', 'rule_type', name='uq_product_rec_rules_org_src_tgt_type')
    )
    op.create_index(op.f('ix_product_recommendation_rules_id'), 'product_recommendation_rules', ['id'], unique=False)
    op.create_index(op.f('ix_product_recommendation_rules_organization_id'), 'product_recommendation_rules', ['organization_id'], unique=False)
    op.create_index(op.f('ix_product_recommendation_rules_source_product_id'), 'product_recommendation_rules', ['source_product_id'], unique=False)
    op.create_index(op.f('ix_product_recommendation_rules_target_product_id'), 'product_recommendation_rules', ['target_product_id'], unique=False)
    op.create_index('ix_product_rec_rules_org_src', 'product_recommendation_rules', ['organization_id', 'source_product_id'], unique=False)
    op.create_index('ix_product_rec_rules_org_active', 'product_recommendation_rules', ['organization_id', 'is_active'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_product_rec_rules_org_active', table_name='product_recommendation_rules')
    op.drop_index('ix_product_rec_rules_org_src', table_name='product_recommendation_rules')
    op.drop_index(op.f('ix_product_recommendation_rules_target_product_id'), table_name='product_recommendation_rules')
    op.drop_index(op.f('ix_product_recommendation_rules_source_product_id'), table_name='product_recommendation_rules')
    op.drop_index(op.f('ix_product_recommendation_rules_organization_id'), table_name='product_recommendation_rules')
    op.drop_index(op.f('ix_product_recommendation_rules_id'), table_name='product_recommendation_rules')
    op.drop_table('product_recommendation_rules')

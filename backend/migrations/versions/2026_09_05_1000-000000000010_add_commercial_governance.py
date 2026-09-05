"""Add discount_policies, approval_rules, and quotation_approvals tables for Combined Phase 23-25 Commercial Governance

Revision ID: 000000000010
Revises: 000000000009
Create Date: 2026-09-05 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = '000000000010'
down_revision: Union[str, None] = '000000000009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Discount Policies table
    op.create_table(
        'discount_policies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='100', nullable=False),
        sa.Column('scope', sa.String(length=50), server_default='organization', nullable=False),
        sa.Column('product_id', UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('max_discount_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('max_discount_amount', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('minimum_unit_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('minimum_margin_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('priority > 0', name='ck_discount_policies_priority_positive'),
        sa.CheckConstraint("scope IN ('user', 'customer', 'product', 'role', 'organization')", name='ck_discount_policies_scope_valid'),
    )
    op.create_index('ix_discount_policies_org_scope', 'discount_policies', ['organization_id', 'scope'])
    op.create_index('ix_discount_policies_lookup', 'discount_policies', ['organization_id', 'is_active', 'priority'])

    # 2. Approval Rules table
    op.create_table(
        'approval_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='100', nullable=False),
        sa.Column('min_discount_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('max_discount_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('min_margin_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('risk_level', sa.String(length=30), nullable=True),
        sa.Column('quotation_value_threshold', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('approval_level', sa.Integer(), server_default='1', nullable=False),
        sa.Column('required_role', sa.String(length=50), server_default='admin', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('priority > 0', name='ck_approval_rules_priority_positive'),
        sa.CheckConstraint('approval_level > 0', name='ck_approval_rules_level_positive'),
    )
    op.create_index('ix_approval_rules_lookup', 'approval_rules', ['organization_id', 'is_active', 'priority'])

    # 3. Quotation Approvals table
    op.create_table(
        'quotation_approvals',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quotation_id', UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('approval_rule_id', UUID(as_uuid=True), sa.ForeignKey('approval_rules.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('requested_by_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('approved_by_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('status', sa.String(length=30), server_default='PENDING', nullable=False),
        sa.Column('approval_level', sa.Integer(), server_default='1', nullable=False),
        sa.Column('reasons', sa.Text(), nullable=True),
        sa.Column('decision_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_quotation_approvals_org_quotation', 'quotation_approvals', ['organization_id', 'quotation_id'])
    op.create_index('ix_quotation_approvals_status', 'quotation_approvals', ['status'])


def downgrade() -> None:
    op.drop_table('quotation_approvals')
    op.drop_table('approval_rules')
    op.drop_table('discount_policies')

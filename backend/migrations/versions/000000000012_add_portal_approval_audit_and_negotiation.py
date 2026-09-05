"""add portal approval audit and negotiation tables

Revision ID: 000000000012
Revises: 000000000011
Create Date: 2026-09-05 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000000000012'
down_revision: Union[str, None] = '000000000011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Approval Audit Logs
    op.create_table(
        'approval_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('approval_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotation_approvals.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('actor_name', sa.String(length=255), nullable=True),
        sa.Column('previous_status', sa.String(length=30), nullable=True),
        sa.Column('new_status', sa.String(length=30), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('approval_rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('approval_rules.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approval_level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # 2. Portal Users
    op.create_table(
        'portal_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('organization_id', 'email', name='uq_portal_users_org_email')
    )

    # 3. Quotation Line Comments
    op.create_table(
        'quotation_line_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quotation_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotation_items.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('author_type', sa.String(length=20), nullable=False, server_default='INTERNAL_USER'),  # 'INTERNAL_USER', 'CUSTOMER_PORTAL'
        sa.Column('author_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('author_portal_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('author_name', sa.String(length=255), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('is_internal_only', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # 4. Quotation Change Requests
    op.create_table(
        'quotation_change_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quotation_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotation_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('requested_by_portal_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('change_type', sa.String(length=50), nullable=False),  # 'quantity_change', 'counter_discount', 'validity_extension', 'general_terms'
        sa.Column('status', sa.String(length=30), nullable=False, server_default='OPEN'),  # 'OPEN', 'UNDER_REVIEW', 'ACCEPTED', 'REJECTED', 'WITHDRAWN'
        sa.Column('requested_discount_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('requested_quantity', sa.Numeric(10, 2), nullable=True),
        sa.Column('request_details', sa.Text(), nullable=False),
        sa.Column('response_note', sa.Text(), nullable=True),
        sa.Column('reviewed_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # 5. Quotation Versions
    op.create_table(
        'quotation_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('subtotal', sa.Numeric(12, 2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('gross_margin', sa.Numeric(12, 2), nullable=True),
        sa.Column('margin_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=False),
        sa.Column('snapshot_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('quotation_versions')
    op.drop_table('quotation_change_requests')
    op.drop_table('quotation_line_comments')
    op.drop_table('portal_users')
    op.drop_table('approval_audit_logs')

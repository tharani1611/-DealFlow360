"""Add quotation_state_history table for Quotation State Machine (Phase 22)

Revision ID: 000000000009
Revises: 000000000008
Create Date: 2026-09-05 09:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = '000000000009'
down_revision: Union[str, None] = '000000000008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'quotation_state_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('quotation_id', UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('from_status', sa.String(length=30), nullable=True),
        sa.Column('to_status', sa.String(length=30), nullable=False),
        sa.Column('changed_by_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(
        'ix_quotation_state_history_org_quotation',
        'quotation_state_history',
        ['organization_id', 'quotation_id']
    )
    op.create_index(
        'ix_quotation_state_history_created_at',
        'quotation_state_history',
        ['created_at']
    )


def downgrade() -> None:
    op.drop_index('ix_quotation_state_history_created_at', table_name='quotation_state_history')
    op.drop_index('ix_quotation_state_history_org_quotation', table_name='quotation_state_history')
    op.drop_table('quotation_state_history')

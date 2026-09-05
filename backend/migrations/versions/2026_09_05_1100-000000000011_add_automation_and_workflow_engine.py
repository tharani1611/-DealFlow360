"""Add automation_rules, automation_executions, and automation_execution_actions tables for Combined Phase 36-40 Automation Engine

Revision ID: 000000000011
Revises: 000000000010
Create Date: 2026-09-05 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = '000000000011'
down_revision: Union[str, None] = '000000000010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Automation Rules table
    op.create_table(
        'automation_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='DRAFT', nullable=False, index=True),
        sa.Column('priority', sa.Integer(), server_default='0', nullable=False),
        sa.Column('trigger_type', sa.String(length=100), nullable=False, index=True),
        sa.Column('conditions', JSONB, nullable=False, server_default='{}'),
        sa.Column('actions', JSONB, nullable=False, server_default='[]'),
        sa.Column('created_by_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # 2. Automation Executions table
    op.create_table(
        'automation_executions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('rule_id', UUID(as_uuid=True), sa.ForeignKey('automation_rules.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_type', sa.String(length=100), nullable=False, index=True),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False, index=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False, index=True),
        sa.Column('conditions_matched', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('actions_total', sa.Integer(), server_default='0', nullable=False),
        sa.Column('actions_succeeded', sa.Integer(), server_default='0', nullable=False),
        sa.Column('actions_failed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('trigger_context', JSONB, nullable=False, server_default='{}'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
    )

    # 3. Automation Execution Actions table
    op.create_table(
        'automation_execution_actions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('execution_id', UUID(as_uuid=True), sa.ForeignKey('automation_executions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='SUCCESS', nullable=False),
        sa.Column('result_payload', JSONB, nullable=False, server_default='{}'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('automation_execution_actions')
    op.drop_table('automation_executions')
    op.drop_table('automation_rules')

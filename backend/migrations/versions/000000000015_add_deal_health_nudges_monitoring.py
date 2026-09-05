"""add deal_health_snapshots nudges nudge_history and monitoring_events

Revision ID: 000000000015
Revises: 000000000014
Create Date: 2026-09-05 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '000000000015'
down_revision = '000000000014'
branch_labels = None
depends_on = None


def upgrade():
    # 1. deal_health_snapshots
    op.create_table(
        'deal_health_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ATTENTION'),
        sa.Column('positive_drivers', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('negative_drivers', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('metrics_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('calculation_version', sa.String(length=20), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deal_health_snapshots_organization_id'), 'deal_health_snapshots', ['organization_id'], unique=False)
    op.create_index(op.f('ix_deal_health_snapshots_deal_id'), 'deal_health_snapshots', ['deal_id'], unique=False)
    op.create_index(op.f('ix_deal_health_snapshots_status'), 'deal_health_snapshots', ['status'], unique=False)

    # 2. nudges
    op.create_table(
        'nudges',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nudge_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='INFO'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dedup_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='OPEN'),
        sa.Column('assigned_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('action_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['assigned_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'dedup_hash', name='uq_nudges_org_dedup')
    )
    op.create_index(op.f('ix_nudges_organization_id'), 'nudges', ['organization_id'], unique=False)
    op.create_index(op.f('ix_nudges_nudge_type'), 'nudges', ['nudge_type'], unique=False)
    op.create_index(op.f('ix_nudges_severity'), 'nudges', ['severity'], unique=False)
    op.create_index(op.f('ix_nudges_entity_type'), 'nudges', ['entity_type'], unique=False)
    op.create_index(op.f('ix_nudges_entity_id'), 'nudges', ['entity_id'], unique=False)
    op.create_index(op.f('ix_nudges_dedup_hash'), 'nudges', ['dedup_hash'], unique=False)
    op.create_index(op.f('ix_nudges_status'), 'nudges', ['status'], unique=False)

    # 3. nudge_history
    op.create_table(
        'nudge_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nudge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_status', sa.String(length=20), nullable=True),
        sa.Column('to_status', sa.String(length=20), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_name', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['nudge_id'], ['nudges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nudge_history_organization_id'), 'nudge_history', ['organization_id'], unique=False)
    op.create_index(op.f('ix_nudge_history_nudge_id'), 'nudge_history', ['nudge_id'], unique=False)

    # 4. monitoring_events
    op.create_table(
        'monitoring_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='INFO'),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_monitoring_events_organization_id'), 'monitoring_events', ['organization_id'], unique=False)
    op.create_index(op.f('ix_monitoring_events_event_type'), 'monitoring_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_monitoring_events_severity'), 'monitoring_events', ['severity'], unique=False)
    op.create_index(op.f('ix_monitoring_events_entity_type'), 'monitoring_events', ['entity_type'], unique=False)
    op.create_index(op.f('ix_monitoring_events_entity_id'), 'monitoring_events', ['entity_id'], unique=False)


def downgrade():
    op.drop_table('monitoring_events')
    op.drop_table('nudge_history')
    op.drop_table('nudges')
    op.drop_table('deal_health_snapshots')

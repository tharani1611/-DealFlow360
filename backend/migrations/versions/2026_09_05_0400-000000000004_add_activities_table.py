"""Add activities table

Revision ID: 000000000004
Revises: 000000000003
Create Date: 2026-09-05 04:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '000000000004'
down_revision: Union[str, None] = '000000000003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('priority', sa.String(length=50), server_default='medium', nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_to_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], name=op.f('fk_activities_assigned_to_user_id_users'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], name=op.f('fk_activities_contact_id_contacts'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name=op.f('fk_activities_created_by_user_id_users'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], name=op.f('fk_activities_customer_id_customers'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], name=op.f('fk_activities_deals'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_activities_organization_id_organizations'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], name=op.f('fk_activities_quotation_id_quotations'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_activities'))
    )
    op.create_index(op.f('ix_activities_assigned_to_user_id'), 'activities', ['assigned_to_user_id'], unique=False)
    op.create_index(op.f('ix_activities_contact_id'), 'activities', ['contact_id'], unique=False)
    op.create_index(op.f('ix_activities_created_by_user_id'), 'activities', ['created_by_user_id'], unique=False)
    op.create_index(op.f('ix_activities_customer_id'), 'activities', ['customer_id'], unique=False)
    op.create_index(op.f('ix_activities_deal_id'), 'activities', ['deal_id'], unique=False)
    op.create_index(op.f('ix_activities_id'), 'activities', ['id'], unique=False)
    op.create_index(op.f('ix_activities_organization_id'), 'activities', ['organization_id'], unique=False)
    op.create_index(op.f('ix_activities_quotation_id'), 'activities', ['quotation_id'], unique=False)
    op.create_index('ix_activities_organization_id_customer_id', 'activities', ['organization_id', 'customer_id'], unique=False)
    op.create_index('ix_activities_organization_id_deal_id', 'activities', ['organization_id', 'deal_id'], unique=False)
    op.create_index('ix_activities_organization_id_due_at', 'activities', ['organization_id', 'due_at'], unique=False)
    op.create_index('ix_activities_organization_id_status', 'activities', ['organization_id', 'status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_activities_organization_id_status', table_name='activities')
    op.drop_index('ix_activities_organization_id_due_at', table_name='activities')
    op.drop_index('ix_activities_organization_id_deal_id', table_name='activities')
    op.drop_index('ix_activities_organization_id_customer_id', table_name='activities')
    op.drop_index(op.f('ix_activities_quotation_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_organization_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_deal_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_customer_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_created_by_user_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_contact_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_assigned_to_user_id'), table_name='activities')
    op.drop_table('activities')

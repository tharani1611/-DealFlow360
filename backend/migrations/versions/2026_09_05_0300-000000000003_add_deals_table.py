"""Add deals table

Revision ID: 000000000003
Revises: 000000000002
Create Date: 2026-09-05 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '000000000003'
down_revision: Union[str, None] = '000000000002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'deals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('deal_number', sa.String(length=50), nullable=False),
        sa.Column('stage', sa.String(length=50), server_default='new', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='open', nullable=False),
        sa.Column('value', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('probability', sa.Integer(), server_default='10', nullable=False),
        sa.Column('expected_close_date', sa.Date(), nullable=True),
        sa.Column('lost_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('value >= 0', name=op.f('ck_deals_value_non_negative')),
        sa.CheckConstraint('probability >= 0 AND probability <= 100', name=op.f('ck_deals_probability_range')),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], name=op.f('fk_deals_contact_id_contacts'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], name=op.f('fk_deals_customer_id_customers'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_deals_organization_id_organizations'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], name=op.f('fk_deals_quotation_id_quotations'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_deals')),
        sa.UniqueConstraint('organization_id', 'deal_number', name=op.f('uq_deals_organization_id_deal_number'))
    )
    op.create_index(op.f('ix_deals_contact_id'), 'deals', ['contact_id'], unique=False)
    op.create_index(op.f('ix_deals_customer_id'), 'deals', ['customer_id'], unique=False)
    op.create_index(op.f('ix_deals_id'), 'deals', ['id'], unique=False)
    op.create_index(op.f('ix_deals_organization_id'), 'deals', ['organization_id'], unique=False)
    op.create_index(op.f('ix_deals_quotation_id'), 'deals', ['quotation_id'], unique=False)
    op.create_index('ix_deals_organization_id_customer_id', 'deals', ['organization_id', 'customer_id'], unique=False)
    op.create_index('ix_deals_organization_id_stage', 'deals', ['organization_id', 'stage'], unique=False)
    op.create_index('ix_deals_organization_id_status', 'deals', ['organization_id', 'status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_deals_organization_id_status', table_name='deals')
    op.drop_index('ix_deals_organization_id_stage', table_name='deals')
    op.drop_index('ix_deals_organization_id_customer_id', table_name='deals')
    op.drop_index(op.f('ix_deals_quotation_id'), table_name='deals')
    op.drop_index(op.f('ix_deals_organization_id'), table_name='deals')
    op.drop_index(op.f('ix_deals_id'), table_name='deals')
    op.drop_index(op.f('ix_deals_customer_id'), table_name='deals')
    op.drop_index(op.f('ix_deals_contact_id'), table_name='deals')
    op.drop_table('deals')

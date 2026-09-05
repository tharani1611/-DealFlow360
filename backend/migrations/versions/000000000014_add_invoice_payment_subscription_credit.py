"""add invoice payment subscription and credit note tables

Revision ID: 000000000014
Revises: 000000000013
Create Date: 2026-09-05 21:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000000000014'
down_revision: Union[str, None] = '000000000013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Invoices
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('invoice_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('currency', sa.String(length=3), server_default=sa.text("'USD'"), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('discount_total', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('tax_total', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('total', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('amount_paid', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('amount_due', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('status', sa.String(length=30), server_default=sa.text("'DRAFT'"), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'invoice_number', name='uq_invoices_org_invoice_number'),
    )

    # 2. Invoice Items
    op.create_table(
        'invoice_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True),
        sa.Column('product_variant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_variants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('quotation_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotation_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), server_default='1.00', nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('line_subtotal', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('line_total', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('billing_type', sa.String(length=20), server_default=sa.text("'ONE_TIME'"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 3. Payments
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('payment_reference', sa.String(length=50), nullable=False, index=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('method', sa.String(length=30), server_default=sa.text("'BANK_TRANSFER'"), nullable=False),
        sa.Column('status', sa.String(length=20), server_default=sa.text("'COMPLETED'"), nullable=False, index=True),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'payment_reference', name='uq_payments_org_payment_ref'),
    )

    # 4. Subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('subscription_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('quotation_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotation_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_variants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('plan_name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), server_default='1.00', nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('billing_interval', sa.String(length=20), server_default=sa.text("'MONTHLY'"), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('next_billing_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default=sa.text("'ACTIVE'"), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'subscription_number', name='uq_subscriptions_org_sub_number'),
    )

    # 5. Billing Schedules
    op.create_table(
        'billing_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('billing_period_start', sa.Date(), nullable=False),
        sa.Column('billing_period_end', sa.Date(), nullable=False),
        sa.Column('billing_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(length=20), server_default=sa.text("'SCHEDULED'"), nullable=False, index=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'subscription_id', 'billing_period_start', 'billing_period_end', name='uq_billing_schedules_period'),
    )

    # 6. Subscription Prorations
    op.create_table(
        'subscription_prorations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('old_quantity', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('new_quantity', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('old_unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('new_unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('billing_period_start', sa.Date(), nullable=False),
        sa.Column('billing_period_end', sa.Date(), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('total_period_days', sa.Integer(), nullable=False),
        sa.Column('remaining_days', sa.Integer(), nullable=False),
        sa.Column('prorated_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor_name', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 7. Subscription Cancellations
    op.create_table(
        'subscription_cancellations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('cancellation_type', sa.String(length=20), server_default=sa.text("'END_OF_PERIOD'"), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('requested_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 8. Credit Notes
    op.create_table(
        'credit_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('credit_note_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('tax_total', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('total', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('status', sa.String(length=20), server_default=sa.text("'DRAFT'"), nullable=False, index=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'credit_note_number', name='uq_credit_notes_org_cn_number'),
    )

    # 9. Credit Note Items
    op.create_table(
        'credit_note_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('credit_note_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('credit_notes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), server_default='1.00', nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 10. Payment Refunds
    op.create_table(
        'payment_refunds',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('refund_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payments.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('credit_note_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('credit_notes.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('refund_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default=sa.text("'COMPLETED'"), nullable=False, index=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'refund_number', name='uq_payment_refunds_org_refund_num'),
    )


def downgrade() -> None:
    op.drop_table('payment_refunds')
    op.drop_table('credit_note_items')
    op.drop_table('credit_notes')
    op.drop_table('subscription_cancellations')
    op.drop_table('subscription_prorations')
    op.drop_table('billing_schedules')
    op.drop_table('subscriptions')
    op.drop_table('payments')
    op.drop_table('invoice_items')
    op.drop_table('invoices')

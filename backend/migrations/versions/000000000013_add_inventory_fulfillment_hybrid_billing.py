"""add inventory fulfillment and hybrid billing tables

Revision ID: 000000000013
Revises: 000000000012
Create Date: 2026-09-05 21:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000000000013'
down_revision: Union[str, None] = '000000000012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Warehouses
    op.create_table(
        'warehouses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'code', name='uq_warehouses_organization_code'),
    )
    op.create_index('ix_warehouses_org_code', 'warehouses', ['organization_id', 'code'])

    # 2. Product Variants
    op.create_table(
        'product_variants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('unit_price_override', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'sku', name='uq_product_variants_org_sku'),
    )
    op.create_index('ix_product_variants_org_sku', 'product_variants', ['organization_id', 'sku'])

    # 3. Inventory Stocks
    op.create_table(
        'inventory_stocks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_variants.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('location_code', sa.String(length=100), nullable=True, server_default='MAIN'),
        sa.Column('on_hand_quantity', sa.Integer(), server_default='0', nullable=False),
        sa.Column('reserved_quantity', sa.Integer(), server_default='0', nullable=False),
        sa.Column('available_quantity', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'warehouse_id', 'product_id', 'variant_id', 'location_code', name='uq_inventory_stocks_org_wh_prod_var_loc'),
    )
    op.create_index('ix_inventory_stocks_org_wh_prod', 'inventory_stocks', ['organization_id', 'warehouse_id', 'product_id'])

    # 4. Inventory Movements
    op.create_table(
        'inventory_movements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_variants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('movement_type', sa.String(length=50), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_name', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_inventory_movements_org_wh_prod', 'inventory_movements', ['organization_id', 'warehouse_id', 'product_id'])

    # 5. Inventory Reservations
    op.create_table(
        'inventory_reservations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quotation_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotation_items.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_variants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_inventory_reservations_org_quotation', 'inventory_reservations', ['organization_id', 'quotation_id'])

    # 6. Warehouse Allocations
    op.create_table(
        'warehouse_allocations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quotation_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotation_items.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('allocated_quantity', sa.Integer(), nullable=False),
        sa.Column('allocation_strategy', sa.String(length=50), server_default='SINGLE_WAREHOUSE', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='ALLOCATED', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_warehouse_allocations_org_quotation', 'warehouse_allocations', ['organization_id', 'quotation_id'])

    # 7. Fulfillment Overrides
    op.create_table(
        'fulfillment_overrides',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quotation_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotation_items.id', ondelete='CASCADE'), nullable=True),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_name', sa.String(length=255), nullable=False),
        sa.Column('original_allocation', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('new_allocation', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_fulfillment_overrides_org_quotation', 'fulfillment_overrides', ['organization_id', 'quotation_id'])

    # 8. Shipments
    op.create_table(
        'shipments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('shipment_number', sa.String(length=100), nullable=False),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('status', sa.String(length=50), server_default='DRAFT', nullable=False),
        sa.Column('carrier', sa.String(length=100), nullable=True),
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
        sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expected_delivery_date', sa.Date(), nullable=True),
        sa.Column('actual_delivery_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_shipments_org_number', 'shipments', ['organization_id', 'shipment_number'])
    op.create_index('ix_shipments_org_quotation', 'shipments', ['organization_id', 'quotation_id'])

    # 9. Shipment Lines
    op.create_table(
        'shipment_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('shipment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quotation_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotation_items.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_variants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 10. Backorders
    op.create_table(
        'backorders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('backorder_number', sa.String(length=100), nullable=False),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('quotation_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotation_items.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_variants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('requested_quantity', sa.Integer(), nullable=False),
        sa.Column('fulfilled_quantity', sa.Integer(), server_default='0', nullable=False),
        sa.Column('remaining_quantity', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='OPEN', nullable=False),
        sa.Column('promised_delivery_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_backorders_org_customer', 'backorders', ['organization_id', 'customer_id'])
    op.create_index('ix_backorders_org_quotation', 'backorders', ['organization_id', 'quotation_id'])

    # 11. Delivery Promises
    op.create_table(
        'delivery_promises',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('shipment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shipments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('backorder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('backorders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('promised_date', sa.Date(), nullable=False),
        sa.Column('expected_date', sa.Date(), nullable=False),
        sa.Column('actual_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='ON_TRACK', nullable=False),
        sa.Column('slippage_days', sa.Integer(), server_default='0', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_delivery_promises_org_quotation', 'delivery_promises', ['organization_id', 'quotation_id'])

    # 12. Billing Classifications
    op.create_table(
        'billing_classifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('quotation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('commercial_model', sa.String(length=50), nullable=False),
        sa.Column('one_time_total', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('recurring_monthly_total', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('billing_frequency', sa.String(length=50), server_default='MONTHLY', nullable=False),
        sa.Column('line_classifications', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_billing_classifications_org_quotation', 'billing_classifications', ['organization_id', 'quotation_id'])


def downgrade() -> None:
    op.drop_table('billing_classifications')
    op.drop_table('delivery_promises')
    op.drop_table('backorders')
    op.drop_table('shipment_lines')
    op.drop_table('shipments')
    op.drop_table('fulfillment_overrides')
    op.drop_table('warehouse_allocations')
    op.drop_table('inventory_reservations')
    op.drop_table('inventory_movements')
    op.drop_table('inventory_stocks')
    op.drop_table('product_variants')
    op.drop_table('warehouses')

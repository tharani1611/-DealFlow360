# DealFlow360 — Original Phases 36–45: Inventory, Fulfillment & Hybrid Billing Architectural Standard

## Executive Summary
This document provides the authoritative technical design and operational specifications for **Original Phases 36–45: Inventory Model, Stock Availability, Inventory Reservation, Smart Warehouse Allocation, Manual Fulfillment Override, Shipment Creation, Backorder Engine, Backorder Consolidation, Delivery Promise Tracking, and Hybrid Billing** within the DealFlow360 platform.

---

# 1. Scope & Functional Architecture

### Phase 36 — Inventory Model & Stock Balances
- **Warehouses**: Multi-warehouse registry with location tracking and allocation priority order.
- **Product Variants**: SKU variant support for physical items.
- **Stock Ledger**: Immutable `inventory_movements` log recording receipts, reservations, releases, shipments, and adjustments.
- **Stock Balance**: `inventory_stocks` maintaining real-time `on_hand_quantity`, `reserved_quantity`, and `available_quantity`.

### Phase 37 — Stock Availability Telemetry
- Quotation availability engine calculating line-level available stock, on-hand stock, reserved stock, and shortfall.
- Real-time stock status badge (`AVAILABLE`, `PARTIALLY_AVAILABLE`, `OUT_OF_STOCK`).

### Phase 38 — Inventory Reservation Engine
- Row-level lock (`with_for_update()`) stock reservation for quotation items.
- Automatically reserves stock when transitioning proposals to accepted/sent or upon explicit sales user reservation.
- Automatic release of reservations upon quotation expiry, cancellation, or rejection.

### Phase 39 — Smart Warehouse Allocation Engine
- **Strategy 1 (Single Warehouse)**: Fulfills 100% of a quotation item from a single high-priority warehouse if available stock suffices.
- **Strategy 2 (Minimal Split)**: Multi-warehouse allocation split across priority warehouses when no single warehouse holds sufficient inventory.

### Phase 40 — Manual Fulfillment Override
- Allows authorized fulfillment managers (`is_admin=True` or `fulfillment.override` permission) to override automatic warehouse allocations.
- Full audit logging in `fulfillment_override_audits` capturing actor, original allocation, new allocation, timestamp, and mandatory reason.

### Phase 41 — Shipment Creation
- Generation of unique shipment numbers (`SHP-XXXXXX`) referencing warehouse allocations.
- Atomic stock reservation consumption and deduction of `on_hand_quantity`.
- Shipment lifecycle management (`DRAFT`, `PACKED`, `SHIPPED`, `DELIVERED`, `CANCELLED`).

### Phase 42 — Backorder Engine
- Automatic generation of `backorders` for inventory shortfalls (`shortfall_quantity > 0`).
- Open backorder tracking per quotation and customer line item.

### Phase 43 — Customer Backorder Consolidation
- Aggregated customer-level backorder view consolidating open shortfall quantities and delivery promises across all active quotations.

### Phase 44 — Delivery Promise Tracking
- Dynamic delivery promise calculations comparing `promised_date` vs `expected_date` vs `actual_date`.
- Calculates slippage days and status (`ON_TIME`, `AT_RISK`, `DELAYED`, `MET`, `MISSED`).

### Phase 45 — Hybrid Billing Engine
- Classifies line items into `ONE_TIME` (physical goods) vs `RECURRING` (subscription services/plans).
- Computes aggregated document-level commercial model (`ONE_TIME`, `RECURRING`, `HYBRID`).
- Real-time reporting of total one-time revenue alongside recurring monthly revenue (MRR).

---

# 2. Database Schema (Alembic Migration 000000000013)

- `warehouses`: `(id, organization_id, code, name, address, priority, is_active, created_at, updated_at)`
- `product_variants`: `(id, organization_id, product_id, sku, name, unit_price_override, is_active, created_at, updated_at)`
- `inventory_stocks`: `(id, organization_id, warehouse_id, product_id, variant_id, location_code, on_hand_quantity, reserved_quantity, available_quantity, created_at, updated_at)`
- `inventory_movements`: `(id, organization_id, warehouse_id, product_id, variant_id, quantity, movement_type, reference_type, reference_id, actor_id, actor_name, notes, created_at)`
- `inventory_reservations`: `(id, organization_id, quotation_id, quotation_item_id, product_id, variant_id, warehouse_id, quantity, status, expires_at, created_at, updated_at)`
- `warehouse_allocations`: `(id, organization_id, quotation_id, quotation_item_id, warehouse_id, allocated_quantity, allocation_strategy, status, created_at, updated_at)`
- `fulfillment_override_audits`: `(id, organization_id, quotation_id, quotation_item_id, actor_id, actor_name, original_allocation, new_allocation, reason, created_at)`
- `shipments`: `(id, organization_id, shipment_number, quotation_id, warehouse_id, status, carrier, tracking_number, shipped_at, expected_delivery_date, actual_delivery_date, created_at, updated_at)`
- `shipment_lines`: `(id, organization_id, shipment_id, quotation_item_id, product_id, variant_id, quantity, created_at)`
- `backorders`: `(id, organization_id, backorder_number, quotation_id, quotation_item_id, customer_id, product_id, variant_id, requested_quantity, fulfilled_quantity, remaining_quantity, warehouse_id, status, promised_delivery_date, created_at, updated_at)`
- `delivery_promises`: `(id, organization_id, quotation_id, shipment_id, backorder_id, promised_date, expected_date, actual_date, status, slippage_days, notes, created_at, updated_at)`
- `billing_classifications`: `(id, organization_id, quotation_id, commercial_model, one_time_total, recurring_monthly_total, billing_frequency, line_classifications, created_at, updated_at)`

---

# 3. Verification & Compliance
- **Backend Tests**: 100% pass rate across 184 test cases in pytest (`184 passed in 84.99s`).
- **Frontend Build**: Zero TypeScript errors in `npm run build` (`dist/assets/index-C7zkP-P5.js 476.17 kB`).
- **Commercial Invariants**: Commercial pricing, margin, risk, and approval engines remain fully authoritative; inventory shortages do NOT alter quotation price or calculated margin.
- **Tenant Isolation**: Multi-tenant isolation enforced on every query and service function.

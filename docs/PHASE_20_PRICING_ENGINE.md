# Phase 20: Quotation Pricing Engine Architecture & Specification

## Executive Summary
Phase 20 introduces the **Quotation Pricing Engine** for DealFlow360. The engine resolves standard base product prices, volume quantity threshold tiers, customer/contract agreements, and promotional discounts through a deterministic, explainable, and tenant-isolated pricing pipeline. All monetary calculations enforce strict `Decimal` precision, preventing floating-point inaccuracies while preserving historical quotation price snapshots.

---

## 1. Architecture Overview & Principles
1. **Deterministic Rule Resolution**: Pricing rules are evaluated strictly by priority, date windows, quantity thresholds, and customer/tenant scope.
2. **2-Tier Pipeline**:
   - **Tier 1 (Price Replacement)**: Contract Price (Priority 1) > Customer Price (Priority 10) > Volume Tier (Priority 20) > Base Product Price.
   - **Tier 2 (Price Adjustment)**: Promotional or additional discounts (`percentage_discount` / `fixed_discount`) applied to the selected replacement unit price.
3. **Manual Override Support**: Explicit client unit price overrides (`manual_unit_price`) bypass automated rule evaluation and are flagged as `MANUAL_OVERRIDE`.
4. **Historical Price Snapshotting**: Created quotations snapshot final calculated unit prices onto `QuotationItem` records, guaranteeing immutability if base prices or rules change later.

---

## 2. Database Data Model (`pricing_rules`)

```sql
CREATE TABLE pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN ('contract', 'customer', 'volume', 'promotion')),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    customer_id UUID NULL REFERENCES customers(id) ON DELETE SET NULL,
    min_quantity NUMERIC(10, 2) NOT NULL DEFAULT 1.00 CHECK (min_quantity > 0),
    max_quantity NUMERIC(10, 2) NULL,
    price_type VARCHAR(50) NOT NULL DEFAULT 'override_price' CHECK (price_type IN ('override_price', 'percentage_discount', 'fixed_discount')),
    value NUMERIC(12, 2) NOT NULL CHECK (value >= 0),
    priority INT NOT NULL DEFAULT 100 CHECK (priority > 0),
    valid_from TIMESTAMP WITH TIME ZONE NULL,
    valid_until TIMESTAMP WITH TIME ZONE NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    description TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
```

### Alembic Migration
- **Revision ID**: `000000000007`
- **Revises**: `000000000006`
- **File**: `migrations/versions/2026_09_05_0700-000000000007_add_pricing_rules_table.py`

---

## 3. Pricing Calculation Pipeline Algorithm

```text
                     Quotation Line Input (product_id, quantity, customer_id, quotation_date)
                                                       │
                                       Manual unit_price provided?
                                            ├── YES ──► Final Unit Price = manual_unit_price (MANUAL_OVERRIDE)
                                            └── NO
                                               │
                                               ▼
                              Fetch Active Tenant Rules for Product & Qty
                                               │
                                               ▼
                                   Tier 1: Price Replacement
                     Order: Contract (p=1) > Customer (p=10) > Volume (p=20) > Base Price
                                               │
                                               ▼
                                    Selected Replacement Price
                                               │
                                               ▼
                                   Tier 2: Promotional Adjustment
                          Apply Percentage or Fixed Promotional Discount
                                               │
                                               ▼
                                  Final Unit Price & Explanation
```

---

## 4. API Endpoints

### 1. Calculate Pricing Preview
`POST /api/v1/pricing/calculate`

#### Request Payload
```json
{
  "product_id": "8a7b6c5d-5717-4562-b3fc-2c963f66afa6",
  "quantity": "50.00",
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "quotation_date": "2026-09-05T12:00:00Z",
  "currency": "USD"
}
```

#### Response Payload
```json
{
  "base_price": "1000.00",
  "selected_unit_price": "900.00",
  "final_unit_price": "900.00",
  "quantity": "50.00",
  "currency": "USD",
  "pricing_source": "VOLUME",
  "applied_rule_id": "c1a2b3c4-5717-4562-b3fc-2c963f66afa6",
  "applied_rule_name": "Volume 50+ Tier",
  "discount_amount": "100.00",
  "discount_percent": "10.00",
  "explanation": "Volume tier price applied (Volume 50+ Tier, 50.00+ units): 900.00 USD (Base price: 1000.00)"
}
```

### 2. Pricing Rule Management Endpoints
- `POST /api/v1/pricing/rules`: Create pricing rule (201 Created).
- `GET /api/v1/pricing/rules`: List tenant pricing rules with filters.
- `GET /api/v1/pricing/rules/{id}`: Get specific rule details.
- `PUT /api/v1/pricing/rules/{id}`: Update pricing rule.
- `DELETE /api/v1/pricing/rules/{id}`: Delete pricing rule (Admin role required).

---

## 5. Security & Multi-Tenant Isolation
- All database queries enforce `organization_id == current_user.organization_id`.
- Cross-tenant product, customer, or rule references return `404 Not Found`.
- Administrative deletion requires `require_admin` dependency.

---

## 6. Verification Summary
- **Pytest Test Suite**: 148 / 148 passed (`tests/test_pricing_engine.py` + regression suite).
- **Frontend Build**: `npm run build` passed with 0 TypeScript errors.
- **Alembic Migration**: `000000000007 (head)` verified active in PostgreSQL.

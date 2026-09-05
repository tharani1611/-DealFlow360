# Phase 21: Real-time Margin Engine Architecture & Specification

## Executive Summary
Phase 21 introduces the **Real-time Margin Engine** for DealFlow360. The engine calculates line-level and quotation-level profitability (revenue, cost basis, gross margin, weighted margin percentage, and margin health classification) in real-time. It seamlessly consumes final selling prices produced by the Phase 20 Pricing Engine and snapshots unit costs onto quotation items for historical reproducibility.

---

## 1. Core Formulas & Financial Precision
1. **Line Revenue**: `quantity * unit_selling_price` (rounded to 2 decimals)
2. **Line Cost**: `quantity * unit_cost` (rounded to 2 decimals)
3. **Gross Margin**: `line_revenue - line_cost` (rounded to 2 decimals)
4. **Line Margin %**:
   - `(gross_margin / line_revenue) * 100` if `line_revenue > 0`
   - `-100.00%` if `line_revenue == 0` and `gross_margin < 0`
   - `0.00%` if `line_revenue == 0` and `gross_margin == 0`
5. **Weighted Quotation Margin %**:
   - `(total_gross_margin / total_revenue) * 100` if `total_revenue > 0`
   - `-100.00%` if `total_revenue == 0` and `total_gross_margin < 0`

---

## 2. Margin Health Classification Thresholds

| Health Status | Margin Percentage Range | Badge Color (Neo Glass) |
| :--- | :--- | :--- |
| **`HEALTHY`** | `>= 30.00%` | Emerald / Green |
| **`CAUTION`** | `15.00% - 29.99%` | Amber / Yellow |
| **`AT_RISK`** | `0.00% - 14.99%` | Orange |
| **`NEGATIVE`** | `< 0.00%` | Rose / Red |

---

## 3. Database Schema Changes & Cost Snapshotting
- **Product Model (`products`)**: Added `unit_cost NUMERIC(12,2) DEFAULT 0.00 NOT NULL` with check constraint `unit_cost >= 0`.
- **QuotationItem Model (`quotation_items`)**: Added `unit_cost NUMERIC(12,2) DEFAULT 0.00 NOT NULL` with check constraint `unit_cost >= 0`.
- **Historical Snapshotting**: Quotation item creation automatically snapshots `product.unit_cost` onto `QuotationItem.unit_cost`. Future changes to product base costs do not mutate historical quotation margins.
- **Alembic Migration**: `migrations/versions/2026_09_05_0800-000000000008_add_margin_cost_fields.py` (`000000000008 (head)`).

---

## 4. API Endpoints (`/api/v1/margins`)

### 1. Calculate Real-time Margin Preview
`POST /api/v1/margins/calculate`

#### Request Payload
```json
{
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "currency": "USD",
  "items": [
    {
      "product_id": "8a7b6c5d-5717-4562-b3fc-2c963f66afa6",
      "quantity": "50.00"
    }
  ]
}
```

#### Response Payload
```json
{
  "quotation_id": null,
  "quotation_number": null,
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "currency": "USD",
  "total_revenue": "40000.00",
  "total_cost": "25000.00",
  "gross_margin": "15000.00",
  "margin_percent": "37.50",
  "health_status": "HEALTHY",
  "items": [
    {
      "product_id": "8a7b6c5d-5717-4562-b3fc-2c963f66afa6",
      "product_name": "Enterprise Suite",
      "quantity": "50.00",
      "unit_selling_price": "800.00",
      "unit_cost": "500.00",
      "line_revenue": "40000.00",
      "line_cost": "25000.00",
      "gross_margin": "15000.00",
      "margin_percent": "37.50",
      "health_status": "HEALTHY",
      "pricing_source": "VOLUME",
      "explanation": "Enterprise Suite: Revenue 40000.00 USD (800.00/unit), Cost 25000.00 USD (500.00/unit), Gross Margin 15000.00 USD (37.50%, HEALTHY)"
    }
  ],
  "explanation": "Quotation Preview: Total Revenue 40000.00 USD, Total Cost 25000.00 USD, Gross Margin 15000.00 USD (37.50%, Health: HEALTHY)"
}
```

### 2. Quotation & Deal Margin Endpoints
- `GET /api/v1/margins/quotations/{quotation_id}`: Retrieves stored quotation margin breakdown using snapshotted unit costs and unit prices.
- `GET /api/v1/margins/deals/{deal_id}`: Retrieves margin breakdown for a deal's associated quotation.

---

## 5. Security & Tenant Isolation
- Tenant isolation enforced strictly via `organization_id == current_user.organization_id`.
- Cross-tenant product, customer, quotation, or deal requests return `404 Not Found`.

---

## 6. Verification Summary
- **Pytest Suite**: `155 / 155 PASSED` (`tests/test_margin_engine.py` + regression suite).
- **Frontend Build**: `npm run build` passed with 0 TypeScript errors.
- **Alembic Revision**: `000000000008 (head)` verified active in PostgreSQL.

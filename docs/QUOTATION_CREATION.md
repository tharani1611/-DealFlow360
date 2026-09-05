# Phase 19: Quotation Creation Architecture & Workflow

## Executive Summary
Phase 19 implements transactional **Quotation Creation** for DealFlow360. Building on top of the Phase 18 Quotation Data Model (`Quotation`, `QuotationItem`), Phase 19 adds transactional creation workflows, server-side validation (active customers/products, contact & deal ownership, valid date ranges), sequential quotation number generation (`QT-000001`), line price and SKU snapshotting, custom unit price overrides, live subtotal/tax/discount calculations, and multi-item UI creation with Neo Glass aesthetics.

---

## 1. Request / Response Schema

### Endpoint
`POST /api/v1/quotations`

### Request Payload (`QuotationCreate`)
```json
{
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "contact_id": "1a2b3c4d-5717-4562-b3fc-2c963f66afa6",
  "deal_id": "9f8e7d6c-5717-4562-b3fc-2c963f66afa6",
  "title": "Q3 Enterprise License Proposal",
  "currency": "USD",
  "terms": "Payment due within 30 days of invoice date.",
  "notes": "Includes 24/7 dedicated support SLA.",
  "quotation_date": "2026-09-05T12:00:00Z",
  "valid_until": "2026-10-05T12:00:00Z",
  "items": [
    {
      "product_id": "8a7b6c5d-5717-4562-b3fc-2c963f66afa6",
      "quantity": "2.00",
      "unit_price": "4500.00",
      "discount_percent": "10.00",
      "discount_amount": "500.00",
      "tax_rate": "5.00",
      "tax_amount": "200.00",
      "description": "Discounted enterprise licenses",
      "sequence": 1
    }
  ]
}
```

### Response Payload (`QuotationResponse`)
```json
{
  "id": "c1a2b3c4-5717-4562-b3fc-2c963f66afa6",
  "organization_id": "7c444e94-55ef-4a31-a09f-eb471f3f9133",
  "quotation_number": "QT-000001",
  "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "contact_id": "1a2b3c4d-5717-4562-b3fc-2c963f66afa6",
  "deal_id": "9f8e7d6c-5717-4562-b3fc-2c963f66afa6",
  "created_by_user_id": "9078d3cc-d8ab-450d-92ab-8eec885fda3e",
  "status": "draft",
  "title": "Q3 Enterprise License Proposal",
  "currency": "USD",
  "subtotal": "9000.00",
  "discount_amount": "500.00",
  "tax_amount": "200.00",
  "total_amount": "8700.00",
  "quotation_date": "2026-09-05T12:00:00Z",
  "valid_until": "2026-10-05T12:00:00Z",
  "items": [
    {
      "id": "e5f6a7b8-5717-4562-b3fc-2c963f66afa6",
      "quotation_id": "c1a2b3c4-5717-4562-b3fc-2c963f66afa6",
      "product_id": "8a7b6c5d-5717-4562-b3fc-2c963f66afa6",
      "sku": "ENT-SOFT-01",
      "description": "Discounted enterprise licenses",
      "quantity": "2.00",
      "unit_price": "4500.00",
      "discount_percent": "10.00",
      "discount_amount": "500.00",
      "tax_rate": "5.00",
      "tax_amount": "200.00",
      "line_total": "8700.00",
      "sequence": 1
    }
  ]
}
```

---

## 2. Server-Side Validation Rules

| Rule | HTTP Status | Exception / Logic |
| :--- | :--- | :--- |
| **Authentication** | `401 Unauthorized` | Missing or invalid JWT Bearer token |
| **Tenant Isolation** | `404 Not Found` | Customer, Contact, Deal, or Product does not belong to user's `organization_id` |
| **Customer-Contact Match** | `404 Not Found` | Specified `contact_id` exists in tenant but belongs to a different customer |
| **Customer-Deal Match** | `404 Not Found` | Specified `deal_id` exists in tenant but belongs to a different customer |
| **Active Customer Check** | `422 BusinessRuleViolation` | `customer.is_active is False` |
| **Active Product Check** | `422 BusinessRuleViolation` | `product.is_active is False` |
| **Date Range Sanity** | `422 BusinessRuleViolation` | `valid_until < quotation_date` |
| **Non-negative Quantities/Prices** | `422 BusinessRuleViolation` | `quantity <= 0`, `unit_price < 0`, `discount_amount < 0`, `tax_amount < 0` |
| **Subtotal Discount Check** | `422 BusinessRuleViolation` | Header level `discount_amount > subtotal` |

---

## 3. Price & SKU Snapshotting & Auto-Sequencing
1. **Price Snapshotting**: If the request payload omits `unit_price` on an item, the service copies `product.unit_price` into `QuotationItem.unit_price`. If provided, custom price override is respected.
2. **SKU Snapshotting**: If the request payload omits `sku` on an item, the service copies `product.sku` into `QuotationItem.sku`.
3. **Auto-Sequencing**: If `sequence` is omitted or set to `0`, the service automatically sets `sequence = index + 1` (1-indexed).

---

## 4. Transactional Atomicity & Rollback
- The entire creation operation is executed within a single database transaction (`AsyncSession`).
- If any line item calculation, entity verification, or database constraint fails, `session.rollback()` is executed automatically, ensuring no orphaned quotation headers or line items are left in the database.

---

## 5. UI Integration (Neo Glass Identity)
- `frontend/src/pages/QuotationsPage.tsx` features a multi-item creation modal (`GlassModal`).
- Select Customer dynamically populates Contact and Deal drop-down lists scoped exclusively to that customer.
- Interactive multi-item row builder supports adding and removing items on-the-fly with live subtotal calculation.
- Primary commercial actions adhere to Neo-Brutalism styling (`BrutalButton`).

---

## 6. Deferred Functionality (Phase 20+)
- **Phase 20**: Pricing Engine (automated multi-tier volume discounts, contract pricing).
- **Phase 21**: Real-time Margin Engine (COGS line margin calculations).
- **Phase 22**: Quotation State Machine (sent/accepted/rejected transitions & locks).
- **Phase 23-25**: Discount governance, risk scoring, & multi-level approval workflows.

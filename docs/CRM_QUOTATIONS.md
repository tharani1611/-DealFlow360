# DealFlow360 — Quotation Management API Specification

## 1. Overview & Architecture

The Quotation Management module enables sales teams to generate, manage, negotiate, and track formal customer quotations. Quotations include line items capturing product pricing, quantity, line totals, subtotal, discount, tax, and grand total.

Each quotation belongs exclusively to a single organization (`organization_id`) and customer (`customer_id`).

```text
Authenticated Request
         │
         ▼
get_current_user() ──► Extract current_user.organization_id
         │
         ▼
Verify Customer & Products belong to `organization_id`
         │
         ▼
Historical Price Snapshot: Copy Product.name and Product.unit_price into QuotationItem
         │
         ▼
Calculate Line Totals, Subtotal, Discount & Tax Validation, Grand Total
         │
         ▼
Generate Sequential Tenant Quotation Number (QT-000001)
         │
         ▼
PostgreSQL DB (Persisted with CASCADE line items)
```

---

## 2. API Endpoints Reference Table

| METHOD | PATH | AUTH REQUIRED | AUTHORIZATION POLICY | EXPECTED STATUS |
| :--- | :--- | :---: | :---: | :---: |
| `POST` | `/api/v1/quotations` | Yes | Authenticated User | `201 Created` |
| `GET` | `/api/v1/quotations` | Yes | Authenticated User | `200 OK` |
| `GET` | `/api/v1/quotations/{quotation_id}` | Yes | Authenticated User | `200 OK` |
| `PUT` | `/api/v1/quotations/{quotation_id}` | Yes | Authenticated User | `200 OK` |
| `DELETE` | `/api/v1/quotations/{quotation_id}` | Yes | Admin Only (`require_admin`) | `204 No Content` |

---

## 3. Business & Financial Rules

1. **Price Snapshot Rule**: `QuotationItem.unit_price` and `product_name` snapshot current `Product` price and name at quotation creation time. Updating `Product.unit_price` later will NEVER alter existing quotation item prices or totals.
2. **Decimal Financial Arithmetic**: All prices, subtotals, discounts, taxes, and totals use exact `Decimal` precision rounded to 2 decimal places (`ROUND_HALF_UP`).
3. **Discount & Tax Constraints**:
   - `discount_amount` must be non-negative (`>= 0.00`) and cannot exceed `subtotal`.
   - `tax_amount` must be non-negative (`>= 0.00`).
   - `total_amount` is calculated as `subtotal - discount_amount + tax_amount` and cannot be negative.
4. **State Machine & Immutability**:
   - Statuses: `draft` -> `sent` -> `accepted` | `rejected` | `expired`.
   - Once a quotation enters a finalized status (`accepted`, `rejected`, `expired`), its items, customer, dates, and pricing cannot be edited.
5. **Tenant Quotation Numbering**:
   - Formatted as `QT-000001`, `QT-000002`... sequential per organization.

---

## 4. API Specification & Sample Payloads

### `POST /api/v1/quotations`
- **Status Code**: `201 Created`
- **Request Payload**:
```json
{
  "customer_id": "4aca2353-b379-47dd-88a8-b70cf36bce39",
  "items": [
    {
      "product_id": "23933ffc-2d45-4682-88a2-b35020749719",
      "quantity": "2.00"
    }
  ],
  "discount_amount": "50.00",
  "tax_amount": "30.00",
  "notes": "Valid for 30 days"
}
```

- **Response Payload (`201 Created`)**:
```json
{
  "id": "61c98dd9-9e24-419e-8481-50d39afe88d0",
  "organization_id": "293de004-57a8-447c-a01b-1ed31a7b740d",
  "customer_id": "4aca2353-b379-47dd-88a8-b70cf36bce39",
  "quotation_number": "QT-000001",
  "status": "draft",
  "quotation_date": "2026-09-05T09:33:46.011370Z",
  "valid_until": null,
  "notes": "Valid for 30 days",
  "subtotal": "350.00",
  "discount_amount": "50.00",
  "tax_amount": "30.00",
  "total_amount": "330.00",
  "items": [
    {
      "id": "fd3d5527-d69e-4e93-b4a0-d8354731c234",
      "quotation_id": "61c98dd9-9e24-419e-8481-50d39afe88d0",
      "product_id": "23933ffc-2d45-4682-88a2-b35020749719",
      "product_name": "Enterprise Server",
      "quantity": "2.00",
      "unit_price": "175.00",
      "line_total": "350.00",
      "created_at": "2026-09-05T09:33:46.014865Z",
      "updated_at": "2026-09-05T09:33:46.014868Z"
    }
  ],
  "created_at": "2026-09-05T09:33:46.012264Z",
  "updated_at": "2026-09-05T09:33:46.012268Z"
}
```

---

## 5. Security & Error Semantics

| Error Code | Trigger Condition |
| :--- | :--- |
| **`401 Unauthorized`** | Missing or invalid Bearer JWT token. |
| **`403 Forbidden`** | Regular non-admin user attempting `DELETE /api/v1/quotations/{id}`. |
| **`404 Not Found`** | Quotation, Customer, or Product ID does not exist OR belongs to another tenant organization. |
| **`422 Unprocessable Entity`** | Validation failure (discount > subtotal, invalid status transition, modifying finalized quotation). |

# DealFlow360 — Product Management API Specification

## 1. Overview & Architecture

The Product Management module enables sales operations teams to maintain a tenant-isolated catalog of products and services available for quotation and pricing. Each product belongs exclusively to a single organization through `organization_id`.

```text
Authenticated Request
         │
         ▼
get_current_user() ──► Extract current_user.organization_id (PostgreSQL Source of Truth)
         │
         ▼
Product Service    ──► Scope query to `organization_id == current_user.organization_id`
         │
         ▼
PostgreSQL DB (Filtered Result / 409 Conflict on SKU clash / 404 Not Found on cross-tenant access)
```

---

## 2. API Endpoints Reference Table

| METHOD | PATH | AUTH REQUIRED | AUTHORIZATION POLICY | EXPECTED STATUS |
| :--- | :--- | :---: | :---: | :---: |
| `POST` | `/api/v1/products` | Yes | Authenticated User | `201 Created` |
| `GET` | `/api/v1/products` | Yes | Authenticated User | `200 OK` |
| `GET` | `/api/v1/products/{product_id}` | Yes | Authenticated User | `200 OK` |
| `PUT` | `/api/v1/products/{product_id}` | Yes | Authenticated User | `200 OK` |
| `DELETE` | `/api/v1/products/{product_id}` | Yes | Admin Only (`require_admin`) | `204 No Content` |

---

## 3. Product Validation Rules

1. **Name**: Required string (`min_length=1`, max 255 chars). Cannot be empty or whitespace only.
2. **SKU**: Required string (`min_length=1`, max 100 chars). Automatically normalized to uppercase (e.g. `SERVER-X1`). Must be unique within the tenant organization.
3. **Unit Price**: Required Decimal value. Must be non-negative (`unit_price >= 0.00`). Preserves 2-decimal precision.
4. **Currency**: Required 3-letter ISO currency code (default `"USD"`), normalized to uppercase.
5. **Client Overrides Blocked**: `id`, `organization_id`, `created_at`, `updated_at` cannot be supplied or modified by the client.

---

## 4. SKU Uniqueness Strategy

- SKU uniqueness is scoped per organization via database constraint `uq_products_organization_id_sku`.
- **Cross-Tenant SKU Coexistence**: Organization A and Organization B may both register product SKU `SERVER-X1`.
- **Intra-Tenant SKU Uniqueness**: Registering or updating a product to an existing SKU within the same organization raises `409 Conflict`.

---

## 5. API Specification & Payloads

### `POST /api/v1/products`
- **Status Code**: `201 Created`
- **Request Payload**:
```json
{
  "name": "Enterprise Cloud Server X1",
  "sku": "SERVER-X1",
  "description": "High performance 64-core dedicated cloud instance",
  "unit_price": 4999.99,
  "currency": "USD",
  "is_active": true
}
```
- **Response Payload (`201 Created`)**:
```json
{
  "id": "c71e21e0-63bf-47bd-b203-d64e9a3b1189",
  "organization_id": "8c0a4b64-8971-4475-b778-9e574c88e9a1",
  "name": "Enterprise Cloud Server X1",
  "sku": "SERVER-X1",
  "description": "High performance 64-core dedicated cloud instance",
  "unit_price": "4999.99",
  "currency": "USD",
  "is_active": true,
  "created_at": "2026-09-05T14:59:00Z",
  "updated_at": "2026-09-05T14:59:00Z"
}
```

---

### `GET /api/v1/products`
- **Status Code**: `200 OK`
- **Query Parameters**:
  - `skip`: (integer, default `0`) Offset
  - `limit`: (integer, default `100`, max `500`) Page limit
  - `search`: (string, optional) Case-insensitive search in product name or SKU
  - `is_active`: (boolean, optional) Active status filter
  - `sku`: (string, optional) Exact SKU filter
  - `currency`: (string, optional) 3-letter currency filter

---

## 6. Multi-Tenant Security & Error Semantics

| Error Code | Trigger Condition |
| :--- | :--- |
| **`401 Unauthorized`** | Missing or invalid Bearer JWT token, or deactivated user/organization. |
| **`403 Forbidden`** | Regular non-admin user attempting `DELETE /api/v1/products/{id}`. |
| **`404 Not Found`** | Product ID does not exist OR belongs to another tenant organization. |
| **`409 Conflict`** | Product SKU already exists within the same organization. |
| **`422 Unprocessable Entity`** | Validation failure (negative price, blank name/SKU, invalid currency code). |

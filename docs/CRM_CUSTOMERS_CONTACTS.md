# DealFlow360 — Customer & Contact Management API Specification

## 1. Overview & Architecture

The Customer & Contact Management module forms the primary CRM directory layer for DealFlow360. All customer and contact records strictly belong to a single organization (tenant) via `organization_id`.

```text
Authenticated Request
         │
         ▼
get_current_user() ──► Extract current_user.organization_id (PostgreSQL Source of Truth)
         │
         ▼
Customer / Contact Service ──► Enforce `organization_id == current_user.organization_id`
         │
         ▼
PostgreSQL DB (Filtered Result / 404 Not Found on cross-tenant access)
```

---

## 2. API Endpoints Reference Table

| METHOD | PATH | AUTH REQUIRED | AUTHORIZATION POLICY | DESCRIPTION |
| :--- | :--- | :---: | :---: | :--- |
| `POST` | `/api/v1/customers` | Yes | Authenticated | Create a new customer in the user's organization |
| `GET` | `/api/v1/customers` | Yes | Authenticated | List/search customers in the user's organization |
| `GET` | `/api/v1/customers/{id}` | Yes | Authenticated | Get customer details by ID (tenant-scoped) |
| `PUT` | `/api/v1/customers/{id}` | Yes | Authenticated | Update customer details (tenant-scoped) |
| `DELETE` | `/api/v1/customers/{id}` | Yes | Admin Only | Delete a customer (tenant-scoped) |
| `POST` | `/api/v1/contacts` | Yes | Authenticated | Create contact person linked to tenant customer |
| `GET` | `/api/v1/contacts` | Yes | Authenticated | List/filter contacts in the user's organization |
| `GET` | `/api/v1/contacts/{id}` | Yes | Authenticated | Get contact details by ID (tenant-scoped) |
| `PUT` | `/api/v1/contacts/{id}` | Yes | Authenticated | Update contact details (tenant-scoped) |
| `DELETE` | `/api/v1/contacts/{id}` | Yes | Admin Only | Delete a contact (tenant-scoped) |

---

## 3. Customer Management API Specification

### `POST /api/v1/customers`
- **Status Code**: `201 Created`
- **Request Payload**:
```json
{
  "name": "Global Logistics Inc",
  "email": "info@globallogistics.com",
  "phone": "+1-555-0199",
  "address": "100 Fleet Street",
  "city": "Metropolis",
  "state": "NY",
  "country": "USA",
  "postal_code": "10001",
  "is_active": true
}
```
- **Response Payload (`201 Created`)**:
```json
{
  "id": "8a31e84a-9b1b-4d4b-97e3-0d3a7719602a",
  "organization_id": "8c0a4b64-8971-4475-b778-9e574c88e9a1",
  "name": "Global Logistics Inc",
  "email": "info@globallogistics.com",
  "phone": "+1-555-0199",
  "address": "100 Fleet Street",
  "city": "Metropolis",
  "state": "NY",
  "country": "USA",
  "postal_code": "10001",
  "is_active": true,
  "created_at": "2026-09-05T14:56:00Z",
  "updated_at": "2026-09-05T14:56:00Z"
}
```

### `GET /api/v1/customers`
- **Status Code**: `200 OK`
- **Query Parameters**:
  - `skip`: (integer, default `0`) Offset
  - `limit`: (integer, default `100`, max `500`) Page size limit
  - `search`: (string, optional) Case-insensitive customer name search filter
  - `is_active`: (boolean, optional) Active status filter

---

## 4. Contact Management API Specification

### `POST /api/v1/contacts`
- **Status Code**: `201 Created`
- **Request Payload**:
```json
{
  "customer_id": "8a31e84a-9b1b-4d4b-97e3-0d3a7719602a",
  "first_name": "Alice",
  "last_name": "Smith",
  "email": "alice.smith@globallogistics.com",
  "phone": "+1-555-0188",
  "job_title": "VP Procurement",
  "is_primary": true
}
```
- **Tenant Validation Rule**: `customer_id` MUST belong to `current_user.organization_id`. If `customer_id` belongs to another tenant or does not exist, the API returns `404 Not Found`.

- **Response Payload (`201 Created`)**:
```json
{
  "id": "e6a7114b-25b4-4e2b-b6d3-2f22b7a95610",
  "organization_id": "8c0a4b64-8971-4475-b778-9e574c88e9a1",
  "customer_id": "8a31e84a-9b1b-4d4b-97e3-0d3a7719602a",
  "first_name": "Alice",
  "last_name": "Smith",
  "email": "alice.smith@globallogistics.com",
  "phone": "+1-555-0188",
  "job_title": "VP Procurement",
  "is_primary": true,
  "created_at": "2026-09-05T14:56:00Z",
  "updated_at": "2026-09-05T14:56:00Z"
}
```

---

## 5. Multi-Tenant Security & Isolation Rules

1. **Client Control Prohibition**: Clients CANNOT provide `organization_id` in request payloads, headers, query params, or JWT claims.
2. **Database Tenant Filter**: Every query incorporates `Customer.organization_id == current_user.organization_id` or `Contact.organization_id == current_user.organization_id`.
3. **Cross-Tenant Masking**: Requests attempting to access or modify records belonging to another tenant receive `404 Not Found` (never `403`), preventing resource enumeration attacks across tenants.
4. **Relational Verification**: Creating or updating a contact's `customer_id` verifies that the referenced customer belongs to the user's organization before committing.

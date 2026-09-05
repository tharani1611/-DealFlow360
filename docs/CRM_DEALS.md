# DealFlow360 — Deals / Sales Pipeline API Specification

## 1. Overview & Architecture

The Deals / Sales Pipeline module enables sales representatives and account managers to track deals/opportunities through a multi-stage sales pipeline. Each deal is associated with a customer company, and can optionally link to a contact person and formal quotation.

Each deal belongs exclusively to a single organization (`organization_id`).

```text
Authenticated Request
         │
         ▼
get_current_user() ──► Extract current_user.organization_id
         │
         ▼
Verify Customer, Contact, and Quotation belong to `organization_id` & `customer_id`
         │
         ▼
Enforce Controlled Stage Transitions & Automatic Probabilities
         │
         ▼
Generate Sequential Tenant Deal Number (DEAL-000001)
         │
         ▼
PostgreSQL DB (Persisted with RESTRICT/SET NULL foreign keys)
```

---

## 2. API Endpoints Reference Table

| METHOD | PATH | AUTH REQUIRED | AUTHORIZATION POLICY | EXPECTED STATUS |
| :--- | :--- | :---: | :---: | :---: |
| `POST` | `/api/v1/deals` | Yes | Authenticated User | `201 Created` |
| `GET` | `/api/v1/deals/pipeline` | Yes | Authenticated User | `200 OK` |
| `GET` | `/api/v1/deals` | Yes | Authenticated User | `200 OK` |
| `GET` | `/api/v1/deals/{deal_id}` | Yes | Authenticated User | `200 OK` |
| `PUT` | `/api/v1/deals/{deal_id}` | Yes | Authenticated User | `200 OK` |
| `DELETE` | `/api/v1/deals/{deal_id}` | Yes | Admin Only (`require_admin`) | `204 No Content` |

---

## 3. Pipeline Stages & State Machine Rules

### Stages & Status Mapping

| STAGE | DEFAULT PROBABILITY | STATUS | DESCRIPTION |
| :--- | :---: | :---: | :--- |
| `new` | 10% | `open` | Initial opportunity lead created |
| `qualified` | 25% | `open` | Customer budget, authority, and need confirmed |
| `proposal` | 50% | `open` | Proposal / formal quote delivered |
| `negotiation` | 75% | `open` | Terms and pricing under active discussion |
| `won` | 100% | `won` | Deal successfully closed / contract signed |
| `lost` | 0% | `lost` | Opportunity lost (requires `lost_reason`) |

### Transition Rules & Finalization Immutability
1. **Forward Movement**: Allowed from open stages (`new` -> `qualified` -> `proposal` -> `negotiation` -> `won`/`lost`).
2. **Stage to 'lost' Requirement**: Moving a deal to `lost` stage **requires** a non-empty `lost_reason` (e.g. `"Price was higher than competitor"`).
3. **Closed Deal Immutability**: Deals in finalized stages (`won` or `lost`) are closed and cannot be moved backward to open stages or edited.

---

## 4. API Specification & Sample Payloads

### `POST /api/v1/deals`
- **Status Code**: `201 Created`
- **Request Payload**:
```json
{
  "customer_id": "4aca2353-b379-47dd-88a8-b70cf36bce39",
  "contact_id": "fd3d5527-d69e-4e93-b4a0-d8354731c234",
  "quotation_id": "61c98dd9-9e24-419e-8481-50d39afe88d0",
  "title": "Enterprise Cloud Expansion",
  "description": "Multi-year cloud server infrastructure deal",
  "value": "25000.00",
  "expected_close_date": "2026-12-31",
  "notes": "Target Q4 close"
}
```

- **Response Payload (`201 Created`)**:
```json
{
  "id": "7b8a12c4-3b2a-46de-9856-112233445566",
  "organization_id": "293de004-57a8-447c-a01b-1ed31a7b740d",
  "customer_id": "4aca2353-b379-47dd-88a8-b70cf36bce39",
  "contact_id": "fd3d5527-d69e-4e93-b4a0-d8354731c234",
  "quotation_id": "61c98dd9-9e24-419e-8481-50d39afe88d0",
  "title": "Enterprise Cloud Expansion",
  "description": "Multi-year cloud server infrastructure deal",
  "deal_number": "DEAL-000001",
  "stage": "new",
  "status": "open",
  "value": "25000.00",
  "probability": 10,
  "expected_close_date": "2026-12-31",
  "lost_reason": null,
  "notes": "Target Q4 close",
  "created_at": "2026-09-05T15:10:00Z",
  "updated_at": "2026-09-05T15:10:00Z"
}
```

---

### `GET /api/v1/deals/pipeline` (Kanban View)
- **Status Code**: `200 OK`
- **Response Payload**:
```json
{
  "stages": {
    "new": [
      {
        "id": "7b8a12c4-3b2a-46de-9856-112233445566",
        "deal_number": "DEAL-000001",
        "title": "Enterprise Cloud Expansion",
        "value": "25000.00",
        "stage": "new",
        "probability": 10
      }
    ],
    "qualified": [],
    "proposal": [],
    "negotiation": [],
    "won": [],
    "lost": []
  }
}
```

---

## 5. Security & Error Semantics

| Error Code | Trigger Condition |
| :--- | :--- |
| **`401 Unauthorized`** | Missing or invalid Bearer JWT token. |
| **`403 Forbidden`** | Regular non-admin user attempting `DELETE /api/v1/deals/{id}`. |
| **`404 Not Found`** | Deal, Customer, Contact, or Quotation ID does not exist OR belongs to another tenant organization/customer. |
| **`409 Conflict`** | Deal number collision (internal retry required). |
| **`422 Unprocessable Entity`** | Validation failure (negative value, probability outside 0-100, invalid stage transition, missing lost_reason on lost deal). |

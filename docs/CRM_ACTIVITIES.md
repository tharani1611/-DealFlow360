# DealFlow360 — Activities & Workflow API Specification

## 1. Overview & Architecture

The Activities & Workflow module enables sales representatives and account teams to record, schedule, assign, and track CRM activities. Activities can be linked to Customers, Contacts, Deals, and Quotations, forming a chronological activity timeline for CRM records.

Each activity belongs exclusively to a single organization (`organization_id`).

```text
Authenticated Request
         │
         ▼
get_current_user() ──► Extract current_user.organization_id & user.id (created_by_user_id)
         │
         ▼
Verify Customer, Contact, Deal, Quotation & Assigned User belong to `organization_id` & `customer_id`
         │
         ▼
Enforce State Machine & Server-Controlled Timestamps (completed_at)
         │
         ▼
PostgreSQL DB (Persisted with SET NULL foreign keys for domain entities)
```

---

## 2. API Endpoints Reference Table

| METHOD | PATH | AUTH REQUIRED | AUTHORIZATION POLICY | EXPECTED STATUS |
| :--- | :--- | :---: | :---: | :---: |
| `POST` | `/api/v1/activities` | Yes | Authenticated User | `201 Created` |
| `GET` | `/api/v1/activities` | Yes | Authenticated User | `200 OK` |
| `GET` | `/api/v1/activities/{activity_id}` | Yes | Authenticated User | `200 OK` |
| `PUT` | `/api/v1/activities/{activity_id}` | Yes | Authenticated User | `200 OK` |
| `POST` | `/api/v1/activities/{activity_id}/complete` | Yes | Authenticated User | `200 OK` |
| `POST` | `/api/v1/activities/{activity_id}/cancel` | Yes | Authenticated User | `200 OK` |
| `DELETE` | `/api/v1/activities/{activity_id}` | Yes | Admin Only (`require_admin`) | `204 No Content` |
| `GET` | `/api/v1/customers/{customer_id}/activities` | Yes | Authenticated User | `200 OK` |
| `GET` | `/api/v1/deals/{deal_id}/activities` | Yes | Authenticated User | `200 OK` |

---

## 3. Activity Rules & State Machine

### Supported Activity Types
- `task`: General action item (e.g. `"Prepare proposal presentation"`).
- `call`: Phone call with customer/contact (e.g. `"Call customer regarding pricing"`).
- `meeting`: In-person or virtual demonstration/meeting (e.g. `"Product demo meeting"`).
- `note`: Internal reference note (e.g. `"Customer prefers annual billing cycle"`).
- `follow_up`: Scheduled follow-up task (e.g. `"Follow up on quotation delivery"`).

### Priority Levels
- `low`: Informational or non-urgent task.
- `medium`: Standard priority (default).
- `high`: High-priority follow-up or task.
- `urgent`: Critical escalation or deal blocker.

### Activity Status & State Machine
- `pending`: Active activity awaiting completion.
- `completed`: Completed activity (`completed_at` timestamp set server-side to current UTC time upon transition).
- `cancelled`: Cancelled activity.
- **Finalized Activity Immutability**: Completed or cancelled activities are closed and cannot be modified or returned to `pending`.

---

## 4. API Specification & Sample Payloads

### `POST /api/v1/activities`
- **Status Code**: `201 Created`
- **Request Payload**:
```json
{
  "activity_type": "call",
  "title": "Call John regarding pricing approval",
  "description": "Discuss enterprise discount tier for cloud servers",
  "priority": "high",
  "customer_id": "4aca2353-b379-47dd-88a8-b70cf36bce39",
  "contact_id": "fd3d5527-d69e-4e93-b4a0-d8354731c234",
  "deal_id": "7b8a12c4-3b2a-46de-9856-112233445566",
  "assigned_to_user_id": "ff5b3758-68a1-4ce6-a6c1-38f66a7f642b",
  "due_at": "2026-09-10T14:00:00Z"
}
```

- **Response Payload (`201 Created`)**:
```json
{
  "id": "e4d3c2b1-a099-4876-b543-210987654321",
  "organization_id": "293de004-57a8-447c-a01b-1ed31a7b740d",
  "activity_type": "call",
  "title": "Call John regarding pricing approval",
  "description": "Discuss enterprise discount tier for cloud servers",
  "status": "pending",
  "priority": "high",
  "customer_id": "4aca2353-b379-47dd-88a8-b70cf36bce39",
  "contact_id": "fd3d5527-d69e-4e93-b4a0-d8354731c234",
  "deal_id": "7b8a12c4-3b2a-46de-9856-112233445566",
  "quotation_id": null,
  "assigned_to_user_id": "ff5b3758-68a1-4ce6-a6c1-38f66a7f642b",
  "created_by_user_id": "ff5b3758-68a1-4ce6-a6c1-38f66a7f642b",
  "due_at": "2026-09-10T14:00:00Z",
  "completed_at": null,
  "created_at": "2026-09-05T15:17:00Z",
  "updated_at": "2026-09-05T15:17:00Z"
}
```

---

## 5. Timeline & Derived Filters

- `GET /api/v1/customers/{customer_id}/activities` — Customer chronological activity timeline (newest first).
- `GET /api/v1/deals/{deal_id}/activities` — Deal chronological activity timeline (newest first).
- `GET /api/v1/activities?overdue=true` — Filters `pending` activities where `due_at < current_utc_time`.
- `GET /api/v1/activities?upcoming=true` — Filters `pending` activities where `due_at >= current_utc_time`.

---

## 6. Security & Error Semantics

| Error Code | Trigger Condition |
| :--- | :--- |
| **`401 Unauthorized`** | Missing or invalid Bearer JWT token. |
| **`403 Forbidden`** | Regular non-admin user attempting `DELETE /api/v1/activities/{id}`. |
| **`404 Not Found`** | Activity, Customer, Contact, Deal, Quotation, or User ID does not exist OR belongs to another tenant organization/customer. |
| **`422 Unprocessable Entity`** | Validation failure (invalid activity_type, invalid priority, modifying finalized completed/cancelled activity). |

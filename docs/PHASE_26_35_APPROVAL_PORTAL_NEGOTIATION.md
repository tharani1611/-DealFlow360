# DealFlow360 — Original Phases 26–35 Master Documentation

## Approval Routing, Customer Portal Authentication, Quotation Portal & Negotiation Engine

### 1. Executive Overview
This document covers the implementation of **Original Phases 26–35** for the DealFlow360 commercial platform. The sub-system enhances commercial workflow governance by introducing append-only approval audit logging, segregation of duties enforcement, customer-facing portal authentication, line-level comment threads, formal change requests, counter-discount recalculation engines, version history snapshots, and automatic approval invalidation rules.

---

### 2. Architecture & Key Capabilities

#### Phase 26 & 27 & 28: Approval Audit & Segregation of Duties
- **Append-only Audit Logging**: `approval_audit_log` records all approval lifecycle transitions (`APPROVAL_SUBMITTED`, `APPROVAL_APPROVED`, `APPROVAL_REJECTED`, `APPROVAL_INVALIDATED`) with explicit actor context, timestamp, previous status, new status, trigger reasons, and approver notes.
- **Segregation of Duties**: Enforces business policy preventing non-admin submitters from approving their own quotations (`HTTP 422 BusinessRuleViolationException`).
- **Approval Invalidation**: Edits to commercial terms (discount adjustments, line items) automatically invalidate pre-existing approvals (`status = 'INVALIDATED'`) and record audit events.

#### Phase 29 & 30: Customer Portal Authentication & Quotation Portal
- **Customer Portal Authentication**: `PortalUser` model and `portal_auth` service issue JWT tokens containing distinct claims:
  ```json
  {
    "type": "portal",
    "customer_id": "...",
    "organization_id": "..."
  }
  ```
- **Security Boundary**: Dedicated API dependency `get_current_portal_user` enforces portal claims and blocks access to internal CRM routes. `get_current_user` strictly rejects `type: portal` tokens on internal routes.
- **Sanitized Quotations Data**: Portal endpoints sanitize commercial data—stripping `unit_cost`, `gross_margin`, internal approval notes, and internal line comments (`is_internal_only == True`) before sending to customer devices.
- **Customer Portal Actions**: Accept proposal and reject proposal workflows update quotation statuses (`accepted` or `rejected`) while emitting audit logs.

#### Phase 31 & 32 & 33: Line-level Comments & Change Requests
- **Line Comments**: `quotation_line_comment` model supports dual-mode threaded comments (`is_internal_only = True` for sales team, `is_internal_only = False` visible to customer portal).
- **Change Requests**: `quotation_change_request` model enables customers or reps to propose item quantity or target price modifications, tracked through a lifecycle status (`PENDING`, `ACCEPTED`, `REJECTED`).

#### Phase 34 & 35: Counter-discount Recalculation, Automatic Re-approval & Versioning
- **Counter-Discount Recalculation Engine**: Authoritative, high-precision Decimal pricing recalculation updates item unit discounts or quotation total discounts, invoking margin engines and governance evaluations deterministically.
- **Version History Snapshots**: `quotation_version` model snapshots full JSON representations of quotation state before commercial modifications, supporting point-in-time diffing and commercial auditing.

---

### 3. Database Schema Extensions (Migration `000000000012`)

- `approval_audit_logs`:
  - `id`, `organization_id`, `quotation_id`, `actor_id`, `actor_name`, `event_type`, `previous_status`, `new_status`, `reason`, `notes`, `created_at`
- `portal_users`:
  - `id`, `organization_id`, `customer_id`, `email`, `password_hash`, `full_name`, `is_active`, `last_login_at`, `created_at`, `updated_at`
- `quotation_line_comments`:
  - `id`, `organization_id`, `quotation_id`, `quotation_item_id`, `author_id`, `author_name`, `is_portal_user`, `is_internal_only`, `comment`, `created_at`
- `quotation_change_requests`:
  - `id`, `organization_id`, `quotation_id`, `quotation_item_id`, `requester_id`, `requester_name`, `is_portal_user`, `request_type`, `proposed_quantity`, `proposed_discount_percent`, `proposed_target_price`, `reason`, `status`, `reviewer_id`, `reviewed_at`, `created_at`
- `quotation_versions`:
  - `id`, `organization_id`, `quotation_id`, `version_number`, `snapshot_data` (JSONB), `change_reason`, `created_by_id`, `created_by_name`, `created_at`

---

### 4. Verification & Testing

- **Backend Pytest Suite**: 100% pass rate (`180 passed, 0 failed`) across all test modules including `test_approval_engine.py`, `test_commercial_governance_integration.py`, and `test_phases_26_35_approval_portal_negotiation.py`.
- **Frontend Production Build**: `npm run build` executed with 0 TypeScript compiler errors.

---

### 5. API Endpoint Reference

| Method | Endpoint | Description | Auth Claim Requirement |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/portal/auth/login` | Authenticates portal user and returns customer JWT token | None (Public) |
| `GET` | `/api/v1/portal/auth/me` | Fetches authenticated portal user profile | `type: portal` |
| `GET` | `/api/v1/portal/quotations` | Lists quotations for customer | `type: portal` |
| `GET` | `/api/v1/portal/quotations/{id}` | Fetches sanitized quotation detail | `type: portal` |
| `POST` | `/api/v1/portal/quotations/{id}/accept` | Accepts proposal | `type: portal` |
| `POST` | `/api/v1/portal/quotations/{id}/reject` | Rejects proposal | `type: portal` |
| `GET` | `/api/v1/negotiation/quotations/{id}/audit-logs` | Fetches approval audit trail | `type: internal` |
| `POST` | `/api/v1/negotiation/quotations/{id}/comments` | Creates line-level comment | `type: internal` or `type: portal` |
| `POST` | `/api/v1/negotiation/quotations/{id}/change-requests` | Proposes commercial change request | `type: internal` or `type: portal` |
| `POST` | `/api/v1/negotiation/quotations/{id}/counter-discount` | Recalculates quotation with counter-discount | `type: internal` or `type: portal` |
| `GET` | `/api/v1/negotiation/quotations/{id}/versions` | Fetches quotation version snapshots | `type: internal` |

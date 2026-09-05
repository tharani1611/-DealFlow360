# DealFlow360 — Authorization & Role-Based Access Control (RBAC) Architecture

## 1. Executive Summary

DealFlow360 implements a lightweight, organization-aware Authorization & Role-Based Access Control (RBAC) layer.

Authentication and Authorization are strictly decoupled:

```text
Authentication ("Who are you?")
      │  resolves & validates Bearer token
      ▼
current_user (User model loaded from PostgreSQL)
      │
      ▼
Authorization ("What are you allowed to do?")
      │  evaluates roles & permissions against PostgreSQL source of truth
      ▼
Allow (200 OK) / Deny (403 Forbidden)
```

---

## 2. Role Model Architecture

### Source of Truth
The user's role is anchored directly in the PostgreSQL database column:
```sql
users.is_admin  BOOLEAN NOT NULL DEFAULT false
```

- `is_admin = True` ──► **Admin** (`role = "admin"`)
- `is_admin = False` ──► **User** (`role = "user"`)

The Python `User` model computes `user.role` dynamically from `is_admin`, guaranteeing that API outputs (`UserResponse`) and internal logic can never drift out of sync.

### Database Authoritative Evaluation
JWT access tokens carry user identity (`sub` claim containing user UUID). Role evaluation is performed dynamically against the live PostgreSQL `User` record on every request:
- Revoking admin privileges (`is_admin = False`) in the database immediately denies access on the next request.
- Client-supplied claims, headers (`X-Organization-ID`), or body fields cannot override database role permissions or tenant identity.

---

## 3. Dependency Pipeline & HTTP Semantics

```text
Incoming HTTP Request
         │
         ▼
get_current_user()  ──►  Missing / Invalid / Expired / Inactive User ──► 401 Unauthorized
         │
         ▼
require_admin()     ──►  Authenticated User is_admin == False        ──► 403 Forbidden
         │
         ▼
Endpoint Handler
```

### Distinction Between 401 and 403

| HTTP Status | Condition | Example Scenario |
| :--- | :--- | :--- |
| **`401 Unauthorized`** | Authentication credentials missing, invalid, expired, or user/org deactivated. | Request without `Authorization: Bearer <token>` or with expired token. |
| **`403 Forbidden`** | Authenticated user credentials valid, but user lacks required role/privileges. | Regular user (`is_admin=False`) attempting to access `require_admin()` route. |

---

## 4. Initial Authorization Matrix

| Capability / Resource | Admin (`is_admin=True`) | User (`is_admin=False`) | Anonymous |
| :--- | :---: | :---: | :---: |
| Register Organization + Admin (`POST /auth/register`) | ✅ | ✅ | ✅ |
| Login (`POST /auth/login`) | ✅ | ✅ | ✅ |
| View Own Profile (`GET /auth/me`) | ✅ | ✅ | ❌ (401) |
| Admin Diagnostic Check (`GET /auth/admin-check`) | ✅ (200) | ❌ (403) | ❌ (401) |
| User Administration (`/users/*`) | Future Phase | Future Phase | ❌ (401) |
| CRM Quotation Governance | Future Phase | Future Phase | ❌ (401) |

---

## 5. Implementation Details

### Dependencies (`backend/app/api/deps.py`)

```python
def is_admin_user(user: User) -> bool:
    """Helper checking if user has administrator privileges."""
    return bool(user and user.is_admin)

async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """FastAPI authorization dependency requiring administrator privileges."""
    if not is_admin_user(current_user):
        raise ForbiddenException("Administrator privileges required")
    return current_user
```

### Diagnostic Endpoint (`GET /api/v1/auth/admin-check`)

```json
{
  "authorized": true,
  "role": "admin",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "organization_id": "8c0a4b64-8971-4475-b778-9e574c88e9a1"
}
```

---

## 6. Tenant Boundary & Isolation Strategy

1. **Database Relationship Primacy**: Authorization contexts strictly use `current_user.organization_id` from PostgreSQL.
2. **Header & Body Ignored**: Headers like `X-Organization-ID` or body parameters cannot switch tenant context or elevate privileges.
3. **Multi-Tenant Protection**: Users cannot access resources or authorization contexts outside their authenticated organization.

---

## 7. Future Extension Strategy

When complex domain requirements arrive (e.g. Discount Governance, Multi-level Approval Chains, Sales Manager vs Rep permissions):
- `roles`, `permissions`, and `user_roles` tables can be introduced via Alembic migrations without breaking `get_current_user()` or `require_admin()`.
- Granular permission dependencies (e.g. `require_permission("quotations:approve")`) can extend the existing `deps.py` pipeline cleanly.

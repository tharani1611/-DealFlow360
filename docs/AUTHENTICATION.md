# DealFlow360 — Authentication Architecture & API Specification

## 1. Executive Summary

DealFlow360 implements a multi-tenant, organization-aware authentication layer built with FastAPI, SQLAlchemy 2.x async, PostgreSQL, bcrypt, and `python-jose` (JWT).

In accordance with the multi-tenant database design:
```text
users.organization_id + users.email
```
is a composite unique constraint. The same email address can exist across different organizations without identity collision. Therefore, authentication strictly requires an **organization context** (`organization_slug`) during login.

---

## 2. Authentication Flow & Lifecycle

```text
Register (POST /api/v1/auth/register)
   │
   ├─► Validate Slug & Email
   ├─► Hash Password (bcrypt)
   ├─► Create Organization (is_active=true)
   ├─► Create Administrator User (is_active=true, is_admin=true)
   └─► Commit Transaction Atomically ──► Return User, Org & JWT

Login (POST /api/v1/auth/login)
   │
   ├─► Lookup Organization by Slug (check is_active)
   ├─► Lookup User by organization_id + Email (check is_active)
   ├─► Verify Password Hash (bcrypt.checkpw)
   └─► Generate JWT (sub=User UUID) ──► Return User, Org & JWT

Authenticated Request (GET /api/v1/auth/me)
   │
   ├─► Extract "Authorization: Bearer <token>"
   ├─► Decode & Validate JWT (Signature, Expiration, Subject)
   ├─► Fetch User from DB (selectinload Organization)
   ├─► Verify User.is_active AND Organization.is_active
   └─► Return Authenticated Profile
```

---

## 3. Security Architecture & Principles

### A. Password Security
- Passwords are hashed immediately upon receipt using bcrypt.
- Plaintext passwords are never persisted to disk, stored in memory beyond the request, or written to logs.
- Password hashes (`password_hash`) are explicitly omitted from all response schemas (`UserResponse`, `RegisterResponse`, `AuthResponse`).

### B. Tenant Isolation & Identity Derivation
- Authentication requires `organization_slug` to resolve tenant scope.
- Tenant identity is derived directly from `current_user.organization_id` in the database.
- Arbitrary tenant claims or headers supplied by clients are rejected.

### C. Stateless JWT with Database Verification
- JWT tokens contain standard claims: `sub` (User UUID), `iat` (Issued At), and `exp` (Expiration).
- Every authenticated request verifies that both the `User` and `Organization` records exist in the database and are `is_active = True`. Deactivated accounts or organizations lose API access immediately regardless of token expiration.

---

## 4. API Endpoint Specification

### A. `POST /api/v1/auth/register`

Atomically registers a new Organization and creates its initial primary administrator User.

- **Status Code**: `201 Created`
- **Request Body**:
```json
{
  "organization_name": "Acme Corporation",
  "organization_slug": "acme-corp",
  "email": "admin@acme.com",
  "full_name": "Acme Admin User",
  "password": "StrongPassword123!"
}
```

- **Validation Rules**:
  - `organization_slug`: lowercase letters, numbers, and hyphens (`^[a-z0-9]+(?:-[a-z0-9]+)*$`).
  - `email`: normalized lowercase, format validated.
  - `password`: min 8 chars, max 72 bytes.

- **Success Response (`201 Created`)**:
```json
{
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "organization_id": "8c0a4b64-8971-4475-b778-9e574c88e9a1",
    "email": "admin@acme.com",
    "full_name": "Acme Admin User",
    "is_active": true,
    "is_admin": true,
    "created_at": "2026-09-05T14:40:00Z",
    "updated_at": "2026-09-05T14:40:00Z",
    "organization": null
  },
  "organization": {
    "id": "8c0a4b64-8971-4475-b778-9e574c88e9a1",
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "is_active": true,
    "created_at": "2026-09-05T14:40:00Z",
    "updated_at": "2026-09-05T14:40:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

- **Error Responses**:
  - `409 Conflict`: Organization slug already taken or user already exists in organization.
  - `422 Unprocessable Entity`: Request body validation failed (invalid slug, short password, etc.).

---

### B. `POST /api/v1/auth/login`

Authenticates a user using organization slug, email, and password.

- **Status Code**: `200 OK`
- **Request Body**:
```json
{
  "organization_slug": "acme-corp",
  "email": "admin@acme.com",
  "password": "StrongPassword123!"
}
```

- **Success Response (`200 OK`)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "organization_id": "8c0a4b64-8971-4475-b778-9e574c88e9a1",
    "email": "admin@acme.com",
    "full_name": "Acme Admin User",
    "is_active": true,
    "is_admin": true,
    "created_at": "2026-09-05T14:40:00Z",
    "updated_at": "2026-09-05T14:40:00Z",
    "organization": null
  },
  "organization": {
    "id": "8c0a4b64-8971-4475-b778-9e574c88e9a1",
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "is_active": true,
    "created_at": "2026-09-05T14:40:00Z",
    "updated_at": "2026-09-05T14:40:00Z"
  }
}
```

- **Error Responses**:
  - `401 Unauthorized`: Returns generic message `"Invalid organization, email, or password"` to prevent account enumeration.

---

### C. `GET /api/v1/auth/me`

Retrieves current authenticated user profile and organization information derived from Bearer token.

- **Headers**: `Authorization: Bearer <access_token>`
- **Status Code**: `200 OK`
- **Success Response (`200 OK`)**:
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "organization_id": "8c0a4b64-8971-4475-b778-9e574c88e9a1",
  "email": "admin@acme.com",
  "full_name": "Acme Admin User",
  "is_active": true,
  "is_admin": true,
  "created_at": "2026-09-05T14:40:00Z",
  "updated_at": "2026-09-05T14:40:00Z",
  "organization": {
    "id": "8c0a4b64-8971-4475-b778-9e574c88e9a1",
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "is_active": true,
    "created_at": "2026-09-05T14:40:00Z",
    "updated_at": "2026-09-05T14:40:00Z"
  }
}
```

- **Error Responses**:
  - `401 Unauthorized`: Missing header, invalid token signature, expired token, non-existent user, or deactivated user/organization.

---

## 5. Development Configuration

Environment variables (`backend/.env`):

```ini
JWT_SECRET_KEY=CHANGE_THIS_IN_PRODUCTION_JWT_SECRET_KEY_MIN_32_BYTES
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
```

> [!WARNING]
> Never commit production JWT secrets to source control. In development environments without `JWT_SECRET_KEY`, a default development fallback secret is used with warning logs.

---

## 6. Verification & Test Execution

Run the complete test suite:

```bash
pytest backend/tests
```

Execution output:
```text
backend/tests/test_auth.py ....................                         [ 47%]
backend/tests/test_database.py .........                                [ 69%]
backend/tests/test_health.py ...                                        [ 76%]
backend/tests/test_main.py ..                                           [ 80%]
backend/tests/test_models.py .                                          [ 83%]
backend/tests/test_security.py .......                                  [100%]

============================== 42 passed in 4.70s ==============================
```

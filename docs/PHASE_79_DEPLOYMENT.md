# DealFlow360 — Phase 79: Production Deployment & Infrastructure Guide

## 1. Architecture Overview
DealFlow360 is engineered as a cloud-native, secure, multi-tenant B2B Sales Operations & CPQ platform.

```text
       [ HTTPS / Internet Traffic ]
                    │
                    ▼
   [ Reverse Proxy / Load Balancer / Nginx ]
        (SSL/TLS Termination, Gzip, WAF)
        ┌───────────┴───────────┐
        ▼                       ▼
[ Frontend SPA (Nginx) ]   [ ASGI Backend (FastAPI / Uvicorn) ]
  - Neo-Glass Design System   - Multi-Worker ASGI Processes
  - Static Asset Caching      - RBAC & Tenant Scoping
  - Direct SPA Route Fallback  - Authoritative Financial Engine
                               - Event Workflow Engine
                                └───▶ [ PostgreSQL 16+ ]
                                      - Async connection pool
                                      - Row-level tenant isolation
                                      - Transactional DDL (Alembic)
```

---

## 2. Prerequisites & Environment Setup

### System Requirements
- **Runtime**: Python 3.13+, Node.js 20+ LTS
- **Database**: PostgreSQL 16+ with `uuid-ossp` or native UUIDv4 support
- **Reverse Proxy**: Nginx 1.24+ or Cloudflare / AWS ALB

### Environment Configuration (.env)
Use `.env.example` as the authoritative template.

| Variable | Type | Required | Description |
|---|---|---|---|
| `APP_ENV` | String | Yes | Set to `production` |
| `DEBUG` | Boolean | Yes | Set to `false` in production |
| `SECRET_KEY` | String (Hex) | Yes | Core cryptographically secure secret (min 32 bytes) |
| `JWT_SECRET_KEY` | String (Hex) | Yes | Dedicated JWT signature key (min 32 bytes) |
| `DATABASE_URL` | String | Yes | `postgresql+asyncpg://<user>:<pwd>@<host>:5432/<dbname>` |
| `CORS_ORIGINS` | JSON Array | Yes | Explicit whitelist: `["https://app.dealflow360.com"]` |
| `ALLOWED_HOSTS` | List / String | Yes | Host validation: `["app.dealflow360.com", "backend"]` |
| `AI_PROVIDER` | String | No | Default `gemini` |
| `GEMINI_API_KEY` | String | Optional | Server-side Gemini API key (never exposed to client) |

---

## 3. Database Setup & Migration Procedure

### Step 1: Managed Database Creation
```bash
# Connect to PostgreSQL cluster as superuser
createdb dealflow360_prod -O dealflow_prod_user
```

### Step 2: Running Migrations
Always run database migrations prior to routing live traffic to new application instances:
```bash
cd backend
alembic upgrade head
```
Verify current head:
```bash
alembic current
# Expected: 000000000015 (head)
```

---

## 4. Production Process Management

### ASGI Backend Execution (Uvicorn / Systemd)
Run behind a process supervisor (e.g. systemd or Docker container restart policy):
```bash
cd backend
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --no-access-log \
  --proxy-headers
```
> [!IMPORTANT]
> Never deploy with `--reload` in production environments.

### Health & Readiness Endpoints
- **Liveness Check**: `GET /api/v1/health`
  - Returns `200 OK` with status `healthy`, app name, environment, and version. Zero database credentials or secrets leaked.
- **Readiness Check**: `GET /api/v1/readiness`
  - Returns `200 OK` with database ping status (`database_connected: true`).

---

## 5. Frontend Build & Static Serving

### Step 1: Production Build
```bash
cd frontend
npm ci
npm run build
```
Generates optimized static bundles in `dist/` with chunk splitting (`vendor-react`, `vendor-icons`).

### Step 2: Nginx SPA Configuration
Ensure Nginx routes all unmatched requests to `/index.html` to support client-side React Router:
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

---

## 6. Security & Hardening Checklist

- [x] **Secrets Management**: No hardcoded API keys, JWT tokens, or DB passwords in codebase or dockerfiles.
- [x] **Security Headers**: Enabled `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and `X-XSS-Protection`.
- [x] **Error Masking**: Unhandled server exceptions logged internally with clean `500 Internal Server Error` responses. Zero stack traces or file paths leaked.
- [x] **CORS Lockdown**: Explicit origin whitelisting required. Wildcard `*` disabled.
- [x] **Demo Isolation**: Demo seeders (`seed_demo_data.py`) never run automatically on production startup.

---

## 7. Backup, Disaster Recovery & Rollback

### Automated Daily PostgreSQL Backup
```bash
pg_dump -U dealflow_prod_user -h db.internal.dealflow360.com -d dealflow360_prod -F c -b -v -f /backups/dealflow360_$(date +%Y%m%d_%H%M%S).dump
```

### Restore Procedure
```bash
pg_restore -U dealflow_prod_user -h db.internal.dealflow360.com -d dealflow360_prod -v -c /backups/dealflow360_<timestamp>.dump
cd backend && alembic upgrade head
```

### Application Rollback
1. Stop the application process.
2. If database schema was migrated, rollback migration: `alembic downgrade <target_revision>`.
3. Checkout previous release artifact or Docker image tag.
4. Restart application and verify `/api/v1/health` and `/api/v1/readiness`.

# DealFlow360 — Database Foundation & Migration Specification

## Document Information
* **System Name**: DealFlow360 (An Intelligent, Self-Governing Sales Operations Platform)
* **Document Title**: PostgreSQL Database Foundation & Alembic Migration Architecture
* **Phases**: Phase 4 (Database Foundation) & Phase 5 (Core Data Models)
* **Authoritative References**: [`docs/PROJECT-CONSTITUTION.md`](file:///c:/Users/lenovo/Desktop/DealFlow360/docs/PROJECT-CONSTITUTION.md), [`docs/PHASE-2-FUNCTIONAL-ARCHITECTURE.md`](file:///c:/Users/lenovo/Desktop/DealFlow360/docs/PHASE-2-FUNCTIONAL-ARCHITECTURE.md)

---

# 1. DATABASE TECHNOLOGY & ASYNC ARCHITECTURE

DealFlow360 uses **PostgreSQL** as its primary transactional database engine. The persistence layer is built on SQLAlchemy 2.x with the `asyncpg` driver to provide high-concurrency non-blocking I/O operations.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Request Handler                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ async with get_db()
┌───────────────────────────────────▼────────────────────────────────────┐
│                    SQLAlchemy 2.x AsyncSession                         │
│           (Auto-commit on exit, explicit rollback on error)            │
├────────────────────────────────────────────────────────────────────────┤
│                 SQLAlchemy AsyncEngine + asyncpg Driver                │
│                 (Pool size: 10, Max overflow: 20, Pre-ping)             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ TCP / IP (Port 5432)
┌───────────────────────────────────▼────────────────────────────────────┐
│                      PostgreSQL Database Engine                        │
│           (ACID Transactions, Row Locks, Immutable Audit Logs)         │
└────────────────────────────────────────────────────────────────────────┘
```

---

# 2. NAMING CONVENTIONS & CONSTRAINT STRATEGY

To ensure deterministic, cross-environment database schemas, all database objects follow explicit naming conventions configured directly on SQLAlchemy's `MetaData`:

```python
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referenced_table_name)s",
    "pk": "pk_%(table_name)s"
}
```

### Table & Column Rules
* **Tables**: Plural `snake_case` (e.g., `organizations`, `customers`, `products`).
* **Columns**: Singular `snake_case` (e.g., `unit_price`, `organization_id`).
* **Foreign Keys**: `fk_<table_name>_<column_name>_<referenced_table_name>` (e.g., `fk_users_organization_id_organizations`).
* **Primary Keys**: `pk_<table_name>` (e.g., `pk_organizations`).
* **Unique Constraints**: `uq_<table_name>_<column_names>` (e.g., `uq_users_organization_id_email`).

---

# 3. PRIMARY IDENTIFIER STRATEGY (UUID v4)

DealFlow360 uses **UUID v4** primary keys across application entities:
* **Storage Type**: PostgreSQL native `UUID` (via `sqlalchemy.dialects.postgresql.UUID(as_uuid=True)`).
* **Generation**: Application-side generation using `uuid.uuid4()` default factories combined with PostgreSQL database-level `uuid-ossp` / `pgcrypto` defaults.
* **Benefits**: Prevents sequential ID enumeration attacks, guarantees global uniqueness across distributed environments, and supports client-side ID pre-generation when necessary.

---

# 4. TIMESTAMP STRATEGY (UTC TIMEZONE-AWARE)

All entities incorporate timezone-aware UTC timestamps:
* **`created_at`**: `DateTime(timezone=True)`, defaults to `datetime.now(timezone.utc)` and SQL `server_default=func.now()`.
* **`updated_at`**: `DateTime(timezone=True)`, automatically refreshed via `onupdate=lambda: datetime.now(timezone.utc)` and `server_default=func.now()`.

---

# 5. REUSABLE BASE MODEL INFRASTRUCTURE

Model entities inherit common architectural mixins from `app.core.database`:

```python
class Base(DeclarativeBase):
    metadata = metadata

class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now()
    )
```

---

# 6. ALEMBIC ASYNC MIGRATION ARCHITECTURE

Database migrations are managed via **Alembic** configured for asynchronous execution:
* **Configuration File**: `backend/alembic.ini`
* **Migration Environment**: `backend/migrations/env.py` (loads `settings.DATABASE_URL` dynamically and binds `target_metadata = Base.metadata`).
* **Baseline Revision**: `backend/migrations/versions/2026_09_05_0000-000000000000_baseline_infrastructure.py` (enables `uuid-ossp` and `pgcrypto` PostgreSQL extensions).
* **Phase 5 Migration Revision**: `backend/migrations/versions/2026_09_05_0100-000000000001_add_core_organization_user_customer_contact_product_models.py`

### Standard Migration Workflow Commands
```bash
# Generate a new migration after model edits
alembic revision --autogenerate -m "Add domain tables"

# Apply pending migrations to database
alembic upgrade head

# Roll back most recent migration
alembic downgrade -1
```

---

# 7. TRANSACTION MANAGEMENT & CONCURRENCY READINESS

### Transaction Boundaries
Requests interacting with the database use the `get_db()` dependency:
* Opens `AsyncSession`.
* Automatically issues `COMMIT` upon successful route completion.
* Automatically issues `ROLLBACK` and raises domain exceptions on failure.

---

# 8. CORE DATA MODELS (PHASE 5)

The initial core business models establish tenant isolation and customer/catalog foundations:

```
[Organization]
  ├── Users (1:N)
  ├── Customers (1:N)
  │     └── Contacts (1:N)
  └── Products (1:N)
```

### Model Specifications

1. **`Organization` (`organizations`)**
   - Tenant entity. Fields: `id`, `name`, `slug` (unique), `is_active`, `created_at`, `updated_at`.
   - Relationships: `users`, `customers`, `contacts`, `products`.

2. **`User` (`users`)**
   - Application user belonging to an Organization.
   - Fields: `id`, `organization_id` (FK -> `organizations.id`, RESTRICT), `email`, `full_name`, `password_hash`, `is_active`, `is_admin`, `created_at`, `updated_at`.
   - Constraint: `uq_users_organization_id_email` (email unique per organization).

3. **`Customer` (`customers`)**
   - Customer company entity scoped to an Organization.
   - Fields: `id`, `organization_id` (FK -> `organizations.id`, RESTRICT), `name`, `email`, `phone`, `address`, `city`, `state`, `country`, `postal_code`, `is_active`, `created_at`, `updated_at`.
   - Index: `ix_customers_organization_id_name`.

4. **`Contact` (`contacts`)**
   - Individual contact linked to a Customer and Organization.
   - Fields: `id`, `organization_id` (FK -> `organizations.id`, RESTRICT), `customer_id` (FK -> `customers.id`, RESTRICT), `first_name`, `last_name`, `email`, `phone`, `job_title`, `is_primary`, `created_at`, `updated_at`.
   - Index: `ix_contacts_organization_id_customer_id`.

5. **`Product` (`products`)**
   - Sellable product/service catalog item scoped to an Organization.
   - Fields: `id`, `organization_id` (FK -> `organizations.id`, RESTRICT), `name`, `sku`, `description`, `unit_price` (`Numeric(12,2)`), `currency` (`USD`), `is_active`, `created_at`, `updated_at`.
   - Constraints: `uq_products_organization_id_sku` (SKU unique per org), `ck_products_unit_price_non_negative` (`unit_price >= 0`).

---

# 9. ENVIRONMENT CONFIGURATION & LOCAL SETUP

### Environment Parameters (`.env`)
```ini
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=dealflow_user
POSTGRES_PASSWORD=dealflow_password
POSTGRES_DB=dealflow360_db
DATABASE_URL=postgresql+asyncpg://dealflow_user:dealflow_password@localhost:5432/dealflow360_db
```

---

# 10. DEFINITION OF DONE FOR PHASE 5

Phase 5 is complete when:
1. All 5 core models (`Organization`, `User`, `Customer`, `Contact`, `Product`) are implemented in `app/models/` using SQLAlchemy 2.x declarative types.
2. Tenant scoping (`organization_id`) and `ondelete="RESTRICT"` foreign keys are enforced.
3. Monetary fields (`unit_price`) use `Numeric(12, 2)` decimal representation.
4. Composite unique constraints (`uq_users_organization_id_email`, `uq_products_organization_id_sku`) and check constraints are configured.
5. Migration `000000000001_add_core_organization_user_customer_contact_product_models.py` is generated and verified with `alembic history` / `alembic current`.
6. Full backend test suite (`pytest`) passes (15/15 tests passing).
7. No AI packages, microservices, secrets, or later-phase domain features (quotations, deals, payments) were added.

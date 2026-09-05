# DealFlow360 — Phase 18: Quotation Data Model Specification

## 1. Overview & Conceptual Architecture
The `Quotation` and `QuotationItem` data models serve as the foundational persistence layer for commercial proposals within DealFlow360. Designed in accordance with **Phase 18 of the Master Roadmap**, the model supports historical price and SKU snapshotting, multi-tenant isolation, contact/deal optional associations, audit compatibility, and strict decimal financial precision to enable downstream pricing, discounting, margin, and state machine engines (Phases 19–25).

---

## 2. Entities & Schema Specification

### `Quotation` Entity (`quotations` table)
Represents a sales quotation issued to a Customer within an Organization.

| Column | Type | Constraints / Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default: `uuid4()` | Unique quotation identifier |
| `organization_id` | `UUID` | FK `organizations.id` (RESTRICT), NOT NULL, Index | Multi-tenant organization scoping |
| `customer_id` | `UUID` | FK `customers.id` (RESTRICT), NOT NULL, Index | Parent customer associated with quotation |
| `contact_id` | `UUID` | FK `contacts.id` (SET NULL), Nullable, Index | Optional target contact person at customer |
| `deal_id` | `UUID` | FK `deals.id` (SET NULL), Nullable, Index | Optional sales deal opportunity |
| `title` | `VARCHAR(255)` | Nullable | Commercial proposal title or subject line |
| `quotation_number` | `VARCHAR(50)` | NOT NULL, Index | Tenant-scoped unique quotation reference (e.g., `QT-000001`) |
| `status` | `VARCHAR(30)` | Default: `'draft'`, NOT NULL | Lifecycle status (`draft`, `sent`, `accepted`, `rejected`, `expired`) |
| `currency` | `VARCHAR(3)` | Default: `'USD'`, NOT NULL | ISO 4217 3-letter currency code |
| `quotation_date` | `TIMESTAMPTZ` | Default: `now()`, NOT NULL | Date quotation was issued |
| `valid_until` | `TIMESTAMPTZ` | Nullable | Expiration date of commercial offer |
| `notes` | `TEXT` | Nullable | Internal notes or customer-facing terms |
| `terms` | `TEXT` | Nullable | Formal commercial terms & conditions |
| `created_by_user_id`| `UUID` | FK `users.id` (SET NULL), Nullable, Index | Audit user who created the quotation |
| `updated_by_user_id`| `UUID` | FK `users.id` (SET NULL), Nullable, Index | Audit user who last updated the quotation |
| `subtotal` | `NUMERIC(12,2)`| Default: `0.00`, NOT NULL, Check `>= 0` | Sum of all line item totals |
| `discount_amount` | `NUMERIC(12,2)`| Default: `0.00`, NOT NULL, Check `>= 0` | Quotation-level discount amount |
| `tax_amount` | `NUMERIC(12,2)`| Default: `0.00`, NOT NULL, Check `>= 0` | Quotation-level tax amount |
| `total_amount` | `NUMERIC(12,2)`| Default: `0.00`, NOT NULL, Check `>= 0` | Final payable total (`subtotal - discount_amount + tax_amount`) |
| `created_at` | `TIMESTAMPTZ` | Default: `now()`, NOT NULL | Persistence creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | Default: `now()`, NOT NULL | Persistence update timestamp |

---

### `QuotationItem` Entity (`quotation_items` table)
Represents an individual line item in a Quotation with price and SKU snapshotting.

| Column | Type | Constraints / Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | Primary Key, Default: `uuid4()` | Unique quotation item identifier |
| `quotation_id` | `UUID` | FK `quotations.id` (CASCADE), NOT NULL, Index | Parent quotation |
| `product_id` | `UUID` | FK `products.id` (RESTRICT), NOT NULL, Index | Reference product in organization catalog |
| `product_variant_id`| `UUID` | Nullable, Index | Future compatibility slot for product variants (Phase 12 catalog) |
| `product_name` | `VARCHAR(255)`| NOT NULL | **Snapshot**: Name of product at time of quotation creation |
| `sku` | `VARCHAR(100)`| Nullable | **Snapshot**: SKU of product at time of quotation creation |
| `description` | `TEXT` | Nullable | Optional line item custom description |
| `sequence` | `INTEGER` | Default: `0`, NOT NULL | Line ordering / display sequence |
| `quantity` | `NUMERIC(10,2)`| NOT NULL, Check `> 0` | Quantity ordered |
| `unit_price` | `NUMERIC(12,2)`| NOT NULL, Check `>= 0` | **Snapshot**: Unit price applied to this line item |
| `discount_percent` | `NUMERIC(5,2)` | Default: `0.00`, NOT NULL, Check `0..100`| Reserved for line-level pricing engine (Phase 20) |
| `discount_amount` | `NUMERIC(12,2)`| Default: `0.00`, NOT NULL, Check `>= 0` | Line-level discount amount |
| `tax_rate` | `NUMERIC(5,2)` | Default: `0.00`, NOT NULL, Check `>= 0` | Reserved for tax pricing engine (Phase 20) |
| `tax_amount` | `NUMERIC(12,2)`| Default: `0.00`, NOT NULL, Check `>= 0` | Line-level tax amount |
| `line_total` | `NUMERIC(12,2)`| NOT NULL, Check `>= 0` | Line total (`(quantity * unit_price) - discount_amount + tax_amount`) |
| `created_at` | `TIMESTAMPTZ` | Default: `now()`, NOT NULL | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | Default: `now()`, NOT NULL | Update timestamp |

---

## 3. Key Architectural Principles

### Price & SKU Snapshot Strategy
* At line item creation, `product_name`, `sku`, and default `unit_price` are snapshotted from the `Product` catalog record into `QuotationItem`.
* Future changes to `Product.unit_price` or `Product.name` in the main catalog **do NOT retroactively alter** historical quotations.
* Enables immutable commercial records required for auditing, financial reporting, and legal compliance.

### Tenant Isolation & Relationship Validation
* Every query is filtered by `organization_id == current_user.organization_id`.
* Service layer validates that optional `contact_id` and `deal_id` belong to the same `organization_id` AND `customer_id`.
* Cross-tenant access or invalid cross-customer resource references return standard `404 Not Found`.

### Financial Data Types & Precision
* All monetary values utilize SQLAlchemy `Numeric(12, 2)` (PostgreSQL `NUMERIC(12,2)`).
* Python service calculations enforce `Decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)` to prevent binary floating-point inaccuracies.

### Unique Constraints & Indexing
* `UniqueConstraint("organization_id", "quotation_number")` ensures sequential numbers (e.g. `QT-000001`) are unique per organization.
* Indexes on `organization_id`, `customer_id`, `status`, `created_at`, `deal_id`, `contact_id`, and `product_id` optimize filtering and relational queries.

---

## 4. Migration & Status History
* Baseline Quotation schema created in migration `000000000002`.
* Phase 18 enhanced schema applied in migration `000000000006` (`2026_09_05_0600-000000000006_enhance_quotation_data_model.py`).
* Current Alembic revision: `000000000006 (head)`.

---

## 5. Explicitly Deferred Roadmap Phases
To maintain strict adherence to the Master Roadmap, the following downstream engines remain deferred:
* **Phase 19**: Quotation Creation Workflows
* **Phase 20**: Quotation Pricing Engine (Calculations, Tiers, Price Lists)
* **Phase 21**: Real-time Margin Engine
* **Phase 22**: Quotation State Machine (Full Transition Guard Enforcement)
* **Phase 23**: Discount Governance
* **Phase 24**: Blended Discount Risk Engine

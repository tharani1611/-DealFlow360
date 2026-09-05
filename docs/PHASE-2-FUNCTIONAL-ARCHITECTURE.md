# DealFlow360 — Phase 2: Functional Architecture & Data Design

## Document Metadata
* **System Name**: DealFlow360 (An Intelligent, Self-Governing Sales Operations Platform)
* **Document Title**: Modular Monolith Functional Architecture & Database Specification
* **Phase**: Phase 2 (Functional Architecture & Data Design)
* **Authoritative References**: [`docs/PROJECT-CONSTITUTION.md`](file:///c:/Users/lenovo/Desktop/DealFlow360/docs/PROJECT-CONSTITUTION.md), [`docs/PHASE-1-PRODUCT-DEFINITION.md`](file:///c:/Users/lenovo/Desktop/DealFlow360/docs/PHASE-1-PRODUCT-DEFINITION.md)

---

# 1. ARCHITECTURE OVERVIEW & TECH STACK

DealFlow360 is engineered as a **Clean Modular Monolith**. Microservices, distributed queues (Kafka/RabbitMQ), Redis caches, and container orchestrators (Kubernetes) are explicitly excluded to ensure transaction integrity, simplicity, and rapid development.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   React 18 + TypeScript + Vite UI                      │
│                (Neo Glass Component System & React Router)              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST APIs (JSON)
┌───────────────────────────────────▼────────────────────────────────────┐
│                    FastAPI Async REST API Layer                        │
│                 (Pydantic v2 Validation & RBAC Middleware)             │
├────────────────────────────────────────────────────────────────────────┤
│                 Application Service Layer & Domain Engines             │
│   (Pricing, Risk, Approval, Margin, Fulfillment, Billing, Subscriptions)│
├────────────────────────────────────────────────────────────────────────┤
│                SQLAlchemy 2.x Async Persistence Layer                  │
│                     (asyncpg + Transaction Manager)                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Async PostgreSQL Driver
┌───────────────────────────────────▼────────────────────────────────────┐
│                       PostgreSQL Database Engine                       │
│           (ACID Transactions, Row Locks, Immutable Audit Logs)         │
└────────────────────────────────────────────────────────────────────────┘
```

### Stack Components
* **Backend Runtime**: Python 3.11+ async execution environment.
* **API Framework**: FastAPI for high-performance async REST endpoints and automatic OpenAPI documentation.
* **Database Engine**: PostgreSQL for ACID transactional data integrity.
* **ORM & Database Driver**: SQLAlchemy 2.x AsyncEngine + `asyncpg`.
* **Data Validation & Schemas**: Pydantic v2 for input/output schema enforcement.
* **Database Migrations**: Alembic.
* **Frontend Framework**: React 18+ with TypeScript, built via Vite.
* **Frontend Navigation**: React Router v6+.
* **Frontend Styling**: Tailwind CSS + Custom CSS Neo Glass tokens.

---

# 2. CORE ARCHITECTURAL PRINCIPLES

1. **Backend Authoritative**: All financial calculations, tier pricing, discount governance, risk scoring, approval routing, inventory reservations, fulfillment allocations, billing schedules, proration, and permissions are computed exclusively by backend services. Client-submitted prices or totals are strictly rejected.
2. **Frontend Untrusted**: The frontend interface acts solely as a presentation engine and user input buffer. UI visibility settings do not constitute authorization.
3. **Deterministic Intelligence (NO AI)**: System self-governance, recommendations, anomalies, and health scores derive 100% from deterministic algorithms, decision matrices, and business rules.
4. **Security by Design**: Every endpoint enforces role-based authorization (RBAC), object-level access control (ABAC), input validation, and audit recording.
5. **Transactional Integrity**: Critical multi-step workflows (quote confirmation, inventory reservation, billing generation) execute within strict database transaction boundaries (`BEGIN ... COMMIT / ROLLBACK`).
6. **Decoupled Downstream Lifecycles**: While Quotation is the central commercial object, downstream sub-processes (Fulfillment, Billing, Subscriptions, Payments) maintain independent, decoupled state machines.

---

# 3. BACKEND MODULE BOUNDARIES

The backend source tree is partitioned into 31 logical domain modules:

| Module Package | Responsibility | Primary Entities | Key Services |
| :--- | :--- | :--- | :--- |
| `core` | Base configuration, DB session management, base models | System Config | `DatabaseManager`, `ConfigService` |
| `auth` | Authentication, password hashing, JWT session lifecycle | User credentials, Tokens | `AuthService`, `TokenManager` |
| `users` | Internal user accounts, user profiles | `User` | `UserService` |
| `roles` | RBAC roles and permission matrix enforcement | `Role`, `Permission` | `RBACService` |
| `audit` | Immutable audit logging for security and business events | `AuditEvent` | `AuditService` |
| `customers` | Master customer account data | `Customer`, `Contact` | `CustomerService` |
| `customer_tiers` | Tier classifications and discount ceiling mappings | `CustomerTier` | `TierService` |
| `products` | Master product catalog and unit definitions | `Product`, `Category` | `ProductService` |
| `product_variants`| SKU variant attributes and pricing overrides | `ProductVariant` | `VariantService` |
| `pricing` | Authoritative pricing resolution engine | `PriceList`, `PriceListItem` | `PricingEngine` |
| `discounts` | Discount governance policies and category ceilings | `DiscountPolicy` | `DiscountGovernanceEngine` |
| `margins` | Real-time line and order margin calculations | Margin metrics | `MarginEngine` |
| `quotations` | Core quote domain model and revision handling | `Quotation`, `QuotationLine` | `QuotationService` |
| `approvals` | Multi-stage approval routing and delegation rules | `ApprovalRule`, `ApprovalInstance` | `ApprovalEngine` |
| `negotiation` | Customer portal negotiation threads and counter-offers | `NegotiationSession`, `LineComment` | `NegotiationEngine` |
| `warehouses` | Warehouse locations and shipping cost weighting | `Warehouse` | `WarehouseService` |
| `inventory` | Stock levels, reservations, and stock movements | `InventoryItem`, `StockReservation` | `InventoryEngine` |
| `fulfillment` | Smart warehouse allocation and fulfillment plans | `FulfillmentPlan`, `Allocation` | `FulfillmentEngine` |
| `shipments` | Physical shipment dispatch and tracking | `Shipment`, `ShipmentLine` | `ShipmentService` |
| `backorders` | Backorder creation and stock arrival consolidation | `Backorder` | `BackorderEngine` |
| `delivery` | Delivery promise tracking and slippage telemetry | `DeliveryPromise` | `DeliveryService` |
| `billing` | One-time invoice generation and invoice status tracking | `Invoice`, `InvoiceLine` | `BillingEngine` |
| `subscriptions` | Subscription plans, billing schedules, proration | `Subscription`, `BillingSchedule` | `SubscriptionEngine` |
| `payments` | Payment ledger and invoice allocation | `Payment`, `PaymentAllocation` | `PaymentService` |
| `deal_health` | Rule-based deal health classification | `DealHealthRecord` | `DealHealthEngine` |
| `anomalies` | Deterministic discount anomaly detection | `AnomalyRecord` | `AnomalyEngine` |
| `notifications` | Operational nudges and manager escalations | `Notification` | `NotificationEngine` |
| `upsell` | Deterministic recommendation engine (No AI) | Co-purchase rules | `UpsellEngine` |
| `reporting` | Financial aggregation queries and export generators | Aggregation views | `ReportingService`, `PDF/XLSX Exporters` |
| `admin` | System parameters and catalog administration | System settings | `AdminService` |

---

# 4. DATABASE SCHEMAS & ENTITY RELATIONSHIPS

The PostgreSQL database is organized into normalized relational tables using integer/UUID primary keys, decimal monetary representations (`NUMERIC(12,2)`), and strict foreign key constraints.

```
┌──────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  customers   │1     *│   quotations    │1     *│ quotation_lines │
├──────────────┤───────├─────────────────┤───────├─────────────────┤
│ id (PK)      │       │ id (PK)         │       │ id (PK)         │
│ name         │       │ customer_id(FK) │       │ quotation_id(FK)│
│ tier_id (FK) │       │ status          │       │ product_id (FK) │
└──────────────┘       │ risk_score      │       │ quantity        │
                       │ total_margin    │       │ selling_price   │
                       └────────┬────────┘       └────────┬────────┘
                                │ 1                       │ 1
                                │                         │
                       ┌────────▼────────┐       ┌────────▼────────┐
                       │approval_instances│      │  allocations    │
                       ├─────────────────┤       ├─────────────────┤
                       │ id (PK)         │       │ id (PK)         │
                       │ quotation_id(FK)│       │ line_id (FK)    │
                       │ approver_role   │       │ warehouse_id(FK)│
                       │ status          │       │ allocated_qty   │
                       └─────────────────┘       └─────────────────┘
```

### Primary Entity Definitions

#### 1. Identity & RBAC
* `users` (`id`, `email`, `password_hash`, `full_name`, `role_id`, `is_active`, `created_at`)
* `roles` (`id`, `name`, `description`, `created_at`)
* `permissions` (`id`, `code`, `module`, `description`)
* `role_permissions` (`role_id`, `permission_id`)

#### 2. Customers & Tiers
* `customer_tiers` (`id`, `code`, `name`, `default_discount_ceiling_pct`)
* `customers` (`id`, `legal_name`, `trading_name`, `tax_id`, `tier_id`, `status`, `created_at`)
* `customer_contacts` (`id`, `customer_id`, `email`, `full_name`, `phone`, `is_primary`)

#### 3. Products & Pricing Catalog
* `product_categories` (`id`, `name`, `code`, `max_discount_ceiling_pct`)
* `products` (`id`, `sku`, `name`, `category_id`, `unit_of_measure`, `base_cost`, `base_list_price`, `is_active`)
* `product_variants` (`id`, `product_id`, `variant_code`, `name`, `price_adjustment`, `cost_adjustment`)
* `price_lists` (`id`, `name`, `tier_id`, `effective_start`, `effective_end`, `is_active`)
* `price_list_items` (`id`, `price_list_id`, `product_id`, `unit_price`)

#### 4. Quotations & Governance
* `quotations` (`id`, `quote_number`, `customer_id`, `sales_rep_id`, `status`, `fulfillment_status`, `billing_status`, `risk_score`, `subtotal`, `discount_total`, `tax_total`, `total_amount`, `total_cost`, `gross_margin_amount`, `gross_margin_pct`, `created_at`, `updated_at`)
* `quotation_lines` (`id`, `quotation_id`, `product_id`, `variant_id`, `line_type` [OneTime/Subscription], `billing_frequency`, `quantity`, `base_unit_price`, `discount_pct`, `selling_unit_price`, `unit_cost`, `line_total`, `line_cost`, `line_margin_amount`, `line_margin_pct`)
* `discount_policies` (`id`, `tier_id`, `category_id`, `max_discount_pct`)

#### 5. Approvals & Negotiation
* `approval_rules` (`id`, `min_risk_score`, `max_risk_score`, `required_role`)
* `approval_instances` (`id`, `quotation_id`, `approver_role`, `assigned_user_id`, `status` [Pending/Approved/Rejected], `comments`, `decided_at`)
* `negotiation_sessions` (`id`, `quotation_id`, `customer_contact_id`, `status`, `created_at`)
* `negotiation_comments` (`id`, `negotiation_session_id`, `quotation_line_id`, `author_role`, `message`, `created_at`)
* `negotiation_change_requests` (`id`, `negotiation_session_id`, `line_id`, `requested_qty`, `counter_discount_pct`, `status`)

#### 6. Inventory & Fulfillment
* `warehouses` (`id`, `code`, `name`, `location_city`, `shipping_weight_factor`)
* `inventory_items` (`id`, `warehouse_id`, `product_id`, `stock_qty`, `reserved_qty`, `allocated_qty`)
* `stock_reservations` (`id`, `quotation_line_id`, `warehouse_id`, `reserved_qty`, `expires_at`)
* `fulfillment_plans` (`id`, `quotation_id`, `status`, `created_at`)
* `shipments` (`id`, `fulfillment_plan_id`, `warehouse_id`, `carrier`, `tracking_number`, `shipped_at`)
* `backorders` (`id`, `quotation_line_id`, `backorder_qty`, `status` [Pending/Resolved], `expected_restock_date`)

#### 7. Billing & Subscriptions
* `invoices` (`id`, `invoice_number`, `quotation_id`, `customer_id`, `invoice_type` [OneTime/Recurring], `status` [Issued/Paid/Overdue], `total_amount`, `amount_paid`, `due_date`, `created_at`)
* `invoice_lines` (`id`, `invoice_id`, `quotation_line_id`, `amount`)
* `subscriptions` (`id`, `subscription_number`, `quotation_id`, `customer_id`, `status` [Active/Cancelled], `billing_frequency`, `recurring_amount`, `next_billing_date`)
* `billing_schedules` (`id`, `subscription_id`, `scheduled_date`, `amount`, `status` [Pending/Invoiced])
* `payments` (`id`, `invoice_id`, `amount`, `payment_method`, `reference_number`, `paid_at`, `recorded_by_user_id`)

#### 8. Health & Audit
* `deal_health_records` (`id`, `quotation_id`, `health_state` [Healthy/AtRisk/Critical], `stalled_days`, `slippage_days`, `score`, `evaluated_at`)
* `audit_events` (`id`, `actor_id`, `actor_role`, `action`, `entity_type`, `entity_id`, `before_state` [JSONB], `after_state` [JSONB], `ip_address`, `timestamp`)

---

# 5. QUOTATION REVISION & LIFECYCLE STATE MACHINE

Quotations transition through explicit, validated lifecycle states. Arbitrary status modifications are strictly forbidden.

```
                   ┌────────────────────────────────────────────────────────┐
                   │                                                        │
                   ▼                                                        │
┌───────┐     ┌───────────┐     ┌───────────┐     ┌───────────────────┐     │ (Re-Approval)
│ Draft │────>│  Pending  │────>│ Approved  │────>│ Under Negotiation │─────┘
└───────┘     │ Approval  │     └─────┬─────┘     └─────────┬─────────┘
              └─────┬─────┘           │                     │
                    │                 │                     │
                    ▼                 ▼                     ▼
               ┌───────────┐    ┌───────────┐         ┌───────────┐
               │ Rejected  │    │ Cancelled │         │ Confirmed │
               └───────────┘    └───────────┘         └───────────┘
```

### State Machine Transition Rules

| Initial State | Event / Action | Next State | Permitted Roles | Business Validation & Side Effects |
| :--- | :--- | :--- | :--- | :--- |
| `Draft` | `SUBMIT_FOR_APPROVAL` | `Pending Approval` | Sales Rep | Computes Risk Score. If Risk < 30, auto-transitions to `Approved`. |
| `Pending Approval` | `APPROVE_QUOTE` | `Approved` | Sales Manager / Finance | Validates approver role against risk band. Unlocks quote for customer sharing. |
| `Pending Approval` | `REJECT_QUOTE` | `Rejected` | Sales Manager / Finance | Mandatory comment requirement. Terminal quote state. |
| `Pending Approval` | `RETURN_FOR_REVISION`| `Draft` | Sales Manager / Finance | Unlocks quote for Sales Rep edits. Reset approval instances. |
| `Approved` | `SHARE_WITH_CUSTOMER`| `Under Negotiation` | Sales Rep | Generates customer portal token. |
| `Under Negotiation`| `CUSTOMER_COUNTER_OFFER`| `Pending Approval` | Customer (via API) | Server recalculates risk score. Re-approval triggered if thresholds breached. |
| `Under Negotiation`| `CUSTOMER_CONFIRM` | `Confirmed` | Customer (via API) | Freezes quotation data. Triggers Fulfillment & Billing initialization. |

---

# 6. DECOUPLED OPERATIONAL LIFECYCLES

Downstream operations maintain independent sub-state machines once a quote enters `Confirmed` state:

```
[QUOTATION STATUS]: Confirmed (Frozen)
  ├── [FULFILLMENT STATE]: Unfulfilled ──> Partially Allocated ──> Backordered ──> Fully Fulfilled
  ├── [BILLING STATE]:     Unbilled ──> Partially Billed ──> Fully Billed
  ├── [SUBSCRIPTION STATE]:Pending ──> Active ──> Modified ──> Cancelled
  └── [PAYMENT STATE]:     Unpaid ──> Partially Paid ──> Paid
```

---

# 7. AUTHORITATIVE PRICING ENGINE ARCHITECTURE

The `PricingEngine` resolves item prices through a deterministic hierarchy:

```
[Quote Line Input: Customer ID, Product ID, Variant ID, Quantity]
                              ↓
             [Check Customer-Specific Price List] ──(Found?)──> [Use Customer Price]
                              │ (No)
                              ▼
                [Check Customer Tier Price List] ──(Found?)──> [Use Tier Price]
                              │ (No)
                              ▼
               [Check Volume Quantity Break Rules] ──(Found?)──> [Use Tier/Volume Price]
                              │ (No)
                              ▼
                 [Fallback to Product Base List Price]
                              ↓
              [Apply Variant Price Adjustments (+/-)]
                              ↓
          [Final Server-Authoritative Unit Selling Price]
```

---

# 8. DISCOUNT GOVERNANCE & BLENDED RISK ENGINE ARCHITECTURE

### Risk Score Calculation Formula
The `DiscountGovernanceEngine` calculates the **Blended Discount Risk Score (0–100)**:

$$\text{Risk Score} = \min\left(100, \; S_{\text{breach}} + S_{\text{margin}} + S_{\text{volume}} + S_{\text{count}}\right)$$

Where:
* $S_{\text{breach}} = \sum \max\left(0, \text{Discount}_{\text{line}} - \text{Ceiling}_{\text{category/tier}}\right) \times 4.0$
* $S_{\text{margin}} = \max\left(0, \text{TargetMargin}_{\text{company}} - \text{OrderMargin}_{\text{actual}}\right) \times 2.5$
* $S_{\text{volume}} = \text{OrderTotal} > \$50,000 ? 15 : 0$
* $S_{\text{count}} = \text{Count}(\text{BreachingLines}) \times 5.0$

### Risk Bands & Routing Matrix
* **0 – 29 (Low Risk)**: Auto-Approved or Sales Rep self-approval.
* **30 – 69 (Medium Risk)**: Requires `Sales Manager` Approval.
* **70 – 100 (High Risk)**: Requires `Sales Manager` AND `Finance User` Dual Approval.

---

# 9. REAL-TIME MARGIN ENGINE ARCHITECTURE

The `MarginEngine` evaluates margin health across line items and order totals:

$$\text{Line Margin (\$)} = (\text{Selling Unit Price} - \text{Unit Base Cost}) \times \text{Quantity}$$

$$\text{Line Margin (\%) } = \left(\frac{\text{Line Margin (\$)}}{\text{Selling Unit Price} \times \text{Quantity}}\right) \times 100$$

$$\text{Order Gross Margin (\%)} = \left(\frac{\text{Total Revenue} - \text{Total Cost}}{\text{Total Revenue}}\right) \times 100$$

---

# 10. SMART MULTI-WAREHOUSE FULFILLMENT & BACKORDER ARCHITECTURE

### Allocation Algorithm Execution
Upon quote confirmation, `FulfillmentEngine` executes:
1. Fetch active inventory rows across warehouses with row locking:
   `SELECT * FROM inventory_items WHERE product_id = :product_id FOR UPDATE;`
2. **Single-Warehouse Preference**: If Warehouse A has stock $\ge$ line quantity, allocate 100% to Warehouse A.
3. **Split Allocation**: If no single warehouse has complete stock, split allocation across warehouses in order of highest stock availability and lowest shipping weight factor.
4. **Backorder Event**: If total available stock across all warehouses < line quantity:
   * Allocate all available stock.
   * Create `backorders` record for remaining quantity.
   * Lock partial reservations.

### Backorder Stock Arrival Consolidation
When new inventory arrives (`InventoryEngine.receive_stock`):
1. Query pending `backorders` ordered by quote confirmation date (FIFO).
2. Allocate newly received stock to pending backorders.
3. Upon full resolution of backorder quantity, update status to `Resolved` and trigger consolidated `Shipment` creation.

---

# 11. HYBRID BILLING & SUBSCRIPTION ENGINE ARCHITECTURE

```
                      ┌──> One-Time Lines ───> Invoice (Type: OneTime) ───> Payment Entry
                      │
[Confirmed Quotation]─┤
                      │
                      └──> Recurring Lines ──> Subscription ──> Billing Schedule ──> Recurring Invoices
```

### Proration Math for Mid-Period Subscription Modifications
For a subscription upgraded/cancelled mid-cycle (Day $d$ of $N$ total cycle days):

$$\text{Prorated Credit} = \text{Unused Portion} = \text{Recurring Price} \times \left(\frac{N - d}{N}\right)$$

$$\text{Prorated Charge} = \text{New Recurring Price} \times \left(\frac{N - d}{N}\right)$$

$$\text{Net Invoice Amount} = \text{Prorated Charge} - \text{Prorated Credit}$$

If Net Invoice Amount < 0, the system automatically generates a **Credit Note**.

---

# 12. DETERMINISTIC DEAL HEALTH & ANOMALY ENGINE

The `DealHealthEngine` evaluates active quotes against deterministic risk triggers:

```python
# Conceptual Health Evaluation Matrix
if approval_delay_days > 10 or delivery_slippage_days > 14 or risk_score >= 80:
    health_state = "CRITICAL"
elif approval_delay_days > 5 or margin_pct < 20.0 or negotiation_idle_days > 3:
    health_state = "AT_RISK"
else:
    health_state = "HEALTHY"
```

Every flagged anomaly generates an explainable `AnomalyRecord` banner displayed in the Command Center.

---

# 13. IMMUTABLE AUDIT TRAIL ARCHITECTURE

Audit logs are strictly **append-only**. Database triggers and backend API guards prevent `UPDATE` or `DELETE` operations on `audit_events`.

```json
{
  "timestamp": "2026-09-05T12:30:00Z",
  "actor_id": "usr_9981",
  "actor_role": "Sales Rep",
  "action": "QUOTE_DISCOUNT_APPLIED",
  "entity_type": "Quotation",
  "entity_id": "qte_4412",
  "before_state": { "discount_pct": 10.0, "risk_score": 25 },
  "after_state": { "discount_pct": 25.0, "risk_score": 78 },
  "ip_address": "192.168.1.45"
}
```

---

# 14. REST API SURFACE SPECIFICATION

| Route Prefix | HTTP Method | Endpoint Purpose | Authorized Roles |
| :--- | :--- | :--- | :--- |
| `/api/v1/auth` | `POST` | `/login`, `/logout`, `/refresh` | Public / Authenticated |
| `/api/v1/users` | `GET`, `POST` | User account management | `Admin` |
| `/api/v1/customers` | `GET`, `POST` | Customer account directory | `Sales Rep`, `Manager`, `Finance`, `Admin` |
| `/api/v1/products` | `GET`, `POST` | Product catalog & variants | `Sales Rep`, `Manager`, `Finance`, `Admin` |
| `/api/v1/pricing` | `GET`, `PUT` | Price lists & tier rules | `Finance`, `Admin` |
| `/api/v1/quotations` | `GET`, `POST`, `PUT`| Quotation CRUD & calculation | `Sales Rep`, `Manager`, `Finance`, `Admin` |
| `/api/v1/approvals` | `GET`, `POST` | Review approval queue & decide | `Sales Manager`, `Finance`, `Admin` |
| `/api/v1/portal` | `GET`, `POST` | Customer portal negotiation | `Customer` (Portal Token Isolated) |
| `/api/v1/fulfillment`| `GET`, `POST` | Warehouse allocation & splits | `Finance`, `Admin` |
| `/api/v1/backorders` | `GET`, `POST` | Backorder queue & consolidation| `Finance`, `Admin` |
| `/api/v1/billing` | `GET`, `POST` | Invoicing & subscription ops | `Finance`, `Admin` |
| `/api/v1/payments` | `POST` | Record payment transactions | `Finance`, `Admin` |
| `/api/v1/deal-health`| `GET` | Telemetry & anomaly feeds | `Sales Rep`, `Manager`, `Finance`, `Admin` |
| `/api/v1/reports` | `GET` | KPI queries, PDF & XLSX exports | `Manager`, `Finance`, `Admin` |
| `/api/v1/admin` | `GET`, `PUT` | System parameter configuration | `Admin` |

---

# 15. FRONTEND ARCHITECTURE & NEO GLASS COMPONENT TREE

The React application uses a modular layout with role-aware route guards and a centralized Neo Glass design system:

```
src/
├── components/ui/            # Neo Glass Primitives
│   ├── NeoGlassCard.tsx      # Frosted glass card with neo-brutalist border & hard shadow
│   ├── NeoGlassTable.tsx     # High-density glass grid with sticky header
│   ├── RiskScoreMeter.tsx    # Visual risk score gauge (0-100)
│   ├── StateBadge.tsx        # High-contrast state indicator pill
│   ├── MarginTelemetry.tsx   # Real-time cost vs margin split bar
│   └── ActionButton.tsx      # High-legibility neo-brutalist button
├── layouts/
│   ├── MainLayout.tsx        # Internal sidebar + top nav + shell
│   └── CustomerPortalLayout.tsx # Sandboxed portal layout
├── pages/
│   ├── CommandCenter.tsx
│   ├── QuotationBuilder.tsx
│   ├── ApprovalCenter.tsx
│   ├── NegotiationPortal.tsx
│   ├── FulfillmentCenter.tsx
│   └── BillingSubscriptions.tsx
└── services/
    └── api.ts                # Axios/Fetch client with auth token interceptor
```

---

# 16. CONCURRENCY CONTROL & TRANSACTION BOUNDARIES

To prevent race conditions during high-concurrency operations (e.g., inventory allocation, approval state changes):

1. **Pessimistic Row Locking**: Inventory updates execute with `SELECT ... FOR UPDATE` row locks within PostgreSQL transactions to guarantee stock consistency.
2. **Optimistic Versioning**: Quotations use an integer `version` field. State changes check `WHERE id = :id AND version = :expected_version` to prevent concurrent write collisions.

---

# 17. DEMO DATA DESIGN (KILLER DEMO FLOWS)

The seed data script (`seed_demo_data.py`) will populate realistic entities to execute the two core demo flows:

* **Demo Flow A Seed Data**:
  * Customer *Acme Industrial* (Gold Tier).
  * Products: *Enterprise Server X1* ($5,000 cost: $3,500), *Cloud License Annual* ($1,200/yr cost: $400).
  * Pre-configured Sales Manager & Finance approver accounts.
* **Demo Flow B Seed Data**:
  * 2 Physical Warehouses (*Boston East*, *Reno West*).
  * Stock levels: Boston has 7 units; Reno has 0 units (forces split & 3-unit backorder event).
  * Recurring subscription billing schedules.

---

# 18. DEFINITION OF DONE FOR PHASE 2

Phase 2 is complete when:
1. `docs/PHASE-2-FUNCTIONAL-ARCHITECTURE.md` exists and details the complete modular monolith architecture, database models, state machines, and API boundaries.
2. AI is completely excluded.
3. Server-authoritative logic, Neo Glass UI architecture, and 5-role RBAC are established.
4. Concurrency control, transaction boundaries, and audit trail architectures are defined.
5. No application source code, database tables, or dependencies have been created.

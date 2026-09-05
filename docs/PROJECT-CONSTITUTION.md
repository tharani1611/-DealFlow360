# DealFlow360 — Project Constitution & Master Implementation Rules

## Document Metadata
* **Status**: Official & Permanent Master Constitution
* **Product**: DealFlow360
* **Subtitle**: An Intelligent, Self-Governing Sales Operations Platform
* **Version**: 2.0 (Updated at Phase 0)

---

# 1. ABSOLUTE PROJECT IDENTITY & VISION

**DealFlow360** is an enterprise-grade sales operations platform designed to govern and automate the complete quotation-to-cash operational lifecycle. The platform connects sales, pricing, approval governance, customer negotiation, inventory fulfillment, hybrid billing, subscription cycles, deal health telemetry, and executive reporting into a unified, self-governing system.

### Central Business Object
The central business entity of the platform is the **Deal / Quotation**. All workflows, financial calculations, approval chains, customer interactions, warehouse allocations, billing events, and operational risk metrics revolve around and reference this primary entity.

### Complete Commercial Lifecycle
DealFlow360 governs the following sequential lifecycle steps:
`Customer` → `Deal` → `Quotation` → `Pricing` → `Discount Governance` → `Approval` → `Negotiation` → `Re-Approval` → `Fulfillment` → `Warehouse Allocation` → `Shipment` → `Backorder` → `Billing` → `Subscription` → `Payment` → `Deal Health` → `Analytics`

---

# 2. CRITICAL MANDATE: NO AI

**AI INTELLIGENCE IS NOT PART OF THIS PROJECT.**

The following are strictly prohibited and must NOT be introduced into DealFlow360:
* AI APIs, LLM APIs (Gemini, Claude, OpenAI, Copilot, etc.)
* AI agents, AI gateways, AI services, or AI recommendations
* AI prompts, AI keys, AI-generated business decisions, or AI dashboards

The self-governing intelligence in DealFlow360 derives exclusively from **deterministic server-side logic**:
* Deterministic business rules & decision matrices
* Authoritative pricing engines & tax determination
* Multi-tiered discount governance & blended risk scoring (0–100)
* Automated approval routing & escalation workflows
* Smart multi-warehouse inventory optimization & allocation rules
* Hybrid billing & subscription proration algorithms
* Rule-based deal-health detectors & anomaly monitors
* Operational analytics & structured reporting engines

---

# 3. OFFICIAL UI DESIGN SYSTEM: NEO GLASS

The visual design language for DealFlow360 is **Neo Glass**. This design system is permanent and must be strictly maintained across all user interfaces.

### Core Visual Pillars of Neo Glass
1. **Glassmorphism**:
   * Translucent background surfaces with controlled backdrop blur (`backdrop-filter: blur(...)`).
   * Layered panels with refractive depth and visual hierarchy.
   * Fine, semi-transparent border lines (`1px solid rgba(...)`).
   * Sophisticated frosted glass surfaces.
2. **Neo-Brutalism**:
   * Bold typography with confident font choices and high contrast.
   * Strong, high-contrast borders and defined geometric layout cards.
   * Intentional hard-edged shadow accents (`box-shadow` without excessive blur).
   * Expressive buttons and high-legibility interaction states (hover, focus, active).

### Application Rules for Neo Glass
* **Ubiquitous Application**: Applied consistently across all frontend areas (Auth, Command Center, Quotation Builder, Customer Portal, Fulfillment, Billing, Subscriptions, Deal Health, Admin, etc.).
* **Enterprise Usability**: Neo Glass must enhance usability, accessibility, and content legibility. It must never compromise responsiveness, performance, or WCAG AA color contrast standards.
* **Prohibited UI Patterns**: Bootstrap/Material default themes, flat generic dashboards, plain table templates, or "reinterpretations" into secondary design frameworks are strictly prohibited.

---

# 4. OFFICIAL USER ROLES & AUTHORIZATION BOUNDARIES

DealFlow360 recognizes exactly **five official user roles**:

1. **Sales Rep**: Creates quotes, configures items, applies discounts, submits quotes for approval, communicates with customers, and monitors quote progress.
2. **Sales Manager / Approver**: Evaluates discount requests, reviews blended risk metrics, approves or rejects deal submissions, and sets sales rules within delegation thresholds.
3. **Finance / Operations User**: Overrides high-risk pricing/discounts, manages warehouse allocations, configures subscription/billing rules, processes invoices/payments, and monitors backorder fulfillment.
4. **Customer / Portal User**: Strictly restricted external access to view shared quotations, submit line-item comments, request quantity/discount changes, and confirm proposals.
5. **Admin**: Manages system users, role definitions, audit logs, system configuration, master pricing catalogs, and tenant-wide rules.

*Note: No generic "Viewer" role is permitted. Frontend UI hiding is for UX only; security authority resides exclusively on the backend.*

---

# 5. CORE PRODUCT AREAS & DETERMINISTIC LOGIC

### 1. Customer Management
* Account profiles, contact management, customer tier classifications (e.g., Gold, Silver, Bronze), historical quote logs, and portal access credentials.

### 2. Product Catalog Management
* Master products, product categories, SKU variants, physical units of measure, tax codes, rich descriptions, and lifecycle statuses.

### 3. Pricing Engine
* Server-authoritative calculations for base prices, customer tier multipliers, product variants, volume quantity breaks, currency-specific rules, and tax determinations.

### 4. Discount Governance & Risk Engine
* Multi-tiered discount ceilings enforced by customer tier and product category.
* Real-time calculation of **Blended Discount Risk Score (0–100)** based on total margin impact, category threshold violations, customer historical tier, and volume variance.
* Automated workflow routing to Manager or Finance approvers. Complete audit records for every approval step.

### 5. Real-Time Margin Engine
* Server-authoritative calculation of base cost, selling price, gross margin, line-level margin, order-level margin, and margin delta upon applying discounts or upsells.

### 6. Deterministic Upsell & Cross-Sell Engine
* **No AI**. Driven by explicit configuration and historical business logic:
  * Co-purchase matrix rules
  * Related-product mapping
  * Minimum margin threshold validation
  * Category-level promotional rules

### 7. Approval Workflow Engine
* Multi-stage approval chains based on deal value, risk score, and delegation of authority limits. Supports Approve, Reject, Return for Revision, and Automatic Re-Approval.

---

# 6. CUSTOMER NEGOTIATION PORTAL PRINCIPLES

* **Isolated Security Boundary**: Customer portal users are sandboxed to their own organization's explicit deals via strict object-level authorization.
* **Interactive Negotiation**: Line-level commenting, change requests (quantity adjustments, term adjustments), and counter-discount submissions.
* **Automatic Re-Approval Trigger**: Any customer counter-offer or change request that breaches configured discount thresholds, margin floors, or total deal terms automatically resets approval state and triggers **Mandatory Re-Approval Workflow**.
* **Zero Client Trust**: All customer inputs, totals, and proposed prices are recalculated and validated server-side.

---

# 7. SMART FULFILLMENT & INVENTORY MANAGEMENT

* **Multi-Warehouse Support**: Tracks stock availability across multiple physical or logical warehouses.
* **Smart Allocation Engine**: Recommends warehouse splitting based on stock availability, shipping cost weighting, delivery promise times, and shipment count optimization.
* **Manual Override**: Finance/Operations users can manually adjust allocation splits.
* **Backorder Engine**: Concurrency-safe reservation of available inventory. Automatically places unfulfilled items on backorder and consolidates shipments when new stock arrives.
* **Slippage Telemetry**: Real-time tracking of estimated vs. actual delivery dates.

---

# 8. HYBRID & SUBSCRIPTION BILLING ARCHITECTURE

* **Hybrid Quote Support**: A single quote can simultaneously contain **One-Time Line Items** (hardware, setup fees) and **Recurring Subscription Items** (SaaS licenses, maintenance plans).
* **Billing Operations**:
  * One-time invoice generation upon fulfillment.
  * Automated subscription billing schedules (Monthly, Quarterly, Yearly).
  * In-place subscription modifications (upgrades, downgrades, cancellations).
  * Server-authoritative proration, credit note generation, and partial refund handling.
  * Payment recording and invoice status state tracking (Draft, Issued, Paid, Overdue, Voided).

---

# 9. DEAL HEALTH & OPERATIONS GOVERNANCE

Deal Health continuously monitors active deals against operational risk metrics:
* **Metrics**: Stalled quote duration, discount anomaly flags, delivery promise slippage, approval cycle bottlenecks, customer negotiation friction.
* **Health States**: `Healthy`, `At Risk`, `Critical`.
* **Actions**: Automated nudges, manager escalations, and direct quote deep-linking.

---

# 10. PERMANENT NON-NEGOTIABLE SECURITY PRINCIPLES

### Core Rule: THE FRONTEND IS NEVER TRUSTED.

1. **Backend Authority**: Authentication, authorization, RBAC, pricing math, discount validation, margin checks, inventory reservation, billing calculations, and state transitions are 100% server-authoritative.
2. **Authentication & Session**: Secure passlib/bcrypt password hashing, JWT/cookie-based sessions, token rotation, and invalidation.
3. **Authorization & RBAC**: Every API endpoint enforces role-based and object-level permissions (e.g., Sales Rep A cannot view Sales Rep B's unshared deals; Customer X cannot view Customer Y's portal).
4. **Input & Data Validation**: Pydantic schema validation for all API inputs and outputs. Prevention of SQL injection, XSS, and parameter tampering.
5. **Concurrency Safety**: Database row locking / optimistic locking for inventory reservations and quote status updates to eliminate race conditions.
6. **Secrets & Config**: Environment-variable based secrets management. Zero hardcoded secrets, keys, or credentials in source code.

---

# 11. SYSTEM AUDIT TRAIL STANDARDS

The system provides an immutable audit log for all critical operations:
* **Audited Events**: Authentication events, quote creation/updates, discount submissions, approval approvals/rejections, negotiation inputs, inventory overrides, backorders, invoice generation, payment records, subscription state changes, admin settings edits.
* **Audit Record Schema**: `timestamp`, `actor_id`, `actor_role`, `action_type`, `entity_name`, `entity_id`, `before_state`, `after_state`, `ip_address`, `user_agent`, `context_notes`.
* **Immutability**: Audit records cannot be modified or deleted via API endpoints or user roles.

---

# 12. MONOLITHIC ARCHITECTURE & TECHNOLOGY STACK

DealFlow360 is built as a **Clean Modular Monolith**. Microservices, distributed queues (Kafka), and complex container orchestrators (Kubernetes) are explicitly prohibited to maintain development velocity, transactional consistency, and architectural simplicity.

### Backend Stack
* **Language**: Python 3.11+
* **Framework**: FastAPI (Async API endpoints)
* **Database**: PostgreSQL
* **ORM & Driver**: SQLAlchemy 2.x (Async Engine) + asyncpg
* **Validation**: Pydantic v2
* **Database Migrations**: Alembic

### Frontend Stack
* **Framework**: React 18+ with TypeScript
* **Build Tool**: Vite
* **Routing**: React Router v6+
* **Styling**: Tailwind CSS + Custom CSS for Neo Glass design tokens

---

# 13. EXPECTED BACKEND MODULE BOUNDARIES

The backend architecture is structured into modular domain packages:
* `core` (Configuration, Database, Base Models, Security Utils)
* `auth` (Authentication, JWT, Session)
* `users` & `roles` (User management, RBAC enforcement)
* `audit` (Immutable audit logging)
* `customers` & `customer_tiers` (Customer master data)
* `products` & `variants` (Catalog & SKUs)
* `pricing` & `price_lists` (Authoritative price calculations)
* `warehouses` & `inventory` (Stock levels & reservations)
* `quotations` & `margins` & `discounts` (Quote domain logic & risk score)
* `approvals` (Workflow engine & delegation rules)
* `negotiation` (Customer portal back-and-forth logic)
* `fulfillment` & `shipments` & `backorders` (Logistics execution)
* `billing` & `subscriptions` & `payments` (Financial engine)
* `deal_health` (Telemetry & risk monitoring)
* `notifications` (System alert handlers)
* `reporting` (Analytics aggregations & export handlers)

---

# 14. EXPECTED FRONTEND AREA BOUNDARIES

The frontend user interface is partitioned into 18 dedicated, Neo Glass-styled operational areas:
1. `Authentication` (Login, Password Reset, Portal Access)
2. `Command Center` (Executive Overview, Operational KPI Dashboard)
3. `Sales Workspace` (Sales Rep Pipeline & Quote Workbench)
4. `Customer Management` (Accounts, Tiers, Contact Profiles)
5. `Product Catalog` (Products, Variants, Base Pricing)
6. `Pricing Rules` (Tiers, Price Lists, Tax Rules)
7. `Quotation Builder` (Line-item Configuration, Real-Time Margin Display)
8. `Approval Center` (Manager/Finance Queue & Risk Inspection)
9. `Customer Negotiation Portal` (External Customer Portal)
10. `Fulfillment Center` (Warehouse Allocation, Shipment Plans)
11. `Warehouse Management` (Location & Stock Levels)
12. `Backorder Queue` (Unfulfilled Lines & Stock Arrival Allocation)
13. `Billing & Invoicing` (One-Time Invoice Processing & Statuses)
14. `Subscription Manager` (Recurring Schedules, Upgrades, Proration)
15. `Payment Operations` (Payment Entry, Credit Notes, Partial Refunds)
16. `Deal Health Command` (Stalled Deal Telemetry & Delivery Slippage)
17. `Analytics & Reports` (Custom Exports & Performance Metrics)
18. `Administration` (RBAC, Audit Logs, System Settings)

---

# 15. PRIMARY BUSINESS FLOW & LIFECYCLE

```
[SECURE LOGIN]
      ↓
[COMMAND CENTER]
      ↓
[CUSTOMER / DEAL SELECTION]
      ↓
[QUOTATION BUILDER]
      ↓
[PRODUCTS & AUTHORITATIVE PRICING ENGINE]
      ↓
[REAL-TIME MARGIN & UPSELL ENGINE]
      ↓
[DISCOUNT GOVERNANCE & BLENDED RISK CALCULATION]
      ↓
[AUTOMATED APPROVAL ROUTING (Manager / Finance)]
      ↓
[CUSTOMER NEGOTIATION PORTAL]
      ↓
[CUSTOMER CHANGE REQUEST / COUNTER-OFFER]
      ↓
[SERVER RE-CALCULATE & GOVERNANCE RE-CHECK]
      ↓
[AUTOMATIC RE-APPROVAL WORKFLOW (if thresholds breached)]
      ↓
[QUOTE CONFIRMED & LOCKED]
      ↓
[SMART FULFILLMENT & MULTI-WAREHOUSE SPLIT]
      ↓
[INVENTORY RESERVATION / SHIPMENT PLAN]
      ↓
[BACKORDER HANDLING & STOCK CONSOLIDATION]
      ↓
[HYBRID BILLING GENERATION]
  ├── One-Time Invoice Execution
  └── Recurring Subscription Schedule Activation
      ↓
[PAYMENT RECORDING & RECEIPTING]
      ↓
[DEAL HEALTH MONITORING TELEMETRY]
      ↓
[EXECUTIVE ANALYTICS & EXPORTS]
```

---

# 16. KILLER DEMO FLOWS

### Killer Demo Flow A: The Governed Sales & Negotiation Cycle
1. **Quote Creation**: Sales Rep creates a new quote for Customer Alpha and adds Hardware + SaaS lines.
2. **Deterministic Upsell**: System recommends cross-sell attachment based on co-purchase rules; Sales Rep adds it.
3. **Margin Telemetry**: Real-time margin updates dynamically display gross margin impact.
4. **Discount Request**: Sales Rep applies a 25% discount, triggering a Blended Risk Score of 78/100.
5. **Approval Routing**: Quote is automatically routed to Sales Manager queue based on governance rules.
6. **Manager Approval**: Manager reviews risk score, margin impact, and approves the quote.
7. **Customer Portal**: Customer accesses the shared link, inspects line items, and submits a counter-offer requesting 30% discount.
8. **Recalculation & Re-Approval**: System recalculates risk, detects threshold breach, resets quote status to `Pending Re-Approval`, and routes to Finance.
9. **Final Confirmation**: Finance approves the counter-offer; customer confirms the quote.

### Killer Demo Flow B: Operations, Fulfillment & Hybrid Billing Cycle
1. **Confirmed Quote Trigger**: Confirmed quote transitions to fulfillment.
2. **Inventory Check**: System checks inventory across Warehouse East (Boston) and Warehouse West (Reno).
3. **Smart Allocation & Split**: System creates a split shipment plan (70% East, 30% West).
4. **Backorder Event**: Item B is out of stock; system places Item B on Backorder and reserves Item A.
5. **Consolidation**: Simulated stock arrival fulfills Item B; shipment is consolidated and dispatched.
6. **Hybrid Billing Generation**:
   * One-time invoice generated for Hardware + Shipping.
   * Subscription Schedule activated for monthly SaaS licenses.
7. **Payment & Health**: Payment recorded; invoice marked `Paid`. Deal health stays `Healthy`.

---

# 17. EXPLICIT OUT OF SCOPE BOUNDARIES

The following domains are explicitly **OUT OF SCOPE** and must NOT be implemented:
* ❌ Payroll processing
* ❌ Human Resources (HR) management
* ❌ Full Accounting General Ledger (GL)
* ❌ Complex external CRM integrations (Salesforce, HubSpot sync)
* ❌ SAML / Enterprise SSO / SCIM provisioning
* ❌ Microservices / Distributed queues / Kubernetes / Kafka / Redis
* ❌ AI / LLMs / Generative AI / AI Agents

---

# 18. MASTER IMPLEMENTATION ROADMAP (STEPS 0 – 81)

The implementation of DealFlow360 will proceed strictly according to the following 82 sequential steps:

```
Step 00: Project Constitution & Master Implementation Rules
Step 01: Product Definition & Boundaries
Step 02: Functional Architecture & Data Design
Step 03: Repository & Development Foundation Setup
Step 04: Database Foundation & Alembic Migration Engine
Step 05: Core Base Data Models & Utilities
Step 06: Security & Cryptography Foundation
Step 07: Authentication Engine (JWT, Hashing, Sessions)
Step 08: RBAC & Authorization Enforcement Engine
Step 09: Immutable Audit Logging System
Step 10: Customer Management Domain
Step 11: Product Catalog Management Domain
Step 12: Product Variant Engine
Step 13: Customer Tier Engine
Step 14: Price List & Authoritative Pricing Engine
Step 15: Warehouse Master Data Domain
Step 16: Subscription Plan Master Data
Step 17: Deterministic Upsell & Cross-sell Rule Engine
Step 18: Quotation Core Data Model
Step 19: Quotation Creation Services
Step 20: Server-Authoritative Quotation Pricing Engine
Step 21: Real-Time Margin Calculation Engine
Step 22: Quotation Lifecycle State Machine
Step 23: Discount Governance Engine
Step 24: Blended Discount Risk Score Engine
Step 25: Approval Rule Engine & Delegation Limits
Step 26: Approval Workflow Routing Engine
Step 27: Manager & Finance Approval Processing
Step 28: Approval Audit & History System
Step 29: Customer Portal Authentication & Token Isolation
Step 30: Customer Quotation Inspection Portal
Step 31: Line-Level Commenting & Discussion Engine
Step 32: Customer Change Request Engine
Step 33: Customer Counter-Discount Submission
Step 34: Customer Negotiation Recalculation Engine
Step 35: Automatic Re-Approval Trigger Engine
Step 36: Inventory Master Data Model
Step 37: Multi-Warehouse Stock Availability Engine
Step 38: Concurrency-Safe Inventory Reservation Engine
Step 39: Smart Multi-Warehouse Allocation & Split Engine
Step 40: Manual Fulfillment Override Engine
Step 41: Shipment Creation & Tracking Engine
Step 42: Backorder Tracking & Allocation Engine
Step 43: Stock Arrival Backorder Consolidation Engine
Step 44: Delivery Promise & Slippage Tracking Engine
Step 45: Hybrid Billing Model Core Architecture
Step 46: One-Time Invoice Generation Engine
Step 47: Payment Recording & Invoice Status Engine
Step 48: Subscription Schedule & Billing Engine
Step 49: Subscription Billing Cycle Execution Engine
Step 50: Server-Authoritative Proration Engine
Step 51: Subscription Modification & Cancellation Engine
Step 52: Credit Note & Partial Refund Engine
Step 53: Deal Health Telemetry & Calculation Engine
Step 54: Stalled Quotation Detection Engine
Step 55: Discount Anomaly Telemetry Monitoring
Step 56: Delivery Promise Slippage Telemetry Monitoring
Step 57: Operational Nudge & Escalation Engine
Step 58: Reporting & Aggregation Query Engine
Step 59: Analytics API Endpoints
Step 60: Frontend Vite + React + TS Architecture Setup
Step 61: Authentication & Role-Based Layout UI
Step 62: Command Center Dashboard UI
Step 63: Customer Management UI
Step 64: Product Catalog & Pricing Management UI
Step 65: Neo Glass Quotation Builder UI
Step 66: Approval Center UI & Blended Risk Viewer
Step 67: Isolated Customer Negotiation Portal UI
Step 68: Smart Fulfillment & Warehouse Split UI
Step 69: Hybrid Billing & Subscription Management UI
Step 70: Deal Health Command Center UI
Step 71: Executive Analytics & Administration UI
Step 72: End-to-End API Integration & Frontend Wiring
Step 73: End-to-End Business Lifecycle Flow Verification
Step 74: Backend Security & RBAC Penetration Testing
Step 75: Performance, Concurrency & Load Stress Testing
Step 76: Edge-Case Hardening & Error Boundary Polish
Step 77: Final Architecture & Security Audit
Step 78: Seed Data & Killer Demo Scenarios Setup
Step 79: Production Build Optimization & Deployment Config
Step 80: Final Neo Glass UI Polish
Step 81: Final Quality Assurance & Step-By-Step Signoff
```

---

# 19. EXPLICIT PROHIBITED PATTERNS

Never:
* ❌ Reintroduce AI, LLMs, AI agents, or AI dependencies.
* ❌ Replace Neo Glass with Bootstrap, Material UI, or generic templates.
* ❌ Trust frontend calculations or bypass backend authorization.
* ❌ Hardcode secrets, credentials, or API keys in client or server code.
* ❌ Fake business calculations, approvals, inventory, or billing states.
* ❌ Introduce microservices, Kafka, Redis, or Kubernetes.
* ❌ Implement future steps without explicit instruction.

---

# 20. DEFINITION OF DONE FOR PHASE 0

PHASE 0 is complete when:
1. `docs/PROJECT-CONSTITUTION.md` exists and contains the full content specified herein.
2. AI is explicitly excluded from the project architecture.
3. Neo Glass is explicitly established as the official UI design system.
4. The five official roles are documented.
5. Non-negotiable security principles and server authority are documented.
6. Core business flow and killer demo flows are documented.
7. The master 82-step roadmap (Steps 0–81) is established without omissions.
8. No application source code, database tables, or unnecessary dependencies have been created.
9. Execution stops immediately following Phase 0 completion report.

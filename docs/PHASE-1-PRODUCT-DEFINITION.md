# DealFlow360 — Phase 1: Functional Product Specification

## Document Information
* **Document Title**: Functional Product Specification & Systems Requirement Document
* **System Name**: DealFlow360 (An Intelligent, Self-Governing Sales Operations Platform)
* **Phase**: Phase 1 (Product Definition & Functional Specification)
* **Authoritative Reference**: [`docs/PROJECT-CONSTITUTION.md`](file:///c:/Users/lenovo/Desktop/DealFlow360/docs/PROJECT-CONSTITUTION.md)

---

# 1. PRODUCT VISION & SCOPE STATEMENT

**DealFlow360** is an enterprise-grade, self-governing sales operations platform engineered to manage, govern, and streamline the complete commercial quote-to-cash lifecycle. The platform eliminates uncontrolled discount leakage, enforces multi-department approval governance, handles complex multi-warehouse inventory constraints, supports secure customer negotiation, and unifies hybrid billing (one-time items + recurring subscriptions) with real-time deal health telemetry.

The platform is designed as a **single, connected commercial operating system**, eliminating fragmented workflows between sales reps, managers, finance teams, operations, and customers.

### Central Business Object
The foundational entity of DealFlow360 is the **Deal / Quotation**. Every workflow, financial calculation, approval routing, customer negotiation, inventory reservation, shipment plan, invoice generation, subscription cycle, and deal health metric references and mutates this central object.

### The Complete Connected Lifecycle
```
[Customer]
    ↓
[Deal / Opportunity]
    ↓
[Quotation Origination]
    ↓
[Authoritative Pricing Engine]
    ↓
[Discount Governance & Blended Risk Calculation]
    ↓
[Multi-Level Approval Workflow Engine]
    ↓
[Customer Negotiation Portal]
    ↓
[Server Recalculation & Automatic Re-Approval]
    ↓
[Confirmed Quotation Locking]
    ↓
[Smart Multi-Warehouse Inventory Fulfillment]
    ↓
[Backorder Tracking & Stock Arrival Consolidation]
    ↓
[Hybrid Billing Generation (One-Time Invoices + Subscription Schedules)]
    ↓
[Payment Operations & Credit Tracking]
    ↓
[Deal Health Telemetry & Operations Governance]
    ↓
[Executive Reporting & Financial Exports]
```

---

# 2. OFFICIAL USER ROLES & AUTHORIZATION SPECIFICATION

DealFlow360 defines exactly **five official user roles**. No generic "Viewer" or unauthenticated access roles exist.

| Role | Operational Purpose | Domain Responsibilities & Scope |
| :--- | :--- | :--- |
| **1. Sales Rep** | Frontline deal creation & sales execution | Creates & edits draft quotations; configures line items; views base pricing & costs; applies discounts within delegated tier ceilings; submits quotes for approval; manages customer negotiation threads; tracks fulfillment status; monitors deal health for assigned deals. |
| **2. Sales Manager / Approver** | Sales governance & commercial risk evaluation | Reviews pending approval queues; inspects blended discount risk scores (0–100) and margin impact; approves, rejects, or returns quotes for revision; sets sales rep delegation limits; monitors team pipeline performance. |
| **3. Finance / Operations User** | Financial compliance & operational logistics execution | Reviews high-risk discount requests; manages price lists, customer tiers, and discount ceiling rules; configures warehouse master data & manual inventory allocation overrides; generates one-time invoices; manages subscription billing, proration, and credit notes; records payments; monitors backorders. |
| **4. Customer / Portal User** | External deal inspection & proposal negotiation | Restricted external portal access; inspects shared quotations; submits line-item comments & change requests; submits counter-discount proposals; confirms approved proposals; accepts deal terms. |
| **5. Admin** | System administration & governance configuration | Manages user accounts & role assignments; manages system parameters; configures global pricing catalogs & tax tables; manages approval chains; inspects immutable audit logs; configures system settings. |

---

# 3. FUNCTIONAL DOMAINS SPECIFICATION

## A. Authentication & Security Domain
* **Internal Authentication**: Username/Email + Password authentication with bcrypt/passlib hashing. Secure session tokens (JWT/cookies) with configurable expiration and rotation.
* **Customer Portal Authentication**: Secure, token-isolated single-quotation portal access links (time-limited, cryptographically signed magic tokens or customer account portal logins).
* **Role-Based & Object-Level Access Control (RBAC/ABAC)**:
  * Sales Reps access only their owned or co-assigned quotations.
  * Approvers access quotes routed to their approval queue.
  * Customer Portal Users access *only* their explicit company quotations.
  * All access control is strictly enforced at the backend REST API layer.

## B. Customer Management Domain
* **Customer Accounts**: Master customer entity containing Legal Name, Trading Name, Tax Identifier, Account Status (Active/Suspended/On-Hold), Default Currency, Payment Terms (Net 30, Net 60, Due on Receipt), and Billing/Shipping Addresses.
* **Customer Tier Assignment**: Assignment to predefined tiers (Gold, Silver, Bronze, Standard) which directly drive pricing rules and discount ceiling thresholds.
* **Customer Contacts**: Contact profiles linked to accounts, designated for portal access credentials and notification routing.
* **Quotation History**: Unified ledger of all draft, approved, active, and completed quotations per customer.

## C. Product Management Domain
* **Master Product Catalog**: Products characterized by SKU, Name, Description, Product Category (Hardware, Software, Professional Services, Maintenance), Unit of Measure (Each, License, Hour, Month), Base List Price, Standard Unit Cost, and Tax Category.
* **Product Variants**: Attribute-based variants (e.g., Memory Size, Color, License Tier) with variant-specific price/cost adjustments.
* **Product Status**: Lifecycle status (`Active`, `Deprecated`, `Archived`). Inactive products cannot be added to new quotes.

## D. Pricing Engine Domain
* **Authoritative Price Calculation**: Server calculates line item unit price based on strict precedence rules:
  1. *Customer-Specific Price List* (highest priority)
  2. *Customer Tier Discount / Price List*
  3. *Volume Quantity Break Rules*
  4. *Base Product List Price* (fallback)
* **Effective Date Range**: Price lists enforce `effective_start_date` and `effective_end_date`.
* **Server Authority**: Client-side prices are treated purely as visual displays. The backend recalculates and overwrites any client-submitted price.

---

# 4. DISCOUNT GOVERNANCE & BLENDED RISK ENGINE

Discount Governance prevents margin erosion by enforcing deterministic rules and calculating a real-time **Blended Discount Risk Score (0–100)**.

### Governance Rules Architecture
1. **Customer-Tier Ceilings**: Maximum allowable discount percentage by customer tier and product category.
   * *Example*: Gold Tier → Hardware Max Discount: 15%, Services Max Discount: 10%.
   * *Example*: Standard Tier → Hardware Max Discount: 5%, Services Max Discount: 0%.
2. **Category-Specific Ceiling Override**: Product categories enforce hard ceiling limits regardless of customer tier unless overridden by Finance approval.
3. **Order-Level vs. Line-Level Discounts**: Order-level overall discounts are algorithmically prorated across line items to verify category-level compliance.

### Blended Discount Risk Score Model (0–100)
The risk score is calculated server-side using a deterministic weighted formula:

$$\text{Risk Score} = \min\left(100, w_1 \cdot \text{Ceiling Breach} + w_2 \cdot \text{Margin Impact} + w_3 \cdot \text{Deal Volume} + w_4 \cdot \text{Violation Count}\right)$$

* **Ceiling Breach Points**: Points added for each line item exceeding its configured category/tier ceiling based on percentage points over limit.
* **Margin Impact Points**: Points added based on the delta between base target gross margin and discounted gross margin.
* **Deal Volume Points**: High-value deals with breaches incur additional scrutiny weight.
* **Violation Count Points**: Multiplier based on the number of distinct line items breaching rules.

### Risk Tier Categorization
* **0 – 29 (Low Risk)**: Within rep delegation limits. Automatic approval or direct submission to customer.
* **30 – 69 (Medium Risk)**: Exceeds rep limits. Requires **Sales Manager** approval.
* **70 – 100 (High Risk)**: Severe discount or margin erosion. Requires **Sales Manager + Finance** dual approval.

---

# 5. REAL-TIME MARGIN ENGINE

The Margin Engine provides instant financial transparency on every quotation modification:

* **Unit Base Cost**: Standard cost associated with the product SKU/variant.
* **Selling Unit Price**: Final effective unit price after authoritative tier pricing and approved discounts.
* **Line Gross Margin ($)**: `(Selling Unit Price - Unit Base Cost) * Quantity`
* **Line Gross Margin (%)**: `(Line Gross Margin ($) / Line Total Revenue ($)) * 100`
* **Order Total Revenue ($)**: Sum of all line item final revenues.
* **Order Total Cost ($)**: Sum of all line item total costs.
* **Order Gross Margin ($)**: `Order Total Revenue - Order Total Cost`
* **Order Gross Margin (%)**: `(Order Gross Margin ($) / Order Total Revenue ($)) * 100`
* **Margin Delta ($ & %)**: Real-time comparison showing margin impact before and after discount/upsell changes.

---

# 6. MULTI-LEVEL APPROVAL WORKFLOW ENGINE

The approval system routes deal submissions based on the deterministic risk score and organizational delegation limits.

```
[Sales Rep Submits Quote]
           ↓
[Server Calculates Risk Score & Margin]
           ↓
    ┌──────┴────────────────────────┬────────────────────────┐
    ↓                               ↓                        ↓
[Risk Score < 30]           [30 <= Risk Score < 70]   [Risk Score >= 70]
(Low Risk)                  (Medium Risk)             (High Risk)
    ↓                               ↓                        ↓
[Auto-Approved]             [Sales Manager Queue]     [Sales Manager Queue]
    ↓                               ↓                        ↓
[Ready for Customer]        [Manager Approves]        [Manager Approves]
                                    ↓                        ↓
                            [Ready for Customer]      [Finance Queue]
                                                             ↓
                                                      [Finance Approves]
                                                             ↓
                                                      [Ready for Customer]
```

### Approval Actions
* **Approve**: Advances quote state to `Approved`. Quote is locked against edits by Sales Rep and unlocked for Customer sharing.
* **Reject**: Rejects quote with mandatory reason notes. Quote transitions to `Rejected`.
* **Return for Revision**: Returns quote to Sales Rep with required adjustment notes. Quote transitions to `Draft`.

---

# 7. QUOTATION LIFECYCLE & QUOTATION BUILDER

### Explicit Quotation State Machine
Quotations maintain an explicit lifecycle state model:

* `Draft`: Initial quote creation and editing by Sales Rep.
* `Pending Approval`: Submitted for manager/finance approval. Locked against edits.
* `Approved`: Fully approved internally. Ready for customer presentation.
* `Rejected`: Rejected during internal approval. Terminal state unless cloned.
* `Under Negotiation`: Shared with customer; customer actively reviewing or commenting.
* `Changes Requested`: Customer submitted counter-offer or line change request.
* `Confirmed`: Customer formally accepted deal terms. Quote is frozen and ready for execution.
* `Cancelled`: Deal cancelled by sales team or customer.
* `Expired`: Validity date lapsed without customer confirmation.

```
 [Draft] ───> [Pending Approval] ───> [Approved] ───> [Under Negotiation] ───> [Confirmed]
    │                │                   │                     │                     │
    ▼                ▼                   ▼                     ▼                     ▼
[Cancelled]      [Rejected]         [Cancelled]       [Changes Requested]        [Execution]
                                                               │
                                                               ▼
                                                      [Re-Approval Required]
```

### Independent Execution Lifecycles
Crucially, **Fulfillment** and **Billing** operate on decoupled sub-states once a quote is `Confirmed`:

* **Fulfillment Sub-State**: `Unfulfilled` → `Partially Fulfilled` → `Backordered` → `Fully Fulfilled`
* **Billing Sub-State**: `Unbilled` → `Partially Billed` → `Fully Billed`
* **Subscription Sub-State**: `Inactive` → `Active` → `Modified` → `Cancelled`

### Quotation Builder Workspace
The Quotation Builder UI allows Sales Reps to:
* Search products/variants and add lines.
* Specify line type: **One-Time Purchase** vs. **Recurring Subscription** (Billing Frequency: Monthly, Quarterly, Yearly).
* Edit quantities, base prices, line discounts, and shipping estimates.
* View real-time line margins, order total margin, discount risk score meter, and fulfillment stock availability preview.

---

# 8. DETERMINISTIC UPSELL & CROSS-SELL ENGINE

DealFlow360 implements a **100% deterministic recommendation engine** (No AI).

### Recommendation Logic Rules
1. **Co-Purchase Rules**: Configured mappings (e.g., If Product A [Server Hardware] is added, recommend Product B [Rack Mount Kit]).
2. **Category Attachment Rules**: Configured category recommendations (e.g., If Software License is added, recommend Annual Maintenance Plan).
3. **Margin Floor Check**: Recommendations are filtered to ensure suggested products meet minimum target margin thresholds.
4. **Promotional Bundles**: Pre-configured bundle rules offering volume or complementary product discounts.

### UI Representation
Recommendations appear as actionable Neo Glass drawer cards displaying:
* Product Name & SKU
* Trigger Reason (e.g., *"Frequently purchased with Server Hardware"*)
* Price Impact & Additional Margin Contribution
* Actions: `[Add to Quote]` or `[Dismiss]`

---

# 9. CUSTOMER NEGOTIATION PORTAL

The Customer Portal provides a secure, restricted external surface for proposal evaluation and interactive negotiation.

### Customer Capabilities
* **Inspect Quotation**: View itemized line details, quantities, unit prices, total contract value, payment terms, and delivery promises.
* **Line-Level Commenting**: Post contextual discussion threads on specific line items.
* **Change Requests**: Request quantity adjustments or specification modifications.
* **Counter-Discount Proposals**: Submit counter-offer discount percentages or target total price.
* **Confirm Proposal**: Digitally confirm and accept the quotation.

### Server Recalculation & Automatic Re-Approval Trigger
When a customer submits a negotiation response:
1. Server recalculates prices, taxes, totals, gross margin, and blended discount risk.
2. If counter-proposed terms breach configured discount ceilings or margin floors:
   * Status automatically transitions from `Under Negotiation` to `Changes Requested / Pending Re-Approval`.
   * An automated re-approval task is routed to the Sales Manager / Finance queue.
   * **No customer-submitted total or price is trusted without server re-verification.**

---

# 10. SMART MULTI-WAREHOUSE FULFILLMENT

The Fulfillment Engine optimizes logistics across multiple physical warehouses.

### Smart Allocation Algorithm
Upon quote confirmation, the system analyzes stock availability across all active warehouses and recommends an optimal allocation plan based on:
1. **Stock Availability**: Direct matching of line quantities to warehouse stock levels.
2. **Shipment Minimization**: Prioritizes fulfilling from a single warehouse to minimize split shipments.
3. **Shipping Cost Weighting**: Factor in shipping origin distance/cost rules.
4. **Manual Override**: Operations users can override recommended allocations and split lines across warehouses manually.

---

# 11. BACKORDER TRACKING & CONSOLIDATION ENGINE

When total stock across warehouses is insufficient for a confirmed line item:

1. **Backorder Creation**: The unfulfilled quantity is automatically assigned to a `Backorder` state linked to the quotation line item.
2. **Stock Reservation**: Available partial stock is reserved immediately to prevent allocation race conditions.
3. **Delivery Promise Slippage Alert**: Estimated stock arrival date is tracked against the original promised delivery date.
4. **Stock Arrival Consolidation**: When new inventory is received (purchase order arrival), the backorder engine automatically consolidates pending backorders and generates a consolidated shipment plan.

---

# 12. DELIVERY PROMISE & SLIPPAGE TELEMETRY

* **Promised Delivery Date**: Date committed to the customer during quote confirmation.
* **Estimated Delivery Date**: Calculated date based on current warehouse allocation and stock availability.
* **Actual Delivery Date**: Recorded upon carrier dispatch/fulfillment completion.
* **Slippage Telemetry**: System automatically flags lines where `Estimated Delivery Date > Promised Delivery Date` with visual `Slippage Warning` badges, triggering operational nudges.

---

# 13. HYBRID & SUBSCRIPTION BILLING MODEL

DealFlow360 handles quotations containing both **One-Time Products** and **Recurring Subscriptions** within a single commercial document.

```
                     ┌──> One-Time Items ───> One-Time Invoice ───> Payment Entry
                     │
[Confirmed Quote] ───┤
                     │
                     └──> Recurring Items ──> Subscription Plan ──> Billing Schedule ──> Recurring Invoices
```

### 1. One-Time Billing Execution
* Generates standard accounts receivable invoices upon fulfillment completion.
* Invoice status tracking: `Draft` → `Issued` → `Partially Paid` → `Paid` → `Overdue` / `Voided`.

### 2. Subscription Billing Execution
* Creates active subscription schedules for recurring lines (Monthly, Quarterly, Annual).
* Automated billing schedule generator creates recurring invoice drafts at each billing interval.
* Supports **In-Place Modifications**: Upgrades, downgrades, and cancellations.
* **Server-Authoritative Proration**: Calculates exact prorated charges for mid-cycle changes.
* **Credit Notes & Partial Refunds**: Issues credit notes for unearned revenue on cancelled subscriptions or returned items.

---

# 14. PAYMENT OPERATIONS

* **Payment Recording**: Internal manual entry of payment transactions against issued invoices (Check, Wire Transfer, Credit Card reference).
* **Partial Payment Handling**: Tracks balance due per invoice; automatically updates status to `Partially Paid`.
* **Payment Ledger**: Complete transaction history containing Payment Date, Amount, Payment Method, Reference Number, Recorded By, and Invoice ID.

---

# 15. DETERMINISTIC DEAL HEALTH ENGINE

Deal Health monitors active commercial pipeline items to prevent deal stagnation and operational failure (100% Rule-Based, No AI).

### Deal Health Classification Rules
* **Healthy (Green)**: Quote progressing normally within standard SLA timeframes; margin within target; no fulfillment slippage.
* **At Risk (Yellow)**: Quote stagnant in `Draft` or `Pending Approval` for > 5 business days; minor margin compression; customer negotiation counter-offer pending > 3 days.
* **Critical (Red)**: Approval delayed > 10 days; delivery slippage > 14 days; high discount risk score (>80); backorder stalled without restock date.

---

# 16. DETERMINISTIC ANOMALY DETECTION

The system monitors quote data for operational anomalies using transparent rule matrices:
* **High Discount Anomaly**: Quote discount exceeds customer historical tier average by > 15 percentage points.
* **Margin Compression Anomaly**: Total deal gross margin drops below company-wide minimum threshold (e.g., < 20%).
* **Repeated Threshold Violation**: User repeatedly resubmits quote just 0.1% below approval limits.
* **Rule Explanation**: Every anomaly banner displays an explicit, human-readable rationale (e.g., *"Flagged: Hardware discount of 28% exceeds Gold tier norm of 15%"*).

---

# 17. OPERATIONAL NUDGES & ESCALATIONS

Automated background triggers generate operational notifications for critical events:

| Trigger Event | Target Recipient | Severity | Escalation Action |
| :--- | :--- | :--- | :--- |
| Approval Pending > 48 Hours | Sales Manager | Medium | Email / In-App Nudge |
| Approval Pending > 96 Hours | Finance Director | High | Automated Escalation to Senior Approver |
| Customer Counter-Offer Received | Sales Rep | High | In-App Alert + Deal Health update |
| Delivery Promise Slippage > 7 Days | Operations Manager | High | Backorder Queue Priority Flag |
| Invoice Overdue > 30 Days | Finance User | High | Automated Account Hold Warning |

---

# 18. REPORTING & ANALYTICS SPECIFICATION

The reporting module delivers executive operational insights across standard commercial dimensions.

### Reporting Dimensions
* **Filter Dimensions**: Date Range, Sales Team, Sales Representative, Deal Status, Product Category, Customer Tier.
* **Core KPI Metrics**:
  * Total Quote Volume & Pipeline Value
  * Average Discount Percentage & Total Discount Value
  * Overall Gross Margin ($ & %)
  * Approval SLA Cycles & Rejection Rates
  * Warehouse Allocation Splits & Backorder Rate
  * Annual Recurring Revenue (ARR) & Monthly Recurring Revenue (MRR) from Subscriptions
  * Accounts Receivable Days Sales Outstanding (DSO)

### Export Standards
* **PDF Export**: Formatted, print-ready Quotation PDFs, Invoices, and Executive Summaries.
* **XLSX Export**: Native multi-tab Excel workbooks containing detailed line-item financial data, formulas, and summary aggregations. *(CSV is explicitly insufficient).*

---

# 19. ADMINISTRATION WORKSPACE SPECIFICATION

Centralized configuration console accessible exclusively to the `Admin` role:
* **User & Role Management**: Create users, assign roles, define sales teams, and set manager reporting hierarchies.
* **Pricing & Discount Governance Rules**: Configure base price lists, customer tiers, category discount ceilings, and blended risk weighting coefficients.
* **Approval Chain Configurator**: Define multi-stage approval thresholds, delegation limits, and backup approvers.
* **Warehouse Master Data**: Register warehouse locations, shipping cost weights, and inventory locations.
* **Subscription Plan Catalog**: Define standard billing intervals, proration rules, and grace periods.
* **Deterministic Recommendation Rules**: Manage co-purchase rules, category cross-sell mappings, and bundle promotions.
* **Immutable Audit Trail Viewer**: Searchable, filterable log of all system audit records.

---

# 20. COMMAND CENTER WORKSPACE SPECIFICATION

The primary operational dashboard for internal users (Sales Reps, Managers, Finance, Ops), rendered using the **Neo Glass** design system.

### Command Center Panels
1. **Executive KPI Header**: Real-time metric cards for Active Pipeline Value, Blended Margin %, Pending Approvals Count, Backorder Lines Count, and Monthly Recurring Revenue.
2. **Action Queue**: Role-specific task cards (e.g., Approver: *"3 Quotes Awaiting Review"*; Sales Rep: *"2 Customer Counter-Offers Received"*).
3. **Pipeline Velocity Matrix**: Visual pipeline state breakdown with deal health status badges.
4. **Operational Risk & Anomaly Feed**: Live feed of flagged discount anomalies, stalled quotes, and delivery slippages.

---

# 21. NEO GLASS UX DESIGN SYSTEM SPECIFICATION

The UI design system for DealFlow360 is strictly **Neo Glass** (Glassmorphism + Neo-Brutalism).

### Visual Tokens & Primitives
* **Surfaces**: Semi-transparent dark/light glass panels (`background: rgba(15, 23, 42, 0.75)`, `backdrop-filter: blur(16px)`).
* **Borders**: Sharp 1px solid borders (`border: 1px solid rgba(255, 255, 255, 0.12)`) paired with high-contrast structural dividers.
* **Shadows**: Distinctive neo-brutalist hard drop shadows (`box-shadow: 4px 4px 0px rgba(0, 0, 0, 0.5)`).
* **Typography**: Clean, bold sans-serif type hierarchy (Inter / JetBrains Mono for monetary figures) with deliberate size contrast.
* **Color Palette**: Dark slate frosted backgrounds, vivid cyan/violet primary actions, high-visibility status accents (Emerald for Healthy, Amber for At-Risk, Crimson for Critical/High-Risk).

### Conceptual UI Component Registry
* `NeoGlassCard`: Container with frosted backdrop and hard drop-shadow border.
* `NeoGlassTable`: High-density data grid with translucent rows, sticky headers, and clear hover highlights.
* `RiskScoreMeter`: Visual dial/bar displaying blended discount risk (0–100) with color transition.
* `StateBadge`: High-contrast status pill indicating quote state, health, or fulfillment status.
* `MarginTelemetryBar`: Real-time visual split bar showing Cost vs. Gross Margin percentage.

---

# 22. DOMAIN SECURITY REQUIREMENTS SPECIFICATION

| Domain | Security Vulnerability / Risk | Mandatory Backend Protection |
| :--- | :--- | :--- |
| **Customer Domain** | Multi-tenant data leakage | Strict tenant/account ownership filtering on all DB queries. |
| **Quotation Domain** | Unauthorized quote modification | Object-level authorization enforcing sales rep ownership or manager scope. |
| **Pricing Domain** | Client price manipulation | 100% server-authoritative price recalculation; client price inputs rejected. |
| **Discount Governance** | Bypassing discount ceilings | Server validation of line & order discounts against database rules. |
| **Approval Domain** | Self-approval or escalation bypass | State transition validation checking authenticated user role & risk score rules. |
| **Negotiation Domain** | Cross-customer quote tampering | Signed, single-quote token isolation for customer portal access. |
| **Inventory Domain** | Reservation race conditions | Database row-level locking (`SELECT ... FOR UPDATE`) during inventory reservations. |
| **Billing Domain** | Duplicate invoicing / state corruption | Explicit state machine transitions; transactional DB operations. |
| **Admin Domain** | Unauthorized privilege escalation | Admin-only API middleware guards on all administrative routes. |
| **Audit Domain** | Audit log tampering | Immutable append-only audit records; no UPDATE/DELETE API endpoints. |

---

# 23. FORMAL BUSINESS RULE SPECIFICATION FRAMEWORK

Every major operational workflow in DealFlow360 follows this strict specification pattern:

### Standard Pattern Example: Discounted Quote Submission
1. **User Action**: Sales Rep clicks `[Submit for Approval]` on a draft quotation.
2. **Business Rule**:
   * Calculate line item totals and gross margin.
   * Calculate Blended Discount Risk Score based on category ceilings, margin impact, and deal value.
   * Determine required approval level (Low Risk → Auto, Medium → Manager, High → Manager + Finance).
3. **State Transition**: Quote status changes from `Draft` to `Pending Approval`.
4. **Validation**: Check that quote has at least 1 line item, valid customer account, and non-expired base prices.
5. **Audit Record**: Log event `QUOTE_SUBMITTED_FOR_APPROVAL` with `actor_id`, `quote_id`, `risk_score`, and `calculated_margin`.

---

# 24. REQUIREMENT CLASSIFICATION (MUST / SHOULD / OPTIONAL)

### MUST HAVE (Mandatory MVP Scope for Demo Flows)
* Complete 5-Role Security & RBAC enforcement.
* Neo Glass Design System across all frontend screens.
* Server-authoritative Pricing & Real-Time Margin calculation.
* Discount Governance & Blended Risk Score Engine (0–100).
* Multi-Level Approval Engine (Manager & Finance routing).
* Isolated Customer Negotiation Portal with counter-discount submit & automatic re-approval.
* Smart Multi-Warehouse Inventory Fulfillment & Allocation Split.
* Backorder Engine with stock arrival consolidation.
* Hybrid Billing Engine (One-time invoices + Recurring subscription schedules).
* Deterministic Deal Health Engine & Anomaly Detection.
* Native PDF & XLSX reporting exports.
* Killer Demo Flow A & Killer Demo Flow B execution.

### SHOULD HAVE (High Priority Operational Refinements)
* Granular notification preferences per user role.
* Advanced audit trail search and diff visualization.
* Bulk stock allocation override tools for Finance users.

### OPTIONAL (Deferred / Lower Priority)
* Custom theme accent color customization in Neo Glass.
* Automated carrier tracking API integration (mock carrier tracking used instead).

---

# 25. EXPLICIT OUT OF SCOPE BOUNDARIES

The following capabilities are explicitly **OUT OF SCOPE** and will **NOT** be created:
* ❌ Artificial Intelligence, LLMs, AI agents, AI gateways, or AI recommendations.
* ❌ General Ledger (GL) accounting, payroll, or HR management.
* ❌ External CRM sync engines (Salesforce/HubSpot connectors).
* ❌ SAML 2.0 / SCIM enterprise SSO protocols.
* ❌ Microservices, Kafka, Redis, or Kubernetes deployment infrastructure.

---

# 26. KILLER DEMO SCENARIOS SPECIFICATION

### Killer Demo Flow A: Governed Sales & Customer Negotiation
1. **Quote Origination**: Sales Rep creates Quote `Q-1001` for Customer *Acme Corp* (Gold Tier).
2. **Line Configuration**: Adds 10x Server Hardware ($5,000/ea) + 12-Month SaaS Subscription ($1,000/mo).
3. **Margin Telemetry**: System displays Gross Margin: $18,000 (30.0%).
4. **Discount Application**: Sales Rep applies 25% discount to Hardware (Exceeds Gold ceiling of 15%).
5. **Governance Calculation**: Blended Risk Score calculated as `78/100` (High Risk).
6. **Approval Routing**: Quote automatically transitions to `Pending Approval` and appears in Sales Manager & Finance queues.
7. **Approval Processing**: Manager & Finance inspect risk telemetry and click `[Approve]`. Status updates to `Approved`.
8. **Customer Portal Access**: Customer accesses secure portal link, reviews line items, and submits a counter-offer requesting 30% Hardware discount.
9. **Automatic Re-Approval**: Server recalculates risk (`86/100`), detects threshold breach, resets status to `Pending Re-Approval`, and notifies Finance.
10. **Confirmation**: Finance approves counter-offer; customer clicks `[Confirm Quotation]`.

### Killer Demo Flow B: Fulfillment, Backorders & Hybrid Billing
1. **Confirmed Quote Execution**: Quote `Q-1001` confirmed; transitions to fulfillment pipeline.
2. **Stock Inspection**: Warehouse East has 7 Servers; Warehouse West has 0 Servers (3 Servers short).
3. **Smart Allocation & Split**: System allocates 7 Servers to Warehouse East; 3 Servers placed on `Backorder`.
4. **Shipment Dispatch**: Shipment `SH-001` created and dispatched for available 7 Servers.
5. **Backorder Consolidation**: Purchase order arrives at Warehouse West receiving 5 Servers; system automatically allocates 3 Servers, resolves Backorder, and creates Shipment `SH-002`.
6. **Hybrid Billing Generation**:
   * One-time invoice `INV-1001` generated for 10x Servers + Shipping.
   * Subscription Schedule `SUB-1001` activated for $1,000/mo SaaS licenses.
7. **Payment & Health**: Payment recorded for `INV-1001`; invoice status marked `Paid`. Deal health stays `Healthy`.

---

# 27. DEFINITION OF DONE FOR PHASE 1

Phase 1 is complete when:
1. `docs/PHASE-1-PRODUCT-DEFINITION.md` exists and accurately captures all functional domain specifications.
2. The central role of the **Deal / Quotation** entity is fully documented.
3. AI is explicitly excluded and deterministic rules defined.
4. Neo Glass visual principles and primitive components are specified.
5. All 5 official user roles and security boundaries are fully detailed.
6. The Blended Risk Score model, Margin Engine, Approval Workflow, Customer Portal, Smart Fulfillment, Backorder Engine, Hybrid Billing, and Deal Health domains are specified.
7. Killer Demo Flows A & B are mapped end-to-end.
8. No application source code, database tables, or dependencies have been created.

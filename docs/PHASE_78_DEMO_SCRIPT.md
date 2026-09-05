# DealFlow360 — Phase 78: Demo Script & Presentation Guide

## 1. Executive Summary
This document provides a repeatable, end-to-end presentation flow for demonstrating DealFlow360 to executive buyers, sales leaders, and technical evaluators. Every scenario is backed by real server-side state machines, financial validations, inventory reservation locks, and multi-tenant security boundaries.

---

## 2. Environment Setup & Personas

### CLI Commands
- **Seed Demo Environment**: `python scripts/seed_demo_data.py`
- **Reset / Teardown**: `python scripts/reset_demo_data.py`

### User Credentials
All users share the default demonstration password: `Password123!`

| Persona | Email | Role / Scope | Primary Demo Value |
|---|---|---|---|
| **System Administrator** | `admin@dealflow.demo` | Organization Admin | System settings, tenant management, workflow rules |
| **Sales Executive** | `sales@dealflow.demo` | Sales / CPQ Rep | Deal pipeline, quotation builder, catalog browsing |
| **Business Owner / Exec** | `owner@dealflow.demo` | Executive Approver | Margin governance, executive discount sign-off |
| **Inventory Manager** | `inventory@dealflow.demo` | Fulfillment / Warehouse | Stock levels, multi-warehouse allocations, backorders |
| **Purchasing Agent** | `purchase@dealflow.demo` | Procurement | Raw material ordering, vendor pricing |
| **Manufacturing Supervisor** | `manufacturing@dealflow.demo` | Production / Assembly | BOM component consumption, assembly completion |
| **Customer Portal User** | `sarah.jenkins@acmecorp.com` | Customer Contact | Interactive proposal review, line notes, discount requests |

---

## 3. 10 Showcase Scenarios Walkthrough

### Scenario 1: Healthy Sales & Revenue Cycle
- **Customer**: Acme Corporation
- **Story**: Standard frictionless enterprise purchase. A quotation is drafted for 10x Ergonomic Executive Desk and 10x Acoustic Meeting Pod ($24,000 gross).
- **Flow**: Quotation transitions `DRAFT` → `PRICED` → `SENT` → `ACCEPTED` → `CONVERTED`. An authoritative tax/discount invoice is generated and settled with a full payment ($24,000). The associated deal automatically advances to `WON`.
- **Takeaway**: Seamless quote-to-cash velocity with automated financial journal settlement.

### Scenario 2: High Discount Governance & Owner Approval
- **Customer**: Global Dynamics
- **Story**: Sales rep offers an aggressive 20% discount on 20x Ergonomic Desks ($16,000 net vs $20,000 gross), breaching the 15% automatic threshold.
- **Flow**: Quotation enters `PENDING_APPROVAL`. Business Owner logs in, reviews the commercial margin risk breakdown, and approves the quote. Quotation unlocks to `PRICED` status.
- **Takeaway**: Strict margin governance preventing unauthorized discounting while keeping reps informed.

### Scenario 3: Customer Portal Interactive Negotiation
- **Customer**: Acme Corporation (`sarah.jenkins@acmecorp.com`)
- **Story**: Buyer reviews quote online, asks questions directly on specific line items, and formally requests a counter-discount.
- **Flow**: Sarah opens quotation in Portal, adds a line comment asking for bulk rates, and submits a change request for 10% discount. Sales rep reviews change request in CRM, approves it, generating an incremented version `v2`.
- **Takeaway**: Real-time collaborative negotiation eliminating offline PDF/email clutter.

### Scenario 4: Real-Time Stock Shortage Detection
- **Customer**: TechFlow Systems
- **Story**: Customer requests 15x Heavy-Duty Steel Pod Frames when only 10 units are physically in stock across all warehouses.
- **Flow**: When sales generates the quote, the engine flags a stock warning (`available: 10, requested: 15`). Prevents unfulfillable delivery promises before quote acceptance.
- **Takeaway**: Transparent inventory visibility directly inside the CPQ quoting workflow.

### Scenario 5: Component Manufacturing & Assembly
- **Customer**: Internal Operations / Stock replenishment
- **Story**: Assembling Acoustic Meeting Pods from raw BOM components (Steel Frames, Soundproof Panels, Oak Desks).
- **Flow**: Production order consumes 2x Steel Frames and 8x Acoustic Foam Panels, deducting raw material balances and crediting 2x Finished Meeting Pods to Central Warehouse.
- **Takeaway**: Integrated light manufacturing without needing external ERP handoffs.

### Scenario 6: Multi-Warehouse Split Delivery & Backorders
- **Customer**: Apex Innovations
- **Story**: Order requires 12x Ergonomic Desks. Central Warehouse holds 8 units, East Coast Warehouse holds 0 units.
- **Flow**: System fulfills 8 units immediately via Central Warehouse shipment (`SHP-2026-000001`), and automatically creates a tracked Backorder (`BO-2026-000001`) for the remaining 4 units.
- **Takeaway**: Intelligent multi-location logistics ensuring zero lost revenue from partial stockouts.

### Scenario 7: Milestone Billing & Split Payments
- **Customer**: Apex Innovations
- **Story**: $5,200 commercial contract billed on net-30 terms.
- **Flow**: Invoice `INV-2026-000002` created. Customer pays 50% deposit ($2,600) via Bank Transfer → Status updates to `PARTIALLY_PAID` with remaining balance tracked. Second payment of $2,600 settles the invoice to `PAID`.
- **Takeaway**: Authoritative partial payment reconciliation with precise balance tracking.

### Scenario 8: SaaS Subscription Billing & Prorated Cancellation
- **Customer**: TechFlow Systems
- **Story**: Annual SaaS recurring contract for Workspace Monitoring Suite ($1,200/yr).
- **Flow**: Subscription created with monthly billing schedule. Mid-period cancellation executed with exact day-level proration calculation, creating credit record and freezing future schedules.
- **Takeaway**: Compliant recurring revenue lifecycle management with automated proration math.

### Scenario 9: AI Telemetry & Predictive Risk Detection
- **Customer**: Nova Creative (Healthy) vs Starlight Health (At-Risk)
- **Story**: Telemetry scan analyzing deal velocity, customer touchpoints, and quote age.
- **Flow**: Nova Creative deal scores `85+ HEALTHY` (recent executive meetings, active quotes). Starlight Health scores `25 CRITICAL` (overdue follow-ups, stale 18-day inactivity).
- **Takeaway**: Early risk warnings enabling sales managers to rescue stalled opportunities before quarter-end.

### Scenario 10: Deterministic Workflow Automation
- **Customer**: Starlight Health
- **Story**: High-value deal creation ($68,000) automatically triggering executive engagement.
- **Flow**: `DEAL_CREATED` event evaluates rule condition (`deal.value >= 50000`). Action executes deterministically, creating a priority task for executive sponsor outreach and logging execution telemetry.
- **Takeaway**: Event-driven CRM automations ensuring high-value deals receive immediate executive attention.

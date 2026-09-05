# DealFlow360 — Bulk Data Seeding & High-Volume Dataset Architecture

## 1. Overview & Purpose

The **DealFlow360 Bulk Data Seeding System** provides a deterministic, high-volume synthetic business dataset containing **9,684+ interconnected records** for testing, analytics, performance benchmarking, pagination, search, filtering, and investor demonstrations.

All generated records are strictly isolated under the dedicated analytics tenant:
- **Organization Name:** `DealFlow360 Analytics Lab`
- **Slug:** `bulk-data-lab`
- **Isolation Test Organization:** `DealFlow360 Isolation Testing Lab` (`bulk-isolation-lab`)

Existing demo environments (`demo-enterprise`, `acme-global`) and production data remain completely unmodified and isolated.

---

## 2. Dataset Architecture & Record Counts

The bulk dataset models a complete commercial, fulfillment, billing, and AI intelligence lifecycle across 200 B2B customers, 120 products, 10 regional warehouses, and 350 enterprise sales opportunities:

| Domain | Entity / Table | Generated Count | Description |
| :--- | :--- | :---: | :--- |
| **Core Master Data** | Tenants (`Organization`) | **2** | Primary Analytics Lab + Secondary Isolation Lab |
| | Staff & Admin Users (`User`) | **21** | Admins, VPs, Account Execs, Inventory, Billing Staff |
| | Portal Users (`PortalUser`) | **25** | Customer contacts authenticated for negotiation portal |
| | B2B Customers (`Customer`) | **200** | Realistic enterprises across 10 Indian metropolitan hubs |
| | Customer Contacts (`Contact`) | **300** | Heads of Procurement and Operations Managers |
| | Products (`Product`) | **120** | Furniture, Equipment, Hospitality, Software, Services, BOMs |
| | Product Variants (`ProductVariant`) | **248** | Finish, size, and tier overrides |
| | Regional Warehouses (`Warehouse`) | **10** | Mumbai, BLR, Delhi, HYD, Pune, AMD, Chennai, Kolkata, Jaipur |
| **Pricing & Governance** | Pricing Rules (`PricingRule`) | **120** | Volume, contract, and promotional pricing tiers |
| | Discount Policies (`DiscountPolicy`) | **60** | Role-based, customer-specific, and product discount caps |
| | Recommendation Rules | **80** | Upsell and cross-sell commercial intelligence |
| | Approval Rules (`ApprovalRule`) | **4** | Multi-tier approval thresholds (10%, 15%, 22%, 30%+) |
| **Commercial Operations** | Sales Deals (`Deal`) | **350** | Opportunities distributed across stages and values |
| | Quotations (`Quotation`) | **350** | Draft, priced, sent, accepted, rejected, expired, converted |
| | Quotation Line Items (`QuotationItem`) | **1,241** | Exact `Decimal` calculations (Subtotal, Discount, Tax, Total) |
| | Quotation State Histories | **350** | Immutable state transition audit trail |
| | Quotation Approvals | **128** | Multi-level approval requests (Pending, Approved, Rejected) |
| | Approval Audit Logs | **128** | Append-only decision audit logs |
| | Quotation Line Comments | **116** | Collaborative internal and customer portal discussions |
| | Quotation Change Requests | **116** | Customer counter-discount proposals and approvals |
| | Quotation Versions (`QuotationVersion`) | **350** | Snapshot version payloads and gross margin history |
| | Commercial Classifications | **350** | One-time, recurring, and hybrid billing classifications |
| **Inventory & Fulfillment** | Stock Distributions (`InventoryStock`) | **605** | Healthy, low, zero, and reserved multi-warehouse stock |
| | Inventory Movements | **500** | Stock receipts and warehouse adjustments |
| | Stock Reservations | **385** | Active and consumed quotation reservations |
| | Warehouse Item Allocations | **385** | Single-warehouse and split allocations |
| | Physical Shipments (`Shipment`) | **110** | Draft, Ready, Packed, Shipped, In-Transit, Delivered |
| | Shipment Lines (`ShipmentLine`) | **385** | Manifested dispatch items with carrier tracking |
| | Backorder Shortfalls (`Backorder`) | **13** | Unfulfilled quantity backlog tracking |
| | Delivery SLA Promises | **110** | Promised vs actual delivery timeline tracking |
| **Billing & Revenue** | Invoices (`Invoice`) | **110** | Draft, Issued, Partially Paid, Paid, Overdue |
| | Invoice Line Items (`InvoiceItem`) | **385** | Itemized invoice lines with tax and discount |
| | Completed Payments (`Payment`) | **108** | Bank transfer, Card, UPI, Cheque settlements |
| | Credit Notes (`CreditNote`) | **11** | Receivable reductions and early payment rebates |
| | Credit Note Items | **11** | Rebate item breakdown |
| | Payment Cash Refunds | **11** | Reimbursement cash payouts linked to payments |
| **Subscriptions** | Subscriptions (`Subscription`) | **87** | Active, Paused, Cancelled SaaS recurring licenses |
| | Recurring Billing Schedules | **348** | Scheduled and Paid monthly billing schedules |
| | Subscription Cancellations | **11** | End-of-period cancellation audit logs |
| **Deal Health & AI** | Deal Health Snapshots | **350** | Deterministic score (20–95) with positive/negative drivers |
| | Anomaly Monitoring Events | **145** | Stalled quotes, discount anomalies, delivery slippage |
| | Nudges & Escalations (`Nudge`) | **145** | Deal stalled alerts with deduplication hashes |
| | Nudge Transition Histories | **145** | Audit log of nudge status changes |
| | CRM Activities (`Activity`) | **350** | Tasks, calls, meetings, follow-ups |
| **Automation Engine** | Automation Workflow Rules | **5** | Event trigger definitions and condition trees |
| | Automation Executions | **150** | Workflow run logs (Success, Failed, Partial) |
| | Execution Action Logs | **150** | Individual step outcomes and dispatch results |
| **TOTAL DATASET** | **Total Generated Records** | **9,684** | **Substantially exceeds 1,000+ requirement** |

---

## 3. CLI Commands & Execution

### A. Seed Bulk Data

To generate or reseed the complete 9,684+ record dataset:

```powershell
cd C:\Users\lenovo\Desktop\DealFlow360\backend
& .venv\Scripts\python.exe scripts/seed_bulk_data.py --count 5000
```

*Execution Time:* **~2.7 seconds** (via batched inserts and dependency flushes).

### B. Reset Bulk Data (Safe Purge)

To safely purge only the bulk analytics tenants (`bulk-data-lab`, `bulk-isolation-lab`) without affecting demo or production tenants:

```powershell
cd C:\Users\lenovo\Desktop\DealFlow360\backend
& .venv\Scripts\python.exe scripts/reset_bulk_data.py --confirm
```

> [!IMPORTANT]
> The `--confirm` flag is mandatory. Executing without `--confirm` will abort with a safety notice.

---

## 4. Multi-Tenant Isolation & Security Guarantees

1. **Zero Tenant Bleed:** Every single record in the bulk dataset contains `organization_id = org_bulk.id`.
2. **Query Sandboxing:** API requests authenticated as `admin@dealflow.demo` (`demo-enterprise`) cannot access any records from `bulk-data-lab`.
3. **Dedicated Lab Admin:**
   - **Slug:** `bulk-data-lab`
   - **Email:** `lab.admin@dealflow.test`
   - **Password:** `BulkPass123!`
4. **Synthetic Data Policy:**
   - All customer names, contact emails (`@dealflow.test`), and phone numbers are purely synthetic.
   - Zero real personal identifiable information (PII) is included.

---

## 5. Financial & Business Invariants

- **Exact Decimal Precision:** All unit prices, discounts, taxes, line subtotals, invoice balances, and payments use `Decimal` with `ROUND_HALF_UP`.
- **Zero Negative Inventory:** Every warehouse stock record enforces `on_hand_quantity >= 0`, `reserved_quantity >= 0`, and `available_quantity = on_hand - reserved`.
- **Valid State Machines:** All quotation, shipment, invoice, payment, and subscription statuses strictly comply with the application's domain state machines.
- **Relational Integrity:** Zero orphan records; all foreign keys, versions, audit logs, and allocations maintain strict relational consistency.

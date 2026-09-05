# DealFlow360 — Resized Bulk Data Seeding & Analytics Dataset Architecture

## 1. Overview & Purpose

The **DealFlow360 Bulk Data Seeding System** provides a deterministic, medium-sized synthetic business dataset containing **~3,500 interconnected records** (with **100–200 records for major business entities** such as 120 customers, 120 products, 120 deals, and 120 quotations) for testing, analytics, performance benchmarking, pagination, search, filtering, and investor demonstrations.

All generated records are strictly isolated under the dedicated analytics tenant:
- **Organization Name:** `DealFlow360 Analytics Lab`
- **Slug:** `bulk-data-lab`
- **Isolation Test Organization:** `DealFlow360 Isolation Testing Lab` (`bulk-isolation-lab`)

Existing demo environments (`demo-enterprise`, `acme-global`) and production data remain completely unmodified and isolated.

---

## 2. Dataset Architecture & Record Counts

The bulk dataset models a complete commercial, fulfillment, billing, and AI intelligence lifecycle across 120 B2B customers, 120 products, 10 regional warehouses, 120 sales deals, and 120 quotations:

| Domain | Entity / Table | Generated Count | Description |
| :--- | :--- | :---: | :--- |
| **Core Master Data** | Tenants (`Organization`) | **2** | Primary Analytics Lab + Secondary Isolation Lab |
| | Staff & Admin Users (`User`) | **20** | Admins, VPs, Account Execs, Inventory, Billing Staff |
| | Portal Users (`PortalUser`) | **20** | Customer contacts authenticated for negotiation portal |
| | B2B Customers (`Customer`) | **120** | Realistic enterprises across 10 Indian metropolitan hubs |
| | Customer Contacts (`Contact`) | **180** | Heads of Procurement and Operations Managers |
| | Products (`Product`) | **120** | Furniture, Equipment, Hospitality, Software, Services, BOMs |
| | Product Variants (`ProductVariant`) | **240** | Finish, size, and tier overrides |
| | Regional Warehouses (`Warehouse`) | **10** | Mumbai, BLR, Delhi, HYD, Pune, AMD, Chennai, Kolkata, Jaipur |
| **Pricing & Governance** | Pricing Rules (`PricingRule`) | **100** | Volume, contract, and promotional pricing tiers |
| | Discount Policies (`DiscountPolicy`) | **60** | Role-based, customer-specific, and product discount caps |
| | Recommendation Rules | **80** | Upsell and cross-sell commercial intelligence |
| | Approval Rules (`ApprovalRule`) | **4** | Multi-tier approval thresholds (10%, 15%, 22%, 30%+) |
| **Commercial Operations** | Sales Deals (`Deal`) | **120** | Opportunities distributed across stages and values |
| | Quotations (`Quotation`) | **120** | Draft, priced, sent, accepted, rejected, expired, converted |
| | Quotation Line Items (`QuotationItem`) | **~360** | Exact `Decimal` calculations (Subtotal, Discount, Tax, Total) |
| | Quotation State Histories | **120** | Immutable state transition audit trail |
| | Quotation Approvals | **~35** | Multi-level approval requests (Pending, Approved, Rejected) |
| | Approval Audit Logs | **~35** | Append-only decision audit logs |
| | Quotation Line Comments | **~40** | Collaborative internal and customer portal discussions |
| | Quotation Change Requests | **~40** | Customer counter-discount proposals and approvals |
| | Quotation Versions (`QuotationVersion`) | **120** | Snapshot version payloads and gross margin history |
| | Commercial Classifications | **120** | One-time, recurring, and hybrid billing classifications |
| **Inventory & Fulfillment** | Stock Distributions (`InventoryStock`) | **~360** | Multi-warehouse stock locations |
| | Inventory Movements | **~360** | Stock receipts and warehouse movements |
| | Stock Reservations | **~125** | Active and consumed quotation reservations |
| | Warehouse Item Allocations | **~125** | Single-warehouse and split allocations |
| | Physical Shipments (`Shipment`) | **~50** | Draft, Ready, Packed, Shipped, In-Transit, Delivered |
| | Shipment Lines (`ShipmentLine`) | **~125** | Manifested dispatch items with carrier tracking |
| | Backorder Shortfalls (`Backorder`) | **~10** | Unfulfilled quantity backlog tracking |
| | Delivery SLA Promises | **~50** | Promised vs actual delivery timeline tracking |
| **Billing & Revenue** | Invoices (`Invoice`) | **~50** | Draft, Issued, Partially Paid, Paid, Overdue |
| | Invoice Line Items (`InvoiceItem`) | **~125** | Itemized invoice lines with tax and discount |
| | Completed Payments (`Payment`) | **~40** | Bank transfer, Card, UPI settlements |
| | Credit Notes (`CreditNote`) | **~5** | Receivable reductions and early payment rebates |
| | Credit Note Items | **~5** | Rebate item breakdown |
| | Payment Cash Refunds | **~5** | Reimbursement cash payouts linked to payments |
| **Subscriptions** | Subscriptions (`Subscription`) | **~30** | Active SaaS recurring licenses |
| | Recurring Billing Schedules | **~120** | Scheduled and Paid monthly billing schedules |
| | Subscription Cancellations | **~6** | End-of-period cancellation audit logs |
| **Deal Health & AI** | Deal Health Snapshots | **120** | Score (20–95) with positive/negative drivers |
| | Anomaly Monitoring Events | **~35** | Stalled quotes, discount anomalies, delivery slippage |
| | Nudges & Escalations (`Nudge`) | **~35** | Deal stalled alerts with deduplication hashes |
| | Nudge Transition Histories | **~35** | Audit log of nudge status changes |
| | CRM Activities (`Activity`) | **120** | Tasks, calls, meetings, follow-ups |
| **Automation Engine** | Automation Workflow Rules | **5** | Event trigger definitions and condition trees |
| | Automation Executions | **80** | Workflow run logs (Success, Failed, Partial) |
| | Execution Action Logs | **80** | Individual step outcomes and dispatch results |
| **TOTAL DATASET** | **Total Generated Records** | **~3,600** | **Resized realistic medium-volume dataset** |

---

## 3. CLI Commands & Execution

### A. Seed Bulk Data

To generate or reseed the resized ~3,600 record dataset:

```powershell
cd C:\Users\lenovo\Desktop\DealFlow360\backend
& .venv\Scripts\python.exe scripts/seed_bulk_data.py
```

*Execution Time:* **~1.2 seconds**.

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

All records generated by the bulk seeder belong exclusively to `bulk-data-lab` and `bulk-isolation-lab`. `demo-enterprise` and `acme-global` are strictly preserved and untouched.

# DealFlow360 — Resized Synthetic Record Dataset Documentation

## 1. Overview & Goal

The **DealFlow360 Synthetic Data Seeding System** populates a realistic, relationally connected business dataset of **100–200 records for major entities** (~3,500 total records) into a dedicated, isolated tenant space (`bulk-data-lab`) for application testing, investor demos, and analytics exploration.

### Target Tenant Details
- **Organization Name:** `DealFlow360 Analytics Lab`
- **Slug:** `bulk-data-lab`
- **Isolation Guarantee:** Operates strictly within `bulk-data-lab` (and `bulk-isolation-lab`). Production data and existing demo tenants (`demo-enterprise`, `acme-global`) are 100% isolated and preserved.

---

## 2. Dataset Entity Breakdown

| Business Domain | Entity / Model | Count | Description |
| :--- | :--- | :---: | :--- |
| **Organization & Users** | `Organization` | **2** | `DealFlow360 Analytics Lab` + `Isolation Lab` |
| | Staff & Admin Users (`User`) | **20** | Admins, Sales Directors, Account Execs, Inventory Managers |
| | Portal Users (`PortalUser`) | **20** | Authenticated customer representatives for portal negotiation |
| **Customers & Contacts** | Customers (`Customer`) | **120** | Realistic B2B companies across Indian metropolitan hubs |
| | Contacts (`Contact`) | **180** | Procurement leads and operations managers |
| **Product & Pricing** | Products (`Product`) | **120** | Office Furniture, Electronics, SaaS licenses, and Components |
| | Product Variants (`ProductVariant`) | **240** | Wood finish, color, and tier overrides |
| | Pricing Rules (`PricingRule`) | **100** | Volume-based pricing tiers |
| | Discount Policies (`DiscountPolicy`) | **60** | Governance policies capping rep discounts |
| **Warehouses & Inventory** | Warehouses (`Warehouse`) | **10** | Regional fulfillment hubs |
| | Stock Distribution (`InventoryStock`) | **~360** | On-hand, reserved, and available stock levels |
| **Sales & Commercial** | Deals (`Deal`) | **120** | Opportunities across proposal and won stages |
| | Quotations (`Quotation`) | **120** | Draft, priced, sent, accepted, rejected, expired, converted |
| | Quotation Items (`QuotationItem`) | **~360** | Itemized lines with exact Decimal tax & discount math |
| **Approvals & Governance** | Quotation Approvals (`QuotationApproval`) | **~35** | Multi-tier discount approval requests |
| | Approval Audit Logs (`ApprovalAuditLog`) | **~35** | Append-only audit logs for governance compliance |
| | Line Comments (`QuotationLineComment`) | **~40** | Customer-rep line item negotiation comments |
| | Change Requests (`QuotationChangeRequest`) | **~40** | Customer counter-discount proposals |
| | Quotation Versions (`QuotationVersion`) | **120** | Historic snapshot versions with gross margin metrics |
| **Fulfillment & Logistics** | Physical Shipments (`Shipment`) | **~50** | Dispatched and delivered warehouse shipments |
| | Shipment Line Items (`ShipmentLine`) | **~125** | Dispatched product line items |
| | Backorders (`Backorder`) | **~10** | Unfulfilled shortfall quantity trackers |
| **Billing & Financials** | Invoices (`Invoice`) | **~50** | Issued, partially paid, and fully settled invoices |
| | Invoice Line Items (`InvoiceItem`) | **~125** | Itemized invoice lines with tax and subtotal |
| | Completed Payments (`Payment`) | **~40** | Bank transfer payment settlements |
| **Subscriptions** | Subscriptions (`Subscription`) | **~30** | Monthly SaaS recurring customer subscriptions |
| | Billing Schedules (`BillingSchedule`) | **~120** | Scheduled and Paid monthly billing runs |
| **AI, Health & Monitoring** | Deal Health Snapshots | **120** | Health scores (15–95) with positive/negative drivers |
| | Anomaly Monitoring Events | **~35** | Automated anomaly flags for stalled quotes & discount risks |
| | Active Nudges & Escalations (`Nudge`) | **~35** | Contextual follow-up recommendations with dedup hashes |
| | Nudge Histories (`NudgeHistory`) | **~35** | Status transition logs for nudges |
| | CRM Activities (`Activity`) | **120** | Scheduled calls and commercial alignment meetings |
| | Automation Engine | **~165** | Rules, executions, and action logs |
| **TOTAL DATASET** | **Total Generated Records** | **~3,600** | **Resized realistic medium-volume dataset** |

---

## 3. CLI Commands

### A. Seed Resized Synthetic Dataset
Populates ~3,600 connected synthetic records into PostgreSQL under `bulk-data-lab`:

```powershell
cd C:\Users\lenovo\Desktop\DealFlow360\backend
& .venv\Scripts\python.exe scripts/seed_200_data.py
```

### B. Reset Synthetic Dataset
Safely wipes records belonging strictly to `bulk-data-lab`:

```powershell
cd C:\Users\lenovo\Desktop\DealFlow360\backend
& .venv\Scripts\python.exe -c "import asyncio; from app.seed.bulk_seeder import reset_bulk_data; asyncio.run(reset_bulk_data())"
```

---

## 4. Verification & Testing

Run the dedicated test suite:

```powershell
cd C:\Users\lenovo\Desktop\DealFlow360\backend
& .venv\Scripts\pytest.exe tests/test_seed_200_data.py
```

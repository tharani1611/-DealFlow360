# DealFlow360 — 200 Synthetic Record Dataset Documentation

## 1. Overview & Goal

The **DealFlow360 200 Synthetic Data Seeding System** populates a realistic, relationally connected business dataset of **371 records** (substantially exceeding the ~200 record requirement) into a dedicated, isolated tenant space for application testing, investor demos, and analytics exploration.

### Target Tenant Details
- **Organization Name:** `DealFlow360 Analytics Lab`
- **Slug:** `bulk-data-lab`
- **Isolation Guarantee:** Operates strictly within `bulk-data-lab`. Production data and existing demo tenants (`demo-enterprise`, `acme-global`) are 100% isolated and preserved.

---

## 2. Dataset Entity Breakdown

| Business Domain | Entity / Model | Count | Description |
| :--- | :--- | :---: | :--- |
| **Organization & Users** | `Organization` | **1** | `DealFlow360 Analytics Lab` (`bulk-data-lab`) |
| | Staff & Admin Users (`User`) | **4** | Admin, Sales Director, Senior Account Exec, Inventory Manager |
| | Portal Users (`PortalUser`) | **5** | Authenticated customer representatives for portal negotiation |
| **Customers & Contacts** | Customers (`Customer`) | **20** | Realistic B2B companies across 15 Indian metropolitan hubs |
| | Contacts (`Contact`) | **20** | Heads of Procurement for each B2B customer |
| **Product & Pricing** | Products (`Product`) | **20** | Office Furniture, Electronics, SaaS licenses, and Components |
| | Product Variants (`ProductVariant`) | **15** | Wood finish, color, and tier overrides |
| | Pricing Rules (`PricingRule`) | **5** | Volume-based pricing tiers |
| | Discount Policies (`DiscountPolicy`) | **5** | Governance policies capping rep discounts |
| **Warehouses & Inventory** | Warehouses (`Warehouse`) | **3** | Ahmedabad Central, Mumbai East, Bangalore West |
| | Stock Distribution (`InventoryStock`) | **15** | On-hand, reserved, and available stock levels |
| **Sales & Commercial** | Deals (`Deal`) | **30** | Expansion opportunities across proposal and won stages |
| | Quotations (`Quotation`) | **30** | Draft, priced, sent, accepted, rejected, expired, converted |
| | Quotation Items (`QuotationItem`) | **64** | Itemized lines with exact Decimal tax & discount math |
| **Approvals & Governance** | Quotation Approvals (`QuotationApproval`) | **5** | Multi-tier discount approval requests |
| | Approval Audit Logs (`ApprovalAuditLog`) | **5** | Append-only audit logs for governance compliance |
| | Line Comments (`QuotationLineComment`) | **5** | Customer-rep line item negotiation comments |
| | Change Requests (`QuotationChangeRequest`) | **5** | Customer counter-discount proposals |
| | Quotation Versions (`QuotationVersion`) | **5** | Historic snapshot versions with gross margin metrics |
| **Fulfillment & Logistics** | Physical Shipments (`Shipment`) | **5** | Dispatched and delivered warehouse shipments |
| | Shipment Line Items (`ShipmentLine`) | **5** | Dispatched product line items |
| | Backorders (`Backorder`) | **3** | Unfulfilled shortfall quantity trackers |
| **Billing & Financials** | Invoices (`Invoice`) | **10** | Issued, partially paid, and fully settled invoices |
| | Invoice Line Items (`InvoiceItem`) | **10** | Itemized invoice lines with tax and subtotal |
| | Completed Payments (`Payment`) | **8** | Bank transfer payment settlements |
| **Subscriptions** | Subscriptions (`Subscription`) | **5** | Monthly SaaS recurring customer subscriptions |
| | Billing Schedules (`BillingSchedule`) | **15** | Past completed and future scheduled billing runs |
| **AI, Health & Monitoring** | Deal Health Snapshots | **10** | Health scores (15–95) with positive/negative drivers |
| | Anomaly Monitoring Events | **5** | Automated anomaly flags for stalled quotes & discount risks |
| | Active Nudges & Escalations (`Nudge`) | **5** | Contextual follow-up recommendations with dedup hashes |
| | Nudge Histories (`NudgeHistory`) | **5** | Status transition logs for nudges |
| | CRM Activities (`Activity`) | **10** | Scheduled calls and commercial alignment meetings |
| | Automation Rules & Executions | **13** | Workflow trigger rules, executions, and action logs |
| **TOTAL DATASET** | **Total Generated Records** | **371** | **Exceeds ~200 record objective** |

---

## 3. CLI Commands

### A. Seed 200 Synthetic Dataset
Populates ~371 connected synthetic records into PostgreSQL under `bulk-data-lab`:

```powershell
cd C:\Users\lenovo\Desktop\DealFlow360\backend
& .venv\Scripts\python.exe scripts/seed_200_data.py
```

### B. Reset 200 Synthetic Dataset
Safely wipes records belonging strictly to `bulk-data-lab`:

```powershell
cd C:\Users\lenovo\Desktop\DealFlow360\backend
& .venv\Scripts\python.exe -c "import asyncio; from app.seed.seeder_200 import reset_200_data; asyncio.run(reset_200_data())"
```

---

## 4. Verification & Testing

Run the dedicated test suite:

```powershell
cd C:\Users\lenovo\Desktop\DealFlow360\backend
& .venv\Scripts\pytest.exe tests/test_seed_200_data.py
```

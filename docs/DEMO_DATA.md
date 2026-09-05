# DealFlow360 — Phase 78: Demo Data Reference Manual

## 1. Quick Start Guide

### 1.1 Seeding Demo Environment
To populate a fresh demo environment with complete master data, product hierarchy, stock levels, and 10 end-to-end showcase scenarios:
```bash
cd backend
.venv\Scripts\python scripts\seed_demo_data.py
```

### 1.2 Resetting Demo Data
To completely purge demo tenant data while guaranteeing zero residual records:
```bash
cd backend
.venv\Scripts\python scripts\reset_demo_data.py
```

---

## 2. Multi-Tenant Architecture & Data Isolation

DealFlow360 provisions two isolated organizations during seeding:

1. **DealFlow360 Demo Enterprise (`demo-enterprise`)**:
   - Primary presentation tenant containing all master records, catalog items, pricing rules, stock distributions, and 10 scenario lifecycles.
2. **Acme Global Holding (`acme-global`)**:
   - Isolation validation tenant confirming zero cross-tenant data leakage across all repository queries and REST APIs.

---

## 3. Demo Persona Matrix

| Persona | Name | Email | Role | Password |
|---|---|---|---|---|
| Administrator | System Admin | `admin@dealflow.demo` | Organization Admin | `Password123!` |
| Sales Executive | Alex Rivera | `sales@dealflow.demo` | Sales / CPQ | `Password123!` |
| Purchasing Agent | Morgan Chen | `purchase@dealflow.demo` | Procurement | `Password123!` |
| Manufacturing Supervisor | David Miller | `manufacturing@dealflow.demo` | Production | `Password123!` |
| Inventory Manager | Sam Taylor | `inventory@dealflow.demo` | Warehouse / Logistics | `Password123!` |
| Business Owner | Elena Rostova | `owner@dealflow.demo` | Executive Approver | `Password123!` |
| Portal Buyer | Sarah Jenkins | `sarah.jenkins@acmecorp.com` | Customer Contact | `Password123!` |

---

## 4. Product Catalog & Inventory Distribution

| SKU | Product Name | Category | Unit Price | Unit Cost | Stock Locations |
|---|---|---|---|---|---|
| `DESK-EXE-001` | Ergonomic Executive Desk | Finished Good | $1,000.00 | $450.00 | Central (18), East (12), West (10) |
| `CHAIR-TS-001` | Task Chair Pro | Finished Good | $400.00 | $180.00 | Central (35), East (20), West (25) |
| `POD-MTG-001` | Acoustic Meeting Pod | Finished Good | $1,400.00 | $650.00 | Central (7), East (5), West (4) |
| `CONF-TBL-001` | Executive Conference Table | Finished Good | $3,500.00 | $1,600.00 | Central (4), East (3), West (2) |
| `BOM-STEEL-001` | Heavy-Duty Steel Pod Frame | Raw Component | $250.00 | $120.00 | Central (10), East (0), West (0) |
| `BOM-PANEL-001` | Soundproof Acoustic Panel | Raw Component | $80.00 | $35.00 | Central (32), East (0), West (0) |
| `BOM-OAK-001` | Solid Oak Desktop Slab | Raw Component | $150.00 | $70.00 | Central (20), East (0), West (0) |
| `BOM-FOAM-001` | High-Density Cushion Foam | Raw Component | $30.00 | $12.00 | Central (40), East (0), West (0) |
| `SRV-SWR-001` | Workspace Monitoring Suite | SaaS / Service | $1,200.00 | $0.00 | N/A (Subscription) |

---

## 5. Automated Verification
To verify the demo data environment programmatically:
```bash
cd backend
.venv\Scripts\pytest tests\test_phase_78_demo_data.py -v
```

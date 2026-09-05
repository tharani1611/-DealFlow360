# Phase 23–25 — Commercial Governance Subsystem Documentation

## 1. Overview

The **Commercial Governance Subsystem** integrates three essential commercial control pillars for DealFlow360:
1. **Phase 23 — Discount Governance Engine**: Policy-based max discount limits, floor unit prices, and target minimum margin rules with scope precedence.
2. **Phase 24 — Blended Discount Risk Engine**: Multi-item revenue-weighted discount calculation and deterministic 0–100 risk scoring with classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
3. **Phase 25 — Approval Rule Engine**: Rule-based authorization triggering, multi-role approval workflow (`PENDING`, `APPROVED`, `REJECTED`, `INVALIDATED`), and server-side state machine integration blocking unapproved `SENT` transitions.

---

# 2. Architectural Pipeline

Every commercial evaluation follows this strict linear calculation and governance pipeline:

```text
Quotation Data (Items, Discounts, Customer)
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│ Phase 20: Pricing Engine (Base Price + Specific Rules) │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 21: Real-time Margin Engine (COGS vs Net Price)  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 23: Discount Governance (Policy Precedence)     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 24: Blended Discount Risk Engine (0-100 Score)   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 25: Approval Rule Engine (Matching & Invalidation)│
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 22: State Machine (Block SENT if blocked)        │
└────────────────────────────────────────────────────────┘
```

---

# 3. Key Concepts & Business Math

### 3.1 Blended Discount Formula (Phase 24)
Blended discount is calculated across all line items on a revenue-weighted basis:

$$\text{Blended Discount \%} = \frac{\text{Total Discount Amount}}{\text{Total Revenue} + \text{Total Discount Amount}} \times 100$$

### 3.2 Discount Policy Precedence (Phase 23)
When evaluating discount governance, applicable policies are ordered by:
1. **Scope Precedence**: `user` > `customer` > `product` > `role` > `organization`
2. **Priority**: Lower integer priority numbers take higher precedence (e.g. `P1` > `P100`).

### 3.3 Risk Factor & Score Calculation (Phase 24)
- **Base Risk Score**: 0
- **Policy Violations**: +35 points
- **Negative Margin Detected**: +45 points
- **Low Overall Margin (< 10%)**: +20 points
- **High Blended Discount (> 25%)**: +25 points
- **Critical Risk Threshold**: Score $\ge 70$ or negative margin $\rightarrow$ `CRITICAL`
- **High Risk Threshold**: Score $\ge 50 \rightarrow$ `HIGH`
- **Medium Risk Threshold**: Score $\ge 25 \rightarrow$ `MEDIUM`
- **Low Risk Threshold**: Score $< 25 \rightarrow$ `LOW`

### 3.4 Approval Invalidation & State Machine Enforcement (Phase 25)
- **Automatic Invalidation**: If any commercial field (`unit_price`, `discount_amount`, `discount_percent`, `quantity`, or `customer_id`) is edited on a quotation in `DRAFT` or `REVISED` state, any existing `APPROVED` decision is automatically set to `INVALIDATED`.
- **State Machine Guard**: The quotation state machine (`transition_quotation`) explicitly blocks transition to `SENT` if approval is `PENDING`, `REJECTED`, or `INVALIDATED`.

---

# 4. Data Models & Database Migrations

- **Alembic Migration**: `000000000010_add_commercial_governance.py`
- **Tables Added**:
  - `discount_policies`: Policy configuration (`scope`, `max_discount_percent`, `min_unit_price`, `min_margin_percent`).
  - `approval_rules`: Rules defining triggers (`min_discount_percent`, `min_margin_percent`, `risk_level`, `required_role`).
  - `quotation_approvals`: History of approval requests, state (`PENDING`, `APPROVED`, `REJECTED`, `INVALIDATED`), and audit details.

---

# 5. API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/discount-governance/policies` | List all active discount policies |
| `POST` | `/api/v1/discount-governance/policies` | Create a discount policy |
| `POST` | `/api/v1/discount-governance/evaluate` | Evaluate quotation items against governance policies |
| `POST` | `/api/v1/discount-risk/evaluate` | Calculate blended discount & risk score |
| `GET` | `/api/v1/approvals/rules` | List approval rules |
| `POST` | `/api/v1/approvals/rules` | Create approval rule |
| `POST` | `/api/v1/approvals/decisions` | Submit approval or rejection decision |
| `POST` | `/api/v1/approvals/reevaluate/{quotation_id}` | Manually trigger approval re-evaluation |
| `GET` | `/api/v1/quotations/{id}/governance` | Fetch comprehensive Commercial Governance summary for a quotation |

---

# 6. Frontend UI Integration

1. **Commercial Governance Page (`/governance`)**: Admin interface for creating, viewing, and deleting discount policies and approval rules.
2. **Quotation Detail Page Commercial Card**: Real-time summary displaying Blended Discount %, Overall Margin %, Risk Score & Badge (`LOW` / `MEDIUM` / `HIGH` / `CRITICAL`), Policy Violations, and Approval Decision Workflow (`Approve`, `Reject`).
3. **Action Button Guards**: `Send Quotation` button is visually disabled with feedback when approval is `PENDING`, `REJECTED`, or `INVALIDATED`.

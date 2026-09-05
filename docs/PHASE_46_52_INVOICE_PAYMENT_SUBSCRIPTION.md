# Phases 46–52: Invoice, Payment & Subscription Lifecycle Engine

## Executive Overview

Phases 46–52 implement the complete commercial financial lifecycle in **DealFlow360**, bridging commercial negotiations and accepted quotations with real-time billing, payments, subscription management, proration math, and credit adjustments.

```text
Quotation (Accepted)
   ├── One-Time Items   ──> Phase 46: Invoice Engine
   └── Recurring Items  ──> Phase 48: Subscription Engine
                                 │
                                 ├── Phase 49: Billing Schedule Engine
                                 │      └── Scheduled / Due Invoices
                                 ├── Phase 50: Subscription Proration Math
                                 ├── Phase 51: Subscription Cancellation Engine
                                 │
 Phase 46: Invoice Engine <──────┘
   │
   ├── Phase 47: Payment Recording Engine (Partial & Full Balance Payments)
   └── Phase 52: Partial Refund & Credit Note Engine
```

---

## Technical Architecture & Database Schema

### Database Migration
Alembic migration: `000000000014_add_invoice_payment_subscription_credit.py`

### Data Models & Relationships

1. **`Invoice` (`invoices`)**
   - Represents a commercial billing document.
   - Enforces `uq_invoices_org_invoice_number` (`organization_id`, `invoice_number`).
   - Fields: `subtotal`, `discount_total`, `tax_total`, `total`, `amount_paid`, `amount_due`, `status` (`DRAFT`, `ISSUED`, `PARTIALLY_PAID`, `PAID`, `OVERDUE`, `VOID`).

2. **`InvoiceItem` (`invoice_items`)**
   - Line items with `billing_type` (`ONE_TIME`, `RECURRING`), `quantity`, `unit_price`, `discount_amount`, `tax_amount`, `line_subtotal`, `line_total`.

3. **`Payment` (`payments`)**
   - Ledger of payments against an invoice.
   - Enforces `uq_payments_org_payment_number`.
   - Payment methods: `CREDIT_CARD`, `BANK_TRANSFER`, `CHECK`, `ACH`, `CASH`.

4. **`Subscription` (`subscriptions`)**
   - Recurring commercial contract.
   - Enforces `uq_subscriptions_org_sub_number`.
   - Statuses: `TRIAL`, `ACTIVE`, `PAUSED`, `CANCELLED`, `EXPIRED`.
   - Billing Intervals: `MONTHLY`, `QUARTERLY`, `YEARLY`.

5. **`BillingSchedule` (`billing_schedules`)**
   - Period-by-period billing dates and status tracking (`SCHEDULED`, `DUE`, `INVOICED`, `PAID`, `SKIPPED`, `CANCELLED`).

6. **`SubscriptionProration` (`subscription_prorations`)**
   - Audit ledger for mid-cycle quantity or price adjustments with exact day-based math.

7. **`SubscriptionCancellation` (`subscription_cancellations`)**
   - Cancellation audit history (`IMMEDIATE` vs `END_OF_PERIOD`).

8. **`CreditNote` (`credit_notes`)** & **`CreditNoteItem` (`credit_note_items`)**
   - Partial or full credit notes issued against an invoice.

9. **`PaymentRefund` (`payment_refunds`)**
   - Partial or full refunds issued against a recorded payment.

---

## Deterministic Financial Math Rules

- **Zero Floating Point Arithmetic**: All monetary quantities use Python `Decimal` with `Numeric(12, 2)` database precision.
- **Server-Side Mutation Control**: All financial totals (`subtotal`, `tax_total`, `discount_total`, `total`, `amount_due`, `amount_paid`, `prorated_amount`) are computed strictly by deterministic Python backend service routines.
- **Proration Formula**:
  $$\text{Days in Period} = \text{End Date} - \text{Start Date}$$
  $$\text{Remaining Days} = \text{End Date} - \text{Effective Date}$$
  $$\text{Unused Credit} = \left(\frac{\text{Old Qty} \times \text{Old Price}}{\text{Days in Period}}\right) \times \text{Remaining Days}$$
  $$\text{New Charge} = \left(\frac{\text{New Qty} \times \text{New Price}}{\text{Days in Period}}\right) \times \text{Remaining Days}$$
  $$\text{Net Prorated Adjustment} = \text{New Charge} - \text{Unused Credit}$$

---

## API Endpoints Reference

### Invoices (`/api/v1/invoices`)
- `POST /` - Create manual invoice
- `POST /from-quotation/{quotation_id}` - Convert accepted quotation items to invoice
- `GET /` - List tenant invoices (optional `customer_id` filter)
- `GET /{id}` - Get invoice detail with line items
- `POST /{id}/issue` - Transition status from `DRAFT` to `ISSUED`
- `POST /{id}/void` - Void an unpaid invoice

### Payments (`/api/v1/payments`)
- `POST /` - Record payment against an invoice (updates `amount_paid`, `amount_due`, and status)
- `GET /invoice/{invoice_id}` - List payments for invoice

### Subscriptions (`/api/v1/subscriptions`)
- `POST /` - Create subscription
- `POST /from-quotation/{quotation_id}` - Auto-generate recurring subscriptions from quotation
- `GET /` - List subscriptions
- `GET /{id}` - Get subscription details with schedules
- `PUT /{id}/status` - Update status (`ACTIVE`, `PAUSED`, etc.)
- `GET /{id}/schedules` - List recurring billing schedules
- `POST /schedules/generate-due` - Idempotently generate due schedules
- `POST /schedules/{schedule_id}/execute-invoice` - Generate draft invoice for a due schedule
- `POST /{id}/proration/calculate` - Preview mid-cycle proration math
- `POST /{id}/proration/apply` - Apply mid-cycle proration adjustment
- `POST /{id}/cancel` - Cancel subscription (`IMMEDIATE` or `END_OF_PERIOD`)

### Credit Notes & Refunds (`/api/v1/credit-notes`)
- `POST /` - Issue credit note against an invoice
- `GET /{id}` - Get credit note detail
- `GET /invoice/{invoice_id}` - List credit notes for invoice
- `POST /refunds` - Process partial/full payment refund
- `GET /refunds/payment/{payment_id}` - List refunds for payment

---

## Verification & Test Suite

- Backend test suite: `tests/test_phases_46_52_invoice_payment_subscription.py` (6 comprehensive test suites covering all 7 phases).
- Multi-tenant isolation verified across all endpoints (`organization_id` boundary enforcement).

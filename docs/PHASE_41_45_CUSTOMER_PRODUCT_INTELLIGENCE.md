# DealFlow360 — Combined Phase 41–45: Customer + Product Intelligence Subsystem

## Executive Overview

The **Customer + Product Intelligence Subsystem** (Combined Phase 41–45) delivers an explainable, deterministic intelligence layer over authoritative CRM, deal, quotation, product, pricing, margin, and activity data.

It operates strictly as an advisory layer—calculating financial metrics with `Decimal` precision, scoring relationship health (0–100) with explicit positive and negative drivers, deriving customer segment and lifecycle classifications, tracking product market penetration, building empirical co-purchase product affinity matrices, and providing AI narrative explanations wrapped in `<UNTRUSTED_CRM_CONTEXT>` security boundaries.

---

## Subsystem Architecture & Phase Order

```text
PHASE 41 — Customer Intelligence Foundation
  • Consolidates Customer 360 facts across deals, quotations, products, and activities.
  • Computes Decimal financial metrics: total won revenue, open pipeline, weighted pipeline, quotation revenue, gross margin, margin %, and average deal value.
  • Classifies engagement recency: VERY_RECENT (<=7d), RECENT (<=14d), AGING (<=30d), STALE (<=60d), INACTIVE (>60d).

PHASE 42 — Customer Health + Segmentation Intelligence
  • Computes deterministic Customer Health Score (0–100).
  • Generates explicit positive_drivers and negative_drivers (risk factors).
  • Assigns health categories: HEALTHY, ENGAGED, ATTENTION, AT_RISK, INACTIVE.
  • Categorizes customer segments: ENTERPRISE, HIGH_VALUE, GROWTH, ACTIVE, DEVELOPING, AT_RISK, INACTIVE.
  • Classifies customer lifecycle stage: NEW, DEVELOPING, ACTIVE, GROWING, MATURE, AT_RISK, INACTIVE.
  • Evaluates revenue, deal, activity, pipeline, and engagement trend indicators.

PHASE 43 — Product Intelligence
  • Consolidates Product 360 performance: units quoted, units won, total revenue, gross margin, margin %, win rate %, average selling price.
  • Calculates customer penetration rate (% of active organization customers using product).
  • Computes product popularity score & rank across catalog inventory.

PHASE 44 — Recommendation + Cross-Sell Intelligence
  • Evaluates empirical co-purchase product affinity matrix (co_purchase_count, attachment_rate_percent, affinity_score).
  • Combines configured recommendation rules with observed co-purchase affinity data.
  • Generates upsell and cross-sell recommendations with confidence ratings (HIGH, MEDIUM, LOW) and empirical evidence.
  • Provides advisory AI explanations for product performance and cross-sell rationale.

PHASE 45 — Frontend Intelligence UI + System Integration
  • Neo Glass control panels and visualization components.
  • CustomerHealthCard component rendering health scores, badges, positive drivers, and risk factors.
  • ProductIntelligenceModal displaying Product 360 performance KPIs, margin %, customer penetration, affinity matrix, and AI advisory.
  • Integration into CustomerDetailPage and ProductsPage.
```

---

## API Endpoints

Registered under `/api/v1/intelligence`:

- `GET /api/v1/intelligence/customers/{customer_id}/360`
  - Returns `Customer360IntelligenceResponse` with financial KPIs, sales metrics, engagement recency, health score, positive/negative drivers, segment, lifecycle stage, trends, and AI executive commentary.
- `GET /api/v1/intelligence/products/{product_id}/360`
  - Returns `Product360IntelligenceResponse` with performance telemetry, gross margin %, win rate %, customer penetration %, popularity rank, co-purchase affinity matrix, and AI advisory commentary.
- `GET /api/v1/intelligence/customers/{customer_id}/product-recommendations`
  - Returns deterministic upsell & cross-sell recommendations based on rules and co-purchase affinity.
- `GET /api/v1/intelligence/customers/{customer_id}/health`
  - Returns engagement score and cooling detection reasons.

---

## Security, Governance & Financial Precision

1. **Decimal Precision**: Financial arithmetic (revenue, pipeline, gross margin, average deal value) uses `Decimal` values throughout backend services.
2. **Multi-Tenant Isolation**: All database queries enforce strict `organization_id` filtering server-side.
3. **Advisory AI Boundary**: AI functions exclusively as a read-only advisory layer. All context sent to AI models is wrapped in `<UNTRUSTED_CRM_CONTEXT>` boundary tags to prevent prompt injection. AI cannot mutate database records or bypass commercial governance.

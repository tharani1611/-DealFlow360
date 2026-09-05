# Phase 26–30 — AI Sales Intelligence & Sales Copilot Subsystem Documentation

## 1. Overview

The **AI Sales Intelligence & Sales Copilot Subsystem** turns DealFlow360 into an explainable, AI-assisted sales platform.
It integrates five logical capabilities:
1. **Phase 26 — Sales Intelligence Foundation**: Normalized structured facts collection (`sales_intelligence.py`).
2. **Phase 27 — Deal Intelligence**: Velocity signals, deal health scoring, commercial risk factors, and deal Q&A (`deal_intelligence.py`).
3. **Phase 28 — Customer Intelligence**: Customer 360 facts, cooling detection, and executive account briefing generation (`customer_intelligence.py`).
4. **Phase 29 — AI Sales Copilot**: Natural language sales assistant with intent routing (`PIPELINE`, `DEAL`, `CUSTOMER`, `QUOTATION`, `PRICING`, `MARGIN`, `DISCOUNT`, `APPROVAL`, `ACTIVITY`, `GENERAL_SALES`), evidence source transparency, hallucination controls, and read-only execution (`ai_sales_copilot.py`).
5. **Phase 30 — Intelligence Dashboard & Recommendations**: Integrated pipeline financial telemetry, deals at risk, cooling accounts, and recommendations (`intelligence.py`).

---

# 2. Architecture & Responsibility Isolation

```text
                  DETERMINISTIC ENGINES (Phases 18–25)
     (Pricing, Margins, Discount Governance, Risk Engine, Approvals, State Machine)
                                    │
                                    ▼
                     STRUCTURED INTELLIGENCE FACTS
                    (sales_intelligence.py — Phase 26)
                                    │
                                    ▼
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
Deal Intelligence            Customer Intelligence        Copilot Routing
 (Phase 27)                   (Phase 28)                   (Phase 29)
       │                            │                            │
       └────────────────────────────┼────────────────────────────┘
                                    ▼
                           AI SALES COPILOT & UI
```

### Critical Rules Enforced:
- **Sole Deterministic Authority**: AI never calculates prices, margins, discount policy limits, or approval decisions. All financial metrics originate from the backend deterministic services.
- **Server-Side API Key & Fallbacks**: `GEMINI_API_KEY` is kept server-side. If the AI service is disabled or unreachable, the system returns fallback responses populated with exact backend facts.
- **Strict Read-Only Execution**: The AI Sales Copilot cannot mutate database records or execute transactions directly.
- **Tenant Isolation**: Every context builder filters records strictly by `organization_id`.
- **Prompt Injection Defense**: Untrusted CRM text is isolated inside `<UNTRUSTED_CRM_CONTEXT>` XML boundary tags.

---

# 3. API Reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/copilot/chat` | Process natural language Sales Copilot inquiry with intent routing & evidence |
| `POST` | `/api/v1/copilot/deals/{deal_id}/qa` | Deal-level natural language Q&A |
| `GET` | `/api/v1/intelligence/dashboard` | Aggregate pipeline financial telemetry & attention metrics |
| `GET` | `/api/v1/intelligence/deals/{deal_id}/health` | Deterministic deal health score, risk factors, and AI explanation |
| `GET` | `/api/v1/intelligence/customers/{customer_id}/engagement` | Customer engagement score (0-100) and cooling detection |
| `GET` | `/api/v1/intelligence/customers/{customer_id}/briefing` | Executive Customer Meeting Briefing |

---

# 4. Verification Results

- **Backend Pytest Suite**: **171 / 171 PASSED**
- **Frontend Production Build**: **PASSED (0 TypeScript errors)**
- **Alembic Head**: `000000000010 (head)`

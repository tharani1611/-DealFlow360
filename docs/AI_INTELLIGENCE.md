# Phase 10 — AI Intelligence Architecture & Integration Guide

## 1. Executive Summary

Phase 10 introduces a **provider-independent, read-only AI Intelligence layer** into the DealFlow360 backend. Built to enhance CRM operational velocity, the AI module generates data-driven relationship summaries, deal risk assessments, next-best-action recommendations, activity engagement insights, and general CRM assistant responses.

Key design principles of Phase 10:
- **Provider Abstraction**: Decoupled from specific LLM APIs via `AbstractAIProvider`. Initial integration uses Google Gemini REST API (`GeminiAIProvider`), with a deterministic offline `MockAIProvider` for test suites and development environments.
- **Strict Read-Only Guarantee**: AI endpoints **never** mutate database state. All outputs are advisory and user-facing.
- **Tenant Isolation**: Multi-tenant database boundary enforcement ensures cross-tenant data requests return `404 Not Found`.
- **Prompt Injection Defense**: Untrusted CRM data is automatically wrapped in `<UNTRUSTED_CRM_CONTEXT>` security tags with strict system instructions instructing the model to treat context solely as data.
- **Data Minimization**: Password hashes, JWT tokens, secrets, and internal fields are scrubbed prior to building context dictionaries.

---

## 2. Configuration (`app/core/config.py`)

The AI module is configured via application settings:

| Setting Key | Default Value | Description |
| :--- | :--- | :--- |
| `AI_ENABLED` | `True` | Master toggle to enable/disable AI endpoints. When `False`, endpoints return `503 Service Unavailable`. |
| `AI_PROVIDER` | `"mock"` / `"gemini"` | Active provider choice (`"gemini"` or `"mock"`). |
| `GEMINI_API_KEY` | `""` | Google Gemini REST API key. |
| `GEMINI_MODEL` | `"gemini-1.5-flash"` | Gemini model identifier. |
| `AI_MAX_OUTPUT_TOKENS` | `1024` | Maximum token limit for AI completions. |
| `AI_TEMPERATURE` | `0.2` | Sampling temperature for completion stability. |
| `AI_TIMEOUT_SECONDS` | `30` | Timeout threshold for outbound HTTP requests. |

---

## 3. Architecture & Key Components

```
                +----------------------------+
                |  FastAPI Router           |
                |  /api/v1/ai/*              |
                +-------------+--------------+
                              |
                              v
                +----------------------------+
                |  AIService Orchestrator    |
                +------+--------------+------+
                       |              |
                       v              v
     +-------------------+          +-------------------+
     | AIContextBuilder  |          | Prompts & Safety  |
     | (Tenant Scoped)   |          | Defense Boundaries|
     +-------------------+          +-------------------+
                       \              /
                        v            v
                 +--------------------------+
                 |   AbstractAIProvider     |
                 +------------+-------------+
                              |
                     +--------+--------+
                     |                 |
                     v                 v
           +------------------+  +-------------------+
           | GeminiAIProvider |  | MockAIProvider    |
           | (REST Async HTTP)|  | (Offline Testing) |
           +------------------+  +-------------------+
```

---

## 4. API Endpoints

All AI endpoints reside under `/api/v1/ai` and require JWT user authentication.

### 1) `POST /api/v1/ai/customers/{customer_id}/summary`
- **Purpose**: Generates relationship summary, key insights, and health score estimate (`good`, `neutral`, `at_risk`).
- **Access**: Customer must belong to user's active organization (returns `404 Not Found` otherwise).

### 2) `POST /api/v1/ai/deals/{deal_id}/analysis`
- **Purpose**: Analyzes deal risk level (`low`, `medium`, `high`), positive signals, identified risks, and recommended actions.
- **Access**: Tenant-scoped.

### 3) `POST /api/v1/ai/deals/{deal_id}/next-action`
- **Purpose**: Recommends next best CRM action (`task`, `call`, `meeting`, `follow_up`), priority, title, and reasoning.
- **Access**: Tenant-scoped.

### 4) `POST /api/v1/ai/deals/{deal_id}/activity-insights`
- **Purpose**: Evaluates deal activity engagement, overdue tasks, upcoming follow-ups, and engagement velocity.
- **Access**: Tenant-scoped.

### 5) `POST /api/v1/ai/assistant`
- **Payload**: `{"question": "Which deals require urgent follow-up?"}`
- **Purpose**: Answers natural language user queries using tenant-scoped CRM context summary.
- **Access**: Tenant-scoped.

---

## 6. Security & Verification Summary

1. **Prompt Injection Defense**: Verified against malicious prompt overrides embedded in customer names or deal titles.
2. **Tenant Isolation**: Verified with multi-tenant tests returning `404 Not Found` for cross-tenant access attempts.
3. **Database Immutability**: Verified zero mutations to deals, customers, or activities after AI evaluation.
4. **Regression Suite**: 100% pass rate across 111 tests in the backend suite.

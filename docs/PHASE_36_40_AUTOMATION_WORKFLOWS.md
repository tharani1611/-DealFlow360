# DealFlow360 — Combined Phase 36–40: Commercial Automation & Workflows Engine

## Overview

The **Commercial Automation & Workflows Subsystem** (Combined Phase 36–40) introduces high-reliability, multi-tenant, event-driven commercial automation into DealFlow360. It automatically evaluates business triggers, applies deterministic typed condition rules, and executes targeted workflow actions—all while respecting commercial governance (pricing, margin, and approval state machines).

---

## Internal Architectural Phases

1. **Phase 36 — Automation Foundation**: Database models (`AutomationRule`, `AutomationExecution`, `AutomationExecutionAction`), Pydantic schemas, and multi-tenant security architecture.
2. **Phase 37 — Trigger & Condition Engine**: Event dispatcher (`DEAL_CREATED`, `DEAL_STAGE_CHANGED`, `QUOTATION_CREATED`, `QUOTATION_STATUS_CHANGED`, `CUSTOMER_CREATED`), field resolver, and deterministic boolean/comparison condition evaluator (supports AND/OR nesting, zero dynamic execution/eval).
3. **Phase 38 — Workflow Action Execution**: Action engine executing typed handlers:
   - `CREATE_ACTIVITY` / `CREATE_TASK`
   - `ASSIGN_DEAL` / `ASSIGN_CUSTOMER`
   - `ADD_NOTE`
   - `SEND_NOTIFICATION`
   - `UPDATE_DEAL_FIELD` / `UPDATE_CUSTOMER_FIELD`
4. **Phase 39 — Reliability, Scheduling & Execution History**: Idempotency hashing (`SHA256(org_id + rule_id + event_type + entity_id + event_id)`), bounded retries ($\le 3$), status tracking (`SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`), and tenant-isolated execution history logs.
5. **Phase 40 — Automation UI & System Integration**: Neo Glass control panel (`AutomationsPage.tsx`), rule modal (`AutomationRuleModal.tsx`), audit trace modal (`ExecutionDetailModal.tsx`), and AI Rule Recommendation Engine.

---

## Database Architecture

### Migration
- File: `backend/migrations/versions/000000000011_add_automation_and_workflow_engine.py`
- Revision ID: `000000000011`

### Tables
- `automation_rules`: Rules with trigger type, status (`ACTIVE`, `PAUSED`, `DRAFT`, `ARCHIVED`), priority, condition JSON, and action JSON.
- `automation_executions`: Audit trail of workflow runs with idempotency key, matched condition flag, succeeded/total action counts, error logs, and retry counters.
- `automation_execution_actions`: Granular record per action step executed within a workflow run.

---

## API Endpoints

Registered at `/api/v1/automations`:

- `GET /api/v1/automations/rules` — List tenant automation rules (optional `status` filter).
- `POST /api/v1/automations/rules` — Create new automation rule.
- `GET /api/v1/automations/rules/{rule_id}` — Get rule details.
- `PUT /api/v1/automations/rules/{rule_id}` — Update automation rule.
- `DELETE /api/v1/automations/rules/{rule_id}` — Delete automation rule.
- `POST /api/v1/automations/rules/{rule_id}/activate` — Activate rule.
- `POST /api/v1/automations/rules/{rule_id}/pause` — Pause rule.
- `GET /api/v1/automations/executions` — List workflow execution audit history.
- `POST /api/v1/automations/executions/{execution_id}/retry` — Re-trigger failed workflow execution (up to 3 retries).
- `GET /api/v1/automations/analytics/summary` — Execution KPI telemetry.
- `POST /api/v1/automations/ai-recommendations` — Generate AI automation recommendations based on CRM pattern analysis.

---

## UI Components

- `AutomationsPage.tsx` (`/automations`): Rules management tab, execution audit log tab, KPI cards, and AI recommendation cards.
- `AutomationRuleModal.tsx`: Visual rule builder for triggers, logical AND/OR conditions, and action step configuration.
- `ExecutionDetailModal.tsx`: Step-by-step audit trace of workflow executions with retry capability.

---

## Commercial Governance & Security

1. **Governance Protection**: Automation actions cannot bypass pricing engines, margin thresholds, or approval state machines.
2. **Multi-Tenant Isolation**: All DB queries, trigger processing, and execution logs filter strictly by `organization_id`.
3. **Determinism & Safety**: Condition evaluations use explicit typed comparisons (no `eval()` or code execution).

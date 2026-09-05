# DealFlow360 — Intelligent Sales Operations & CRM Platform

## Overview
**DealFlow360** is an enterprise-grade sales operations and CRM platform built with a modular-monolith backend and a distinctive **Neo Glass** (Glassmorphism + Neo-Brutalism) user interface.

The platform governs the commercial quotation-to-deal lifecycle: customer relationship management, contact management, commercial product catalog management, itemized quotation state machines, Kanban sales pipeline management, CRM activity workflows, and read-only AI deal intelligence.

---

## Architectural Stack
* **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.x Async (asyncpg), PostgreSQL, Alembic, Pydantic v2, JWT, bcrypt, Pytest.
* **Frontend**: React 18, TypeScript, Vite, React Router DOM v6, Tailwind CSS, Lucide React icons.
* **Design System**: **Neo Glass UI** (Glassmorphism + Neo-Brutalism).
* **AI Layer**: Provider-independent AI abstraction (`AbstractAIProvider`) with Google Gemini REST API integration (`GeminiAIProvider`), deterministic offline testing mock (`MockAIProvider`), prompt injection defense, and tenant-isolated context.

---

## Repository Structure
```text
DealFlow360/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI Application Entry & Router Mount
│   │   ├── core/                    # Config, Security, DB Engine, Exceptions
│   │   ├── models/                  # SQLAlchemy 2.x Async Models
│   │   ├── schemas/                 # Pydantic v2 Validation Schemas
│   │   ├── services/                # Business Domain Logic Services
│   │   ├── ai/                      # AI Provider Abstractions & Prompts
│   │   └── api/v1/                  # FastAPI Endpoints (/auth, /customers, /deals, /ai, etc.)
│   ├── migrations/                  # Alembic Async Migrations (000000000004 head)
│   ├── tests/                       # Pytest Test Suite
│   ├── alembic.ini
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/                     # React Entry & Provider Setup
│   │   ├── context/                 # AuthContext & ToastContext
│   │   ├── services/                # API Client Modules (authApi, customerApi, dealApi, aiApi, etc.)
│   │   ├── components/ui/           # Neo Glass UI Primitives (GlassCard, BrutalButton, KanbanBoard, etc.)
│   │   ├── layouts/                 # MainLayout App Shell & Topbar
│   │   ├── pages/                   # Application Page Views
│   │   └── routes/                  # Protected AppRoutes
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── .env.example
│
├── docs/                            # Architecture & AI Integration Specifications
│   ├── AI_INTELLIGENCE.md
│   └── ...
├── .gitignore
└── README.md
```

---

## Development Setup Instructions

### 1. Backend Setup
1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Activate Python virtual environment:
   ```bash
   .venv\Scripts\activate  # Windows
   ```
3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```
4. Run Alembic database migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   * Health Check: `http://127.0.0.1:8000/api/v1/health`
   * OpenAPI Specs: `http://127.0.0.1:8000/api/v1/docs`

6. Run the Pytest regression suite:
   ```bash
   pytest tests
   ```

### 2. Frontend Setup
1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Copy environment configuration:
   ```bash
   cp .env.example .env.local
   ```
4. Start the Vite dev server:
   ```bash
   npm run dev
   ```
5. Execute production build check:
   ```bash
   npm run build
   ```

### 3. Demo Data Seeding
To populate realistic synthetic enterprise telemetry for live demonstration:
```bash
cd backend
python -m app.seed.demo
```
*Creates synthetic demo organization (`demo-org`) and user (`demo@dealflow360.com` / `Demo123!`) with multi-stage deals, health metrics, and activity timelines.*

---

## User Journey & Navigation
```text
LOGIN ➔ DASHBOARD ➔ CUSTOMERS ➔ CUSTOMER DETAILS ➔ CONTACTS ➔ PRODUCTS ➔ QUOTATIONS ➔ DEALS (KANBAN) ➔ DEAL DETAILS ➔ ACTIVITIES ➔ AI INTELLIGENCE ➔ SETTINGS
```

---

## Documentation Links
* [Demo Script Walkthrough](docs/DEMO_SCRIPT.md)
* [Product Story & Value Proposition](docs/PRODUCT_STORY.md)

---

## Completed Phases
- [x] **Phase 4**: Database Foundation & Alembic Migrations
- [x] **Phase 5**: Core Data Models (Organization, User, Customer, Contact, Product)
- [x] **Phase 6**: Security Architecture, JWT Authentication & Multi-Tenant RBAC
- [x] **Phase 7**: Customer, Contact, Product & Quotation APIs
- [x] **Phase 8**: Deals & Sales Pipeline Kanban
- [x] **Phase 9**: Activities & Workflow Timelines
- [x] **Phase 10**: AI Intelligence Layer
- [x] **Phase 11**: Frontend Foundation & Neo Glass UI Primitives
- [x] **Phase 12**: Neo Glass UI/UX Polish & Experience Refinement
- [x] **Phase 13**: Full End-to-End Integration QA & Demo Readiness
- [x] **Phase 14**: Advanced CRM Intelligence + Competitive Differentiation
- [x] **Phase 15**: Sales Productivity & Executive Intelligence Platform
- [x] **Phase 16**: Final Product Excellence, Security & Hackathon Showcase Readiness

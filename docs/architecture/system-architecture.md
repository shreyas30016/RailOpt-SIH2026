# RailOpt System Architecture

## Overview
RailOpt (SIH 2026 · Problem Statement SIH26027) is an AI-powered, deterministic railway maintenance block planning and decision-support system tailored for Indian Railways operations.

The system bridges maintenance engineering demands (Civil/Engineering, Electrical/TRD, Signalling & Telecom/S&T) with train traffic operations, resolving multi-objective scheduling conflicts through mathematical optimization and conversational AI explanations.

---

## High-Level Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │               CLIENT LAYER                   │
                    │   Tailwind CSS · ES Modules · Stitch UI      │
                    │   Vercel Edge Host (Static Assets)           │
                    └──────────────────────┬───────────────────────┘
                                           │ HTTPS (Configurable Base URL)
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │             API GATEWAY & CORE               │
                    │   FastAPI · ASGI · Dynamic CORS              │
                    │   Token-Based RBAC & Anti-Spoofing           │
                    └──────────────┬───────────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   OPTIMIZATION   │     │    AI COPILOT    │     │   DATA ACCESS    │
│  Google OR-Tools │     │ DeepSeek / NIM   │     │ SQLAlchemy ORM   │
│  CP-SAT Engine   │     │ Function Calling │     │ SQLite / Postgres│
│  Decision Trees  │     │ Safety Filter    │     │ Pydantic Schemas │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

---

## Core System Components

### 1. Presentation Layer (`frontend/`)
- **Hosting**: Static web host (Vercel Edge).
- **Technology**: Native HTML5, ES Modules (`frontend/js/`), Tailwind CSS (CDN), Google Fonts.
- **Routing**: Clean client-side SPA route rewrites configured via `vercel.json`.
- **Runtime Decoupling**: Uses `frontend/js/config.js` to resolve `API_BASE_URL` dynamically from browser globals, meta tags, or `localStorage` overrides, preventing hardcoded production domains.
- **Views**:
  - `login.html`: Role-based persona launcher (Controller, Planner, Engineer, TRD, S&T).
  - `dashboard.html`: Operations KPI cards, corridor status, active train list, quick actions.
  - `maintenance_requests.html`: Multi-departmental maintenance request submission and tracking.
  - `block_planning.html`: Mathematical solver controls, plan generation, and quality scorecards.
  - `gantt_view.html`: 24-hour interactive multi-track corridor Gantt visualization.
  - `what_if.html`: Visual schedule diffs for train delay, section blockage, and emergency injections.
  - `constraints_logic.html`: Mathematical constraint audit and safety verification.
  - `reports.html`: Historical trend analytics and maintenance utilization reports.

### 2. Backend & Application Layer (`backend/app/`)
- **Framework**: FastAPI (Python 3.10+).
- **Configuration**: Pydantic BaseSettings in `backend/app/config.py`.
- **RBAC Engine**: Enforces role division between Divisional Controllers (approvers), Planners (optimizers), and Field Officers (request creators).
- **Routers**:
  - `/api/auth`: Persona profiles and permission grants.
  - `/api/dashboard`: Aggregated operational metrics and department backlogs.
  - `/api/maintenance`: Maintenance job creation, status updates, and department filtering.
  - `/api/optimization`: CP-SAT block planning execution with objective weight tuning.
  - `/api/whatif`: Counterfactual scenario simulation with before/after visual diffs.
  - `/api/gantt`: Scheduled block timeline and train conflict feeds.
  - `/api/reports`: Aggregated analytical metrics and shadow block synergy audits.
  - `/api/trains`: Live corridor train positions, timetable replay, and simulated delay push.
  - `/api/ai`: Intent-classified conversational copilot with deterministic safety boundaries.

### 3. Optimization Layer (`backend/app/optimizer/`)
- **Engine**: Google OR-Tools CP-SAT (Constraint Programming - Satisfiability).
- **Safety Invariants (Hard Constraints)**:
  - Non-overlapping traffic blocks on the same track line.
  - Mandatory train headway buffers between maintenance blocks and scheduled movements.
  - Heavy machinery and tamping machine exclusivity across sections.
  - Strict containment of jobs within active, approved departmental `BlockWindow` intervals.
- **Multi-Objective Goal Programming**:
  - Minimization of passenger train delay penalties.
  - Maximization of shadow block synergies (co-locating S&T or TRD work within Engineering blocks).
  - Maximization of urgent and high-priority maintenance execution within budget.
- **Decision Explainer Tree**: Inspects CP-SAT solver state to generate human-readable justifications for block scheduling and deferrals.

### 4. AI Copilot Layer (`backend/app/ai/`)
- **Architecture**: Provider-agnostic orchestration supporting DeepSeek V4 Flash via NVIDIA NIM with deterministic tool-grounded fallback.
- **Intent Classifier**: Maps natural language queries to discrete actions (`EXPLAIN`, `OPTIMIZE`, `WHAT_IF`, `QUERY`, `NAVIGATION`).
- **Safety Boundary Filter**: Prohibits unauthorized actions (e.g. bypassing safety headway, emergency un-block approvals by non-controllers).
- **Database Mutation Guard**: AI cannot directly modify database tables; all mutations must flow through validated domain APIs.

### 5. Persistence Layer (`backend/app/database.py`)
- **ORM**: SQLAlchemy 2.0.
- **Local / Demo**: SQLite (`railopt.db`).
- **Production**: Configurable via `DATABASE_URL` (supports PostgreSQL / Supabase / Neon).

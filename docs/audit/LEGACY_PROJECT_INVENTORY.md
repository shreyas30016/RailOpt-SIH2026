# RailOpt Legacy Project Inventory
**Repository:** `A:\SHREYAS\RAILWAY BLOCK AI`  
**Git Remote:** `https://github.com/shreyas30016/Railopt-SIH2026.git`  
**Audit Timestamp:** September 2026  
**Project Scope:** SIH 2026 Problem Statement SIH26027 — AI-Powered Automatic Block Planning System for Indian Railways

---

## 1. Directory Structure Overview

```text
A:\SHREYAS\RAILWAY BLOCK AI\
├── .env / .env.example          # Environment configuration (Database URL, Supabase, Solvers)
├── AGENTS.md                    # Project-level rules of truth & domain governance
├── PROJECT_RULES.md             # 23 operational rules for SIH26027
├── README.md                    # Project overview, launch instructions & architecture
├── api/
│   └── index.py                 # Vercel serverless entrypoint importing backend.app.main
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI REST API endpoint routers (8 files)
│   │   │   ├── auth.py          # Session authentication, roles & divisions
│   │   │   ├── dashboard.py     # Bento KPIs, live train feed, urgent queue
│   │   │   ├── gantt.py         # Gantt timeline blocks and train overlay paths
│   │   │   ├── maintenance.py   # Maintenance CRUD & duration prediction baseline
│   │   │   ├── optimization.py  # OR-Tools CP-SAT solver runner & decision explanation
│   │   │   ├── reports.py       # Operational report metrics & historical runs
│   │   │   ├── trains.py        # Live train movement adapter & delay simulation
│   │   │   └── whatif.py        # Dynamic disruption simulation router
│   │   ├── config.py            # Global application settings & SQLite/Supabase resolver
│   │   ├── data/
│   │   │   └── synthetic_seeder.py # Seed data for Delhi–Agra corridor (16 jobs, 6 trains, 6 windows)
│   │   ├── database.py          # SQLAlchemy SessionLocal, declarative Base & engine
│   │   ├── main.py              # FastAPI app initialization, CORS, static routes, lifespan
│   │   ├── models/
│   │   │   └── models.py        # SQLAlchemy database schema models (11 entities)
│   │   ├── optimizer/
│   │   │   ├── constraints.py   # Mathematical constraint definitions
│   │   │   ├── explainer.py     # Deterministic decision reasoning tree builder
│   │   │   ├── rules_loader.py  # YAML rules file parser & validator
│   │   │   ├── solver.py        # Google OR-Tools CP-SAT core mathematical solver
│   │   │   └── whatif.py        # What-If simulator executing differential CP-SAT runs
│   │   ├── schemas/
│   │   │   └── schemas.py       # Pydantic request/response models
│   │   └── services/
│   │       ├── duration_predictor.py # Baseline heuristic duration estimator
│   │       └── train_adapter.py      # Live train data provider with mock fallback
│   └── config/
│       └── railway_rules.yaml   # Declarative railway engineering rules & constraints
├── docs/                        # Specifications, QA audits, runtime logs
├── frontend/
│   ├── assets/                  # Official logos, design assets, and screenshots
│   ├── index.html               # Operations Dashboard (Alias entrypoint)
│   ├── dashboard.html           # Operations Dashboard (Primary)
│   ├── login.html               # Role & Division Sign-In Portal
│   ├── maintenance-requests.html# Multi-Department Backlog & Filtration Table
│   ├── block-planning.html      # CP-SAT Optimization Trigger & Plan Comparison
│   ├── gantt-view.html          # 24-Hour Corridor Gantt Timeline Visualization
│   ├── what-if.html             # Dynamic Scenario Simulation & Replanning
│   ├── constraints-logic.html   # Plan Logic, Hard/Soft Rules & Conflict Audits
│   ├── reports.html             # Operational Analytics, KPIs & CSV Export
│   └── js/
│       ├── app.js               # Main UI event orchestrator & page router
│       ├── appState.js          # Centralized reactive application state store
│       ├── mockData.js          # Client-side fallback datasets (jobs, trains, plans)
│       ├── types.js             # JSDoc type definitions & domain schemas
│       ├── components/          # Reusable DOM presentation components (8 files)
│       │   ├── conflictCard.js  # Solver deconfliction badge renderer
│       │   ├── ganttRow.js      # Gantt bar renderer
│       │   ├── jobRow.js        # Maintenance table row with Approve/Defer/Delete
│       │   ├── kpiCard.js       # Bento metric card component
│       │   ├── optimizationResultView.js # Scheduled blocks & Decision Audit Modal
│       │   ├── planRow.js       # Plan block row component
│       │   ├── trainStatusCard.js # Live corridor train movement tracker
│       │   └── whatIfScenarioView.js # Scenario summary view
│       └── services/
│           ├── dataService.js   # Client HTTP API layer with mock fallback
│           └── trainDataService.js # Dedicated train data client service
├── stitch_export/               # Google Stitch baseline design system & HTML templates
├── tests/                       # Automated pytest test suites (8 files)
├── backend_runner.bat           # Windows batch script for FastAPI runner
├── start.bat                    # One-click Windows full-stack launcher
├── start-frontend-only.bat      # Standalone frontend HTTP server launcher
├── stop.bat                     # Process termination utility for port 8000
└── requirements.txt             # Python backend dependencies
```

---

## 2. Component Inventory & Directory Descriptions

### A. Frontend Layer (`frontend/`)
- **`login.html` (592 lines):** Custom login screen providing Division selection (10 IR divisions) and Role selection (Controller, Planner, Engineer, TRD Officer, S&T Officer). Communicates with `/api/auth/login`.
- **`dashboard.html` / `index.html` (416 lines):** Operations Dashboard. Displays Bento KPIs, live train status feed, department request distribution donut chart, upcoming scheduled blocks, and solver deconfliction cards.
- **`maintenance-requests.html` (460 lines):** Track possession backlog table. Contains department filter tabs (All, Civil Eng, S&T, TRD, Mech), text search, section dropdown, urgency dropdown, dense table, and a static mockup detail sidebar.
- **`block-planning.html` (433 lines):** Block Planning screen. Houses the *"Run CP-SAT Optimization"* trigger, KPI comparison cards (AI Plan vs Manual baseline), scheduled blocks table, unscheduled jobs list, and mathematical rationale narrative.
- **`gantt-view.html` (416 lines):** 24-hour timeline Gantt view. Displays track lines (UP Main, DN Main, 3rd Line) across sections with train movement paths and maintenance block overlay.
- **`what-if.html` (466 lines):** Scenario simulator supporting Train Delays, Block Unavailability, Maintenance Overruns, and Emergency Rail Fractures with before-vs-after delta KPIs.
- **`constraints-logic.html` (448 lines):** Explanations of hard safety constraints, soft optimization objectives, and decision audit logs.
- **`reports.html` (484 lines):** Historical performance metrics, grant ratios, section efficiency list, and CSV export.
- **`frontend/js/app.js` (958 lines):** Primary frontend controller. Handles authentication checks, header population, profile/settings/notifications popovers, dynamic rendering, and event routing.
- **`frontend/js/appState.js` (102 lines):** Observable publish-subscribe state container.
- **`frontend/js/services/dataService.js` (463 lines):** API wrapper with graceful offline fallback to `mockData.js`.
- **`frontend/js/services/trainDataService.js` (172 lines):** Polls `/api/trains/live` and normalizes train status objects.

### B. Backend Layer (`backend/app/`)
- **`backend/app/main.py` (156 lines):** FastAPI application factory. Configures CORS, mounts routers on `/api` and `/api/v1`, serves static HTML files, and manages startup database seeding.
- **`backend/app/database.py` (27 lines):** SQLite / PostgreSQL engine binding and SessionLocal context manager.
- **`backend/app/config.py` (38 lines):** Application settings, database URL resolver, solver timeout parameter, and train API keys.
- **`backend/app/models/models.py` (187 lines):** 11 SQLAlchemy models mapping the complete railway maintenance domain.
- **`backend/app/schemas/schemas.py` (145 lines):** Pydantic validation models for maintenance jobs, optimization runs, and simulation inputs.

### C. Optimizer Layer (`backend/app/optimizer/`)
- **`solver.py` (620 lines):** Google OR-Tools CP-SAT solver implementation. Models maintenance jobs as interval variables, enforces non-overlap constraints against train paths, enforces station spacing buffers, pairs compatible shadow blocks (ENG + TRD + S&T), and optimizes an objective function minimizing train delay while maximizing block utilization.
- **`constraints.py` (155 lines):** Rule classes for Hard Constraints (Passenger conflict, track isolation, mandatory buffer) and Soft Objectives (Synergy, overdue priority, minimized disruption).
- **`explainer.py` (310 lines):** Generates structured decision trees explaining why each job was scheduled or deferred.
- **`whatif.py` (280 lines):** Evaluates disruptive scenario inputs against a baseline plan and re-solves constraints.
- **`rules_loader.py` (110 lines):** Loads domain rules from `backend/config/railway_rules.yaml`.

### D. Data & Services Layer (`backend/app/data/`, `backend/app/services/`)
- **`synthetic_seeder.py` (520 lines):** Generates demo data for the Delhi–Agra mainline corridor (6 sections: NDLS-TKD, TKD-FDB, FDB-PWL, PWL-KDS, KDS-MTJ, MTJ-AGC; 16 multi-department jobs; 6 train schedules; 6 block windows).
- **`train_adapter.py` (340 lines):** Live train adapter with simulated live GPS delays and automatic fallback.
- **`duration_predictor.py` (110 lines):** Deterministic baseline predictor for maintenance durations based on weather and resource availability.

### E. Test Suites (`tests/`)
- **`test_api.py` (3,333 bytes):** End-to-end FastAPI endpoint tests.
- **`test_optimizer.py` (1,889 bytes):** Solver execution, interval non-overlap, and shadow block synergy tests.
- **`test_train_adapter.py` (1,970 bytes):** Mock/live fallback and delay simulation tests.
- **`test_m2_integration.py` (9,352 bytes):** Milestone 2 full integration tests.
- **`test_deterministic_scenario.py` (12,324 bytes):** Deterministic seed scenario verification.
- **`test_stress_scenarios.py` (19,481 bytes):** Heavy corridor load and constraint boundary testing.
- **`test_serverless_compatibility.py` (4,134 bytes):** Vercel serverless /tmp database isolation test.
- **`test_dashboard_interactions.py` (3,135 bytes):** Client-server interaction tests.

---

## 3. Technology Stack Summary

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Web Framework** | FastAPI (Python 3.10+) | High-performance asynchronous REST API & Static file server |
| **Mathematical Solver** | Google OR-Tools CP-SAT | Deterministic constraint satisfaction & combinatorial optimization |
| **Database & ORM** | SQLAlchemy 2.0 / SQLite / PostgreSQL | Relational persistence of railway domain entities & solver runs |
| **Validation Layer** | Pydantic v2 | Request/response schema validation and serialisation |
| **Frontend Architecture** | Vanilla HTML5 / ES6 Modules / Tailwind CSS | High-density enterprise railway dashboard with zero heavy JS framework overhead |
| **Iconography & Fonts** | Google Material Symbols / Inter / JetBrains Mono | Official railway enterprise typography and symbolic indicators |

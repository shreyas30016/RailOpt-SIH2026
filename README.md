# RailOpt

**AI-Powered Automatic Railway Block Planning & Decision Support**  
*Smart India Hackathon 2026 · Problem Statement SIH26027*

[![CI](https://github.com/shreyas30016/Railopt-SIH2026/actions/workflows/tests.yml/badge.svg)](https://github.com/shreyas30016/Railopt-SIH2026/actions/workflows/tests.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![OR-Tools](https://img.shields.io/badge/Google%20OR--Tools-CP--SAT-4285F4.svg?logo=google&logoColor=white)](https://developers.google.com/optimization)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.x-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)

---

## 1. Problem
On Indian Railways' mixed-traffic corridors, maintenance blocks (Civil Engineering, Electrical TRD, and Signalling & Telecom) must be granted daily without crippling high-density passenger and freight operations. Currently, block planning involves manual coordination between multiple departmental field units and the section controller. This manual process frequently results in:
- High passenger train detention and cascading delay propagation.
- Missed opportunities for synchronized "shadow blocks" across departments on the same track section.
- Conflicts between machine availability (e.g. track tampers) and line vacancy.
- Operational friction when responding dynamically to unplanned train delays or emergency maintenance.

---

## 2. Solution
**RailOpt** is an intelligent, deterministic decision-support prototype that automates the generation, evaluation, explanation, and dynamic replanning of railway maintenance blocks.

By encoding railway safety regulations and operational guidelines into mathematical constraints, RailOpt searches combinatorial scheduling spaces using **Google OR-Tools CP-SAT** to deliver globally optimized block plans that minimize train delay while maximizing maintenance throughput.

---

## 3. Key Capabilities
- **Multi-Departmental Coordination**: Jointly schedules Engineering (Track), TRD (Overhead Catenary), and S&T (Signalling) jobs.
- **Automated Shadow Block Pairing**: Automatically identifies and co-locates electrical and signalling work within track maintenance blocks on the same line, saving corridor capacity.
- **Deterministic Mathematical Safety**: Hard safety constraints (headway buffer, non-overlap, machine exclusivity) are strictly enforced as mathematical invariants.
- **Interactive 24-Hour Corridor Gantt**: Rich visual timeline displaying bidirectional train paths, scheduled maintenance blocks, and potential conflict windows.
- **Dynamic What-If Simulation**: Instant counterfactual evaluation of train delays (+15/30/60 min), section blockages, maintenance overruns, and emergency job injections with visual before/after schedule diffs.
- **AI Operational Copilot**: Natural-language assistant powered by DeepSeek V4 Flash via NVIDIA NIM with intent classification, permission scoping, and deterministic safety filters.
- **Plan Quality Scorecard**: Quantitative comparison against an uncoordinated manual baseline across corridor throughput, shadow synergy, and delay penalty.

---

## 4. Architecture

RailOpt employs a modern, decoupled cloud architecture designed for scalability and reliability:

```
     ┌────────────────────────────────────────────────────────┐
     │                     Vercel Edge                        │
     │  Static Frontend (HTML5 / Vanilla ES Modules / CSS)    │
     │  Clean Route Rewrites (/dashboard, /planning, etc.)    │
     └───────────────────────────┬────────────────────────────┘
                                 │
                   HTTPS Request │ Dynamic API Base URL
                                 ▼
     ┌────────────────────────────────────────────────────────┐
     │             External Python Host (FastAPI)             │
     │      (Render / Railway / Fly.io / AWS ECS / EC2)       │
     │                                                        │
     │  - REST API Routers with Environment-Driven CORS       │
     │  - Server-Authoritative RBAC & Anti-Spoofing           │
     │  - Google OR-Tools CP-SAT Mathematical Solver          │
     │  - NVIDIA NIM / DeepSeek AI Copilot Provider           │
     │  - SQLAlchemy ORM (SQLite / PostgreSQL)                │
     └────────────────────────────────────────────────────────┘
```

For detailed architecture documentation, see:
- [System Architecture](docs/architecture/system-architecture.md)
- [Optimization Specification](docs/architecture/optimization-spec.md)
- [AI Copilot Architecture](docs/architecture/ai-architecture.md)

---

## 5. Technology Stack
- **Frontend**: HTML5, Vanilla JavaScript (ES6 Modules), Tailwind CSS, Google Stitch Design System.
- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2.
- **Optimization**: Google OR-Tools CP-SAT (Constraint Programming - Satisfiability).
- **AI & Copilot**: DeepSeek V4 Flash (`deepseek-ai/deepseek-v4-flash-0731`) hosted on NVIDIA NIM API.
- **Persistence**: SQLAlchemy 2.0 ORM, SQLite (Local/Demo), PostgreSQL (Production-ready).
- **Testing**: Pytest, AnyIO, FastAPI TestClient.

---

## 6. User Roles & RBAC Matrix
RailOpt enforces strict server-authoritative role-based access control across five operational personas:

| Role | Department | Can Request Jobs | Can Run Optimization | Can Approve Blocks | Operational Scope |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Section Controller** | Operating | ❌ | ✅ | ✅ | Full corridor authority, final block approval |
| **Block Planner** | Planning | ❌ | ✅ | ❌ | Optimization weight tuning, scenario simulation |
| **Civil Engineer** | Engineering | ✅ | ❌ | ❌ | Track maintenance requests (P-Way, Ballast) |
| **TRD Officer** | Electrical | ✅ | ❌ | ❌ | OHE catenary & power supply maintenance |
| **S&T Officer** | Signalling | ✅ | ❌ | ❌ | Point machines, interlocking, track circuits |

Detailed security specs: [docs/architecture/role-and-access-spec.md](docs/architecture/role-and-access-spec.md) and [docs/architecture/api-rbac-contract.md](docs/architecture/api-rbac-contract.md).

---

## 7. Optimization Engine (Google OR-Tools CP-SAT)
Rather than relying on heuristics or unconstrained LLM outputs, RailOpt models block scheduling as an exact mathematical constraint satisfaction and optimization problem (CP-SAT):
- **Decision Variables**: Start times, durations, track line assignments, and execution binary indicators for each requested job.
- **Objective Function**:
  $$\min \left( w_{\text{delay}} \cdot \sum \text{TrainDelay} - w_{\text{shadow}} \cdot \sum \text{ShadowSynergyHours} - w_{\text{urgent}} \cdot \sum \text{UrgentPriorityScheduled} \right)$$
- **Execution Budget**: Configurable solver time budget (5s–60s) with numerical bounds validation.

---

## 8. AI Operational Copilot
The embedded conversational AI assistant allows controllers and planners to query corridor state, request schedule explanations, and explore options naturally:
- **Provider-Agnostic Core**: Implemented with NVIDIA NIM DeepSeek V4 Flash integration.
- **Intent Routing**: Automatically categorizes queries into `EXPLAIN`, `OPTIMIZE`, `WHAT_IF`, `QUERY`, or `NAVIGATION`.
- **Deterministic Safety Filter**: Strict guardrails intercept and reject any prompt injection or hallucinated attempt to bypass railway safety rules or alter database records directly.

---

## 9. What-If Counterfactual Simulation
Operators can stress-test the corridor against four operational contingencies:
1. **Train Delay Injection**: Shift passenger train schedules by +15, +30, or +60 minutes to analyze downstream block conflicts.
2. **Section Blockage**: Mark specific tracks or sections as emergency unavailable (e.g. rail fracture or OHE breakdown).
3. **Maintenance Overrun**: Simulate job execution exceeding scheduled block duration.
4. **Emergency Job Injection**: Insert unplanned emergency repair requests into an active schedule.

The interface presents a visual side-by-side **Before vs After diff** showing displaced jobs, train delay deltas, and corridor throughput impact.

---

## 10. Railway Safety Invariants
RailOpt enforces non-negotiable hard railway safety constraints:
- **Headway Safety Buffer**: Mandatory operational buffer between scheduled train passages and maintenance blocks.
- **Track Line Exclusivity**: No conflicting traffic blocks simultaneously occupying the same track block section.
- **Machine Exclusivity**: Heavy track maintenance machinery (tampers, ballast regulators) cannot be scheduled in two locations at the same time.
- **BlockWindow Containment**: Jobs requiring traffic blocks are strictly constrained within active, approved sectional block windows.

---

## 11. Disclaimer: Simulated / Demo Data
> **IMPORTANT NOTICE**  
> All corridor layouts, track identifiers, train timetables, delays, and maintenance jobs in this repository are **SIMULATED / DEMO DATA** based on a representative Delhi–Agra corridor model (6 sections, 12 track lines, 30 passenger and freight trains).  
> RailOpt is an academic and hackathon prototype; it is **not connected to live internal Indian Railways systems (NTES, COA, FOIS)** and does not represent certified railway safety equipment.

---

## 12. Screenshots & Interface Overview

| View | Purpose |
| :--- | :--- |
| **Operations Dashboard** | Real-time corridor overview, active trains, backlog counts, quick actions |
| **Maintenance Backlog** | Multi-department job creation, department filtering, priority tagging |
| **Block Planning** | Solver weight tuning, execution budget control, plan quality scorecard |
| **Corridor Gantt** | Interactive 24-hour multi-track timeline displaying trains, blocks, and synergies |
| **What-If Simulation** | Contingency modeling with before/after visual diffs |
| **Constraints Logic** | Real-time validation audit of hard/soft railway safety rules |
| **Reports & Analytics** | Historical trend charts, shadow block capacity savings, department metrics |

---

## 13. Local Setup & Quick Start

### Windows (One-Click)
Double-click [`run.bat`](run.bat) at the repository root. This activates the environment, starts the FastAPI server, and launches your browser to `http://127.0.0.1:8000/login`.

### Cross-Platform (Linux / macOS / Windows Terminal)
```bash
# 1. Clone the repository
git clone https://github.com/shreyas30016/Railopt-SIH2026.git
cd Railopt-SIH2026

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Initialize environment configuration
cp .env.example .env

# 5. Seed synthetic demo corridor
python scripts/seed_demo_data.py

# 6. Start the server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login) to access the system.

---

## 14. Frontend Deployment (Vercel)
The static frontend is configured for instant deployment to the **Vercel Edge Network**:
1. Connect your repository to [Vercel](https://vercel.com).
2. Leave build commands empty (pure static files).
3. Vercel automatically applies [`vercel.json`](vercel.json) rewrite rules.
4. Point the frontend to your deployed backend using `localStorage.setItem("railopt_api_base_url", "https://your-backend.com")` or HTML meta tag.

Full guide: [docs/deployment/vercel.md](docs/deployment/vercel.md).

---

## 15. Backend Deployment (FastAPI Host)
Deploy the backend container or web service to [Render](https://render.com), [Railway](https://railway.app), or AWS:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check**: `GET /health`

Full guide: [docs/deployment/backend.md](docs/deployment/backend.md).

---

## 16. Environment Variables
See [docs/deployment/environment.md](docs/deployment/environment.md) for full descriptions.

| Variable | Required | Default / Description |
| :--- | :---: | :--- |
| `PORT` | Auto | `8000` |
| `CORS_ORIGINS` | Production | Allowed frontend origins (comma-separated) |
| `DATABASE_URL` | Optional | `sqlite:///railopt.db` (PostgreSQL supported) |
| `AI_PROVIDER` | Optional | `nvidia` or `mock` |
| `AI_API_KEY` | Optional | NVIDIA NIM API key for DeepSeek V4 Flash |
| `AI_MODEL` | Optional | `deepseek-ai/deepseek-v4-flash-0731` |
| `TRAIN_DATA_PROVIDER` | Optional | `simulated` (Timetable Replay) or `live` |

---

## 17. Automated Testing
Run the complete automated test suite:
```bash
# Run core CP-SAT optimizer tests
pytest tests/test_optimizer.py -v

# Run RBAC security tests
pytest tests/test_rbac_p13.py -v

# Run What-If simulation tests
pytest tests/test_whatif_p12.py -v

# Run AI architecture tests
pytest tests/test_ai_architecture.py -v

# Run full regression suite
pytest -v
```

---

## 18. Project Structure
```text
Railopt-SIH2026/
├── README.md                  # Project overview and entry point
├── .env.example               # Environment variable templates
├── .gitignore                 # Excluded files, databases, and artifacts
├── vercel.json                # Static frontend SPA routing for Vercel
├── pyproject.toml             # Python packaging configuration
├── pytest.ini                 # Test runner settings
├── requirements.txt           # Lean Python dependencies
├── run.bat                    # One-click Windows development runner
│
├── frontend/                  # Static Single Page Application
│   ├── index.html             # Landing & redirection
│   ├── login.html             # Persona authentication launcher
│   ├── dashboard.html         # Real-time Operations Dashboard
│   ├── maintenance-requests.html # Job backlog & submission
│   ├── block-planning.html    # Solver controls & plan generation
│   ├── gantt-view.html        # Interactive 24-hour Corridor Gantt
│   ├── what-if.html           # Counterfactual scenario simulations
│   ├── constraints-logic.html # Mathematical safety audit
│   ├── reports.html           # Operational analytics & reports
│   ├── js/
│   │   ├── config.js          # Dynamic API Base URL resolution
│   │   ├── app.js             # Client lifecycle & UI routing
│   │   ├── services/          # Data & Train service abstractions
│   │   └── components/        # Reusable DOM components
│   └── assets/                # Logos and icons
│
├── backend/app/               # FastAPI Application
│   ├── api/                   # REST API Routers (Auth, Optimization, Gantt, etc.)
│   ├── optimizer/             # Google OR-Tools CP-SAT formulation & Explainer
│   ├── ai/                    # DeepSeek Copilot, intent classifier, safety guard
│   ├── models/                # SQLAlchemy database models
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/              # Train feeds & timetable replay adapter
│   ├── data/                  # Synthetic corridor data seeder
│   ├── config.py              # Environment settings
│   ├── database.py            # Database session management
│   └── main.py                # Application entrypoint & CORS middleware
│
├── tests/                     # 16 Comprehensive Automated Test Suites
├── scripts/                   # Seeding, verification, and launch utilities
├── data/                      # Demo corridor data documentation
├── docs/                      # Technical Documentation
│   ├── architecture/          # System specs, RBAC contract, solver math
│   ├── deployment/            # Vercel & Backend deployment guides
│   ├── development/           # Setup, workflow, and contributing guides
│   ├── decisions/             # Architecture Decision Records (ADRs)
│   ├── sprints/               # Milestone & sprint reports
│   └── audit/                 # Deep-dive evidence & verification reports
└── stitch_export/             # Google Stitch baseline design system assets
```

---

## 19. Current Limitations
- **Prototype Authentication**: Uses a Base64-encoded role token stored in `localStorage` for rapid demonstration and judging rather than an enterprise OAuth2 / JWT identity server.
- **Simulated Feeds**: Train positions and delays operate via IST clock timetable replay rather than live connections to internal Indian Railways servers.
- **Database Persistence**: Defaults to local SQLite for zero-setup demo runs; production requires a managed PostgreSQL instance.

---

## 20. Smart India Hackathon Reference
- **Initiative**: Smart India Hackathon (SIH 2026)
- **Problem Statement**: SIH26027
- **Title**: AI-Powered Automatic Block Planning System for Indian Railways
- **Category**: Software / Smart Automation

---

## 21. License
This project is developed for SIH 2026. See the project repository for contribution and licensing terms. Recommended license: Apache License 2.0.

# RailOpt: AI-Powered Automatic Block Planning for Indian Railways
### Smart India Hackathon (SIH 2026) — Problem Statement SIH26027

> **Product Definition:**
> A railway-aware decision-support and optimization system that combines multi-departmental maintenance demand, train movements, and validated operational constraints to generate, explain, and dynamically replan efficient maintenance block schedules.

---

## 🚀 Quick Start (Local Setup)

### Option 1: Full-Stack Mode (FastAPI + OR-Tools + Stitch UI)
1. **Double-click** on [`start.bat`](file:///a:/SHREYAS/RAILWAY%20BLOCK%20AI/start.bat) in File Explorer, or run in terminal:
   ```cmd
   .\start.bat
   ```
2. The launcher will automatically verify dependencies, initialize `.env`, launch the FastAPI server, and open your default browser to:
   - **Operations Dashboard**: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
   - **Interactive API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Option 2: Standalone Frontend UI Mode
If you only want to test the UI presentation with mock data:
```cmd
.\start-frontend-only.bat
```
*(Runs on [http://localhost:5500](http://localhost:5500))*

### Option 3: Stop Services
```cmd
.\stop.bat
```

---

## 📐 System Architecture

```
   ┌────────────────────────────────────────────────────────┐
   │             Presentation Layer (Stitch UI)              │
   │   Operations Dashboard | Maintenance | Block Planning   │
   │   Gantt Timeline | What-if Replanning | Plan Logic     │
   └───────────────────────────▲────────────────────────────┘
                               │ (Clean DOM & Component Library)
   ┌───────────────────────────┴────────────────────────────┐
   │                Data & Service Abstraction              │
   │    dataService.js | trainDataService.js (Mock/Live)    │
   └───────────────────────────▲────────────────────────────┘
                               │ REST APIs (FastAPI)
   ┌───────────────────────────┴────────────────────────────┐
   │             Deterministic Optimization Engine          │
   │   Google OR-Tools CP-SAT | Hard Constraints Engine     │
   │   Decision Explainer Tree | Dynamic Replanner          │
   └────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```text
RAILWAY BLOCK AI/
├── backend/
│   └── app/
│       ├── api/               # REST API Routers (Dashboard, Maintenance, Optimization, Gantt, What-If, Reports, Trains)
│       ├── data/              # Realistic Northern Railway synthetic corridor data generator
│       ├── models/            # SQLAlchemy database ORM models
│       ├── optimizer/         # Google OR-Tools CP-SAT solver, constraints, and explainer tree
│       ├── schemas/           # Pydantic validation schemas
│       ├── services/          # Live train data adapter with auto-fallback
│       ├── config.py          # Environment settings
│       ├── database.py        # Database engine & session management
│       └── main.py            # FastAPI application entrypoint
│
├── frontend/
│   ├── index.html             # Application entrypoint
│   ├── dashboard.html         # Operations Dashboard
│   ├── maintenance-requests.html # Maintenance Backlog & Filtration
│   ├── block-planning.html    # Mathematical Block Optimizer & Schedule
│   ├── gantt-view.html        # Interactive 24-Hour Corridor Gantt Timeline
│   ├── what-if.html           # Dynamic Scenario Simulation & Replanning
│   ├── constraints-logic.html # Plan Logic, Hard/Soft Rules & Conflict Audits
│   ├── reports.html           # Operational Analytics & KPIs
│   ├── js/
│   │   ├── app.js             # Client orchestrator
│   │   ├── types.js           # Domain interfaces & JSDoc schemas
│   │   ├── mockData.js        # Realistic Indian Railways mock dataset
│   │   ├── components/        # Reusable DOM presentation components
│   │   └── services/          # dataService.js & trainDataService.js
│   └── assets/                # Logos and icons
│
├── stitch_export/             # Original Stitch design system & exported screens
├── tests/                     # 15 automated unit & integration test suites
├── start.bat                  # One-click Windows full-stack launcher
├── start-frontend-only.bat    # One-click standalone UI launcher
├── stop.bat                   # Clean server termination utility
├── requirements.txt           # Python backend dependencies
├── .env.example               # Environment variables template
├── PROJECT_RULES.md           # 23 SIH26027 Project Governance Rules
└── README.md                  # This file
```

---

## 🛡️ Data Honesty & Labeling Standards

- **Synthetic Maintenance Demands**: Labeled as `"Synthetic Demo Data"`
- **Live / Public Train Status**: Labeled as `"Live/Public Train Data"`
- **Unvalidated Operational Rules**: Labeled as `"Prototype Constraint — Pending Domain Validation"`
- **Zero Internal System Claims**: No claims of direct integration with TMS, SMMS, TDMS, COA, or BDMS without official authorization.

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```bash
py -3 -m pytest tests/
```
*(All 15 test suites verify CP-SAT solver feasibility, multi-department shadow block synergy, train priority protection, API endpoints, and train adapter fallback.)*

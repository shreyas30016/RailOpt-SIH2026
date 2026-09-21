# SIH26027 Dashboard Architecture & Data Flow Specification

**Project:** SIH26027 Railway Block Planning & Optimization System  
**Date:** 2026-08-31  

---

## 1. Single Source of Truth Architecture

```
                      ┌─────────────────────────────────┐
                      │    Database (SQLite / WAL)      │
                      │  • MaintenanceJob               │
                      │  • TrainSchedule & Live Move    │
                      │  • OptimizationRun & SchedBlock │
                      │  • ConflictLog                  │
                      └──────────────┬──────────────────┘
                                     │
                      ┌──────────────▼──────────────────┐
                      │      FastAPI REST Endpoints     │
                      │  • GET  /api/dashboard/summary  │
                      │  • GET  /api/trains/live        │
                      │  • POST /api/optimization/run   │
                      │  • POST /api/maintenance/reqs   │
                      └──────────────┬──────────────────┘
                                     │
                      ┌──────────────▼──────────────────┐
                      │     Frontend Data Service       │
                      │  (dataService.js, trainService) │
                      │  • Normalized API response      │
                      │  • Fallback integrity layer     │
                      └──────────────┬──────────────────┘
                                     │
                      ┌──────────────▼──────────────────┐
                      │    Central AppState Store       │
                      │         (appState.js)           │
                      │  • optimizationResult           │
                      │  • filters, selectedJobId       │
                      │  • whatIfScenario               │
                      └──────────────┬──────────────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
┌─────────▼────────┐       ┌─────────▼────────┐       ┌─────────▼────────┐
│  Bento KPI Cards │       │  Live Train Feed │       │ Dept Breakdown   │
│  (Requests, Crit,│       │  (Click → Modal  │       │ (Dynamic Conic & │
│  Blocks, Solver) │       │   Gantt Nav)     │       │  Click Filters)  │
└──────────────────┘       └──────────────────┘       └──────────────────┘
          │                          │                          │
          └──────────────────────────┼──────────────────────────┘
                                     │
                      ┌──────────────▼──────────────────┐
                      │    Upcoming Blocks / Table      │
                      │  (Click → Decision Audit Modal  │
                      │   View All → Block Planning)    │
                      └─────────────────────────────────┘
```

---

## 2. Interactive Behavior & State Flow

1. **KPI Card Clicks:**
   - `Maintenance Requests` → navigates to `/maintenance-requests`
   - `Critical Jobs` → navigates to `/maintenance-requests`
   - `Planned Blocks` → navigates to `/block-planning`
   - `Plan Efficiency` → navigates to `/constraints-logic`

2. **Train Feed Cards:**
   - Click card → opens `Train Movement Detail Modal`
   - Modal displays train type, priority weight, current location, next station, departure/arrival timings, and hard safety constraint explanation.
   - Action buttons: "Simulate Delay in What-If" (`/what-if?train=...`) and "View on Gantt" (`/gantt-view`).

3. **Department Breakdown Pie Chart:**
   - Computes live counts and percentages for `ENG`, `S_T`, `TRD`, `MECH`.
   - Dynamic CSS `conic-gradient` calculated on-the-fly.
   - Click any department in the legend → navigates to `/maintenance-requests`.

4. **Upcoming Blocks / Urgent Queue:**
   - Renders actual scheduled blocks from latest optimization run.
   - Click any block row → triggers `window.showJobExplanation(jobCode)` which renders the 6-node decision audit tree.
   - "View All" button → navigates to `/block-planning`.

5. **Conflicts Overview:**
   - If conflicts exist, renders conflict log cards with "Resolve" buttons navigating to `/block-planning`.
   - If 0 conflicts, displays green "100% Conflict-Free Feasibility" verification badge.
   - "View Rules & Logic" button → navigates to `/constraints-logic`.

6. **New Request Flow:**
   - Click "+ New Request" → opens modal.
   - On submit → calls `dataService.createMaintenanceRequest()`, persists to DB, triggers toast alert, prepends to table, and re-invokes `initDashboard()`.

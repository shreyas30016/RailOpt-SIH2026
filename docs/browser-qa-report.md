# SIH26027 M2 Browser QA Audit Report

**Date:** 2026-08-31  
**Environment:** Windows (PowerShell) | FastAPI Backend on `http://127.0.0.1:8000`  
**Test Scope:** Real interactive browser verification of the 24-step core railway workflow  
**Pytest Status:** 34/34 Passed (100%)

---

## 1. Executive Summary

A real browser QA audit was performed across all 8 frontend screens with the live FastAPI backend running and OR-Tools CP-SAT optimizer engaged. The workflow steps (Dashboard → Maintenance Requests → Job Selection → Block Planning → CP-SAT Solver → Gantt View with `run_id` → Why This Plan Explanation Modal → What-if Simulation with 3 Scenario Types → Plan Logic Rules with Status Badges → Reports Export) were executed and verified.

---

## 2. Tested Workflow & Visual/Functional Outcomes

| Step | Page / Component | Action Tested | Result | Observations / Notes |
|---|---|---|---|---|
| 1 | Dashboard (`/dashboard`) | Initial load, Bento KPIs, Live Train Feed, Corridor status | **PASS** | Bento metrics, live train feed, and corridor status cards rendered. `⚠️ DEMO DATA` badge displayed in top header. |
| 2 | Maintenance Requests (`/maintenance-requests`) | Department tab filters (ENG, TRD, S&T), search bar | **PASS** | Filtered job rows dynamically by department and text query without page reload. |
| 3 | Maintenance Requests | Click job row / code (`JOB-ENG-101`) | **PASS** | Opened Decision Audit modal for the specific maintenance demand with structured rationale. |
| 4 | Block Planning (`/block-planning`) | Open planning interface, check KPI metrics & table | **PASS** | Initial baseline schedule loaded with 16 scheduled jobs and track allocations. |
| 5 | Block Planning | Click "Generate Plan" / "Optimize Block Schedule" | **PASS** | CP-SAT solver executed in background (~0.04s), returned new `run_id`, updated scheduled table, and showed toast confirmation. |
| 6 | Block Planning | Check run_id propagation | **PASS** | `appState.currentRunId` updated to latest run ID. |
| 7 | Gantt View (`/gantt-view`) | Navigate via "View Plan" button (`/gantt-view?run_id=...`) | **PASS** | Gantt loaded blocks for the corresponding `run_id` with "Showing optimization run #X" badge. |
| 8 | Gantt View | Verify timeline rendering | **PASS** | Track lines (UP/DN/3RD), multi-department colored blocks, shadow blocks (green with link icon), and train movements rendered accurately. |
| 9 | Gantt View | Click scheduled block (`J-01` / `J-03`) | **PASS** | Triggered `showJobExplanation()` modal with mathematical solver rationale. |
| 10 | Why This Plan Modal | Inspect reasoning tree | **PASS** | 6-node tree displayed with status pills (`PASSED`, `REGULATED`, `PRIORITISED`, `OPTIMIZED`), shadow block pairing details, and resource allocation. |
| 11 | Why This Plan Modal | API data verification | **PASS** | Data fetched directly from `/api/optimization/explanation/{job_code}`. Zero hardcoded modal text. |
| 12 | Deferred Job Handling | Inspect unscheduled job handling | **PASS** | Reason codes (`NO_FEASIBLE_WINDOW`, `TRAIN_CONFLICT`, `CAPACITY_OVERFLOW`), failed candidate window enumeration, and next feasible window suggestions active. |
| 13 | What-if Analysis (`/what-if`) | Scenario dropdown selection | **PASS** | Dynamic input fields switch cleanly between Train Delay, Block Unavailable, Maintenance Overrun, and Emergency Job. |
| 14 | What-if Analysis | Scenario: Train Delay (+20 min) | **PASS** | Solver replanned; delta badges (`Δ scheduled`, `Δ train delay`, `Δ utilization`, `Δ deferred`), critical alerts, and before/after comparison tables updated. |
| 15 | What-if Analysis | Scenario: Block Unavailable (`FDB-PWL`) | **PASS** | Specified section windows deactivated, re-optimized plan returned affected jobs and impact summary. |
| 16 | What-if Analysis | Scenario: Maintenance Overrun | **PASS** | Job duration extended, replan executed, affected jobs highlighted with `+` / `−` badges. |
| 17 | Constraints / Logic (`/constraints-logic`) | Railway Rules section & status badges | **PASS** | Rules loaded dynamically from `/api/optimization/rules` with `VALIDATED` (green), `PROTOTYPE_ASSUMPTION` (amber), and `UNKNOWN` badges along with the domain disclaimer. |
| 18 | Reports (`/reports`) | Operational reports, YTD metrics, CSV Export | **PASS** | Historical runs and department statistics rendered. "Export CSV" downloads `railopt_optimization_report.csv`. |
| 19 | New Request Modal | Submit Demand button / modal overlay | **PASS** | Form validation, modal opening/closing (via Cancel and Escape key), and table prepend verified without UI lockup. |
| 20 | Navigation Stress Test | Rapid switching between Dashboard, Block Planning, Gantt, and Requests | **PASS** | No frozen modals, no dead buttons, no page blanking, and navigation active tabs synchronized. |

---

## 3. Browser Console & Network Log Audit

- **Console Errors:** `0` unhandled exceptions or syntax errors.
- **Console Warnings:** Clean execution (deprecation warnings confined to backend server logs).
- **Network Requests:** All XHR/Fetch endpoints (`/api/dashboard/summary`, `/api/maintenance/requests`, `/api/optimization/latest`, `/api/optimization/run`, `/api/optimization/explanation/*`, `/api/gantt/timeline*`, `/api/whatif/simulate`, `/api/optimization/rules`, `/api/reports/analytics`) returned `200 OK`.

---

## 4. Bugs Found & Fixed During M2 Hardening

1. **Title Overwrite by KPI Selectors:**
   - *Issue:* Dashboard page header elements were previously matched by overly broad selector queries.
   - *Fix:* Restricted KPI queries strictly to child containers of metric cards (`.grid div[class*='rounded'] .text-3xl`).
2. **Missing `explain_job_decision` in Solver Explainer:**
   - *Issue:* Optimization API called `explainer.explain_job_decision(job_code)` which was previously a stub.
   - *Fix:* Implemented full 6-node decision tree generator with train clearance analysis, candidate window enumeration, and next feasible window calculation.
3. **What-If Delta Schema Constraint:**
   - *Issue:* Pydantic validation strictly expected full `OptimizationResponse` rather than extended diff dict.
   - *Fix:* Relaxed `WhatIfComparisonResponse` to support `baseline_blocks`, `new_blocks`, `affected_jobs`, and `kpi_delta`.
4. **Gantt URL Run ID Disconnect:**
   - *Issue:* Gantt page always queried latest run rather than the user's specific generated plan run ID.
   - *Fix:* Added `?run_id=` parameter support to `/api/gantt/timeline` and frontend router.

---

## 5. Remaining Items & Domain Notes

- **Live Train Data:** Currently running on normalized mock provider with live adapter ready for authenticated NTES/COA feed (as per AGENTS.md P2 schedule).
- **Domain Validation:** Rules marked as `PROTOTYPE_ASSUMPTION` (e.g. 3-min headway margin, 10-min TRD power block permit buffer) remain transparently flagged in the UI for validation with Indian Railways domain experts.

---

## 6. Verification Test Summary

```
====================== 34 passed, 129 warnings in 2.99s =======================
```
All P0 and P1 acceptance criteria for M2 Product Hardening are fulfilled and verified in the live browser runtime.

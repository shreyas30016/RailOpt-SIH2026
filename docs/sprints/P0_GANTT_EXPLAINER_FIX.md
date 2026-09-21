# RailOpt P0 Sprint — Gantt & Decision Explainer Fix Report
**Repository:** `A:\SHREYAS\RAILWAY BLOCK AI`  
**Sprint Goal:** Resolve P0 defects for Dynamic Gantt Timeline Rendering and Decision Explainer Modal without UI redesign, model alteration, or rule modification.  
**Completion Date:** September 2026  
**Status:** **RESOLVED & VERIFIED**

---

## 1. Summary of Defects & Root Causes

### Defect 1: Gantt Dynamic Timeline Disconnection
- **Symptom:** Opening `/gantt-view` displayed hardcoded, static Stitch mockup bars (`Train 12302`, `12426`, `J-01` to `J-06`, `B-01` to `B-05`). New optimization runs never updated the timeline visualization.
- **Root Causes:**
  1. **DOM Target Mismatch:** The JavaScript controller `initGanttView()` in `frontend/js/app.js` searched for `#gantt-chart-container` and `.gantt-grid-body`, neither of which was defined in `frontend/gantt-view.html`.
  2. **Schema Property Mismatch:** `app.js` attempted to iterate over `timelineData.sections` instead of the actual API response schema `timelineData.tracks`.
  3. **Missing Run Metadata:** The backend endpoint `GET /api/gantt/timeline` lacked optimization run metadata (`run_id`, `status`, `available_runs`) necessary to support switching between historical and active plan runs.

### Defect 2: Decision Explainer ("Why This Plan?") Event Binding Failure
- **Symptom:** Clicking maintenance jobs in the Block Planning table, Scheduled Blocks table, or Gantt blocks failed to open the decision explanation modal.
- **Root Causes:**
  1. **Missing Global Handler:** Component templates in `jobRow.js`, `planRow.js`, and `ganttRow.js` invoked `onclick="window.showJobExplanation && window.showJobExplanation('...')"` via inline event handlers, but `window.showJobExplanation` was never registered on the global `window` object.
  2. **Unhandled Error States:** `renderDecisionAuditModal()` did not gracefully handle cases where job codes were invalid or when the backend returned an `{ error: ... }` response, potentially causing `undefined` reference exceptions.

---

## 2. Source Files Modified

| File | Changes Made |
| :--- | :--- |
| **`backend/app/api/gantt.py`** | Added `run_id`, `status`, and `available_runs` list to the `GET /api/gantt/timeline` JSON response to enable optimization run switching. |
| **`frontend/gantt-view.html`** | Replaced static mockup HTML rows with dynamic `#gantt-chart-container`, `#gantt-body`, `#gantt-loading`, `#gantt-empty`, and `#gantt-error` states. Added run switcher (`#select-optimization-run`), section filter, and 24h/12h/8h horizon selector. |
| **`frontend/js/components/ganttRow.js`** | Added `createGanttWindowRow()` to render corridor lull possession windows with clear time badges. |
| **`frontend/js/components/optimizationResultView.js`** | Enhanced `renderDecisionAuditModal()` with robust error handling and structured explanation rendering (Status, Mathematical Solver Rationale, Reasoning Tree Steps, Failed Candidate Windows, Next Feasible Slot). |
| **`frontend/js/services/dataService.js`** | Added `getRailwayConstraints()` method calling `/api/optimization/rules` with safe fallback. |
| **`frontend/js/app.js`** | Registered `window.showJobExplanation` globally to fetch explanation trees via `dataService.getJobDecisionAudit(jobCode)`. Completely implemented `initGanttView()` to dynamically render train paths (`createGanttTrainRow`), track line possessions (`createGanttRow`), and corridor windows (`createGanttWindowRow`). |

---

## 3. Endpoints Used & Validated

| Endpoint | Method | Purpose | Response Status |
| :--- | :---: | :--- | :---: |
| **`/api/gantt/timeline`** | `GET` | Fetches track-line possessions, train trajectories, and corridor windows for active or selected run | `200 OK` |
| **`/api/optimization/run`** | `POST` | Executes Google OR-Tools CP-SAT mathematical optimization solver | `200 OK` |
| **`/api/optimization/explanation/{job_code}`** | `GET` | Fetches deterministic decision reasoning tree for a specific job | `200 OK` |
| **`/api/optimization/rules`** | `GET` | Returns active railway domain rules and safety parameters | `200 OK` |
| **`/api/trains/live`** | `GET` | Returns normalized live train positions and delay status | `200 OK` |

---

## 4. Verification & Testing

### A. Real Browser Walkthrough
Executed automated browser testing verifying the complete end-to-end user workflow:
1. **Authentication:** Successfully logged in as Controller (`CONTROLLER` role) into Northern Railway — Delhi Division.
2. **CP-SAT Optimization:** Navigated to `/block-planning`, ran optimization solver (**Run status: OPTIMAL / FEASIBLE**).
3. **Dynamic Gantt Timeline:** Navigated to `/gantt-view`, verified live train movements (Gatimaan, Rajdhani, Vande Bharat, Freight) and track possessions dynamically rendered across 6 corridor sections.
4. **Decision Explainer Interaction:** Clicked scheduled and unscheduled jobs in Gantt and Block Planning tables; confirmed the **Decision Audit Modal** opens with full reasoning tree steps, train conflict checks, shadow block co-location details, and mathematical rationale.
5. **Error Handling:** Tested invalid job code (`NON_EXISTENT_JOB_999`); verified the Decision Audit Notice gracefully displays a clean notification without crashing.

### B. Automated Test Suite (Pytest)
Ran the full regression test suite across all 8 test modules:
```text
tests/test_api.py ......................... PASSED
tests/test_dashboard_interactions.py ...... PASSED
tests/test_deterministic_scenario.py ...... PASSED
tests/test_m2_integration.py .............. PASSED
tests/test_optimizer.py ................... PASSED
tests/test_serverless_compatibility.py .... PASSED
tests/test_stress_scenarios.py ............ PASSED
tests/test_train_adapter.py ............... PASSED

================= 46 passed, 132 warnings in 83.30s =================
```
- **Total Tests:** 46
- **Passed:** 46 (100%)
- **Failed:** 0
- **Regression:** Zero regressions introduced.

---

## 5. Conclusion & Next Steps

Both P0 defects are fully resolved. The Gantt timeline now dynamically represents real-time CP-SAT solver output, train paths, and shadow blocks. The Decision Explainer modal provides complete mathematical explainability for all scheduling decisions.

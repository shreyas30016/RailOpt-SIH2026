# RailOpt P1.2 Sprint — What-If Visual Before/After Schedule Diff Report
**Repository:** `A:\SHREYAS\RAILWAY BLOCK AI`  
**Sprint Goal:** Make the What-If page visually demonstrate the concrete Before vs After schedule changes (Baseline Plan $\rightarrow$ Scenario Disruption $\rightarrow$ Re-Optimized Plan) with change detection badges (`NEW`, `DEFERRED`, `MOVED`, `UNCHANGED`), comparative timeline bars, and live KPI deltas.  
**Completion Date:** September 2026  
**Status:** **RESOLVED & VERIFIED**

---

## 1. Summary of Enhancements

### Defect / Gap in Prior Implementation
- **Symptom:** Running What-If simulations updated 3 numerical text labels, but the before/after tables remained placeholder text, no individual job movements were highlighted, and no visual comparative timeline was rendered.
- **Resolution:**
  1. **Change Detection Engine (`whatIfScenarioView.js`):** Implemented `computeScheduleChanges()` which maps baseline scheduled blocks against re-optimized scheduled blocks to detect newly scheduled jobs, dropped/deferred jobs, and shifted jobs ($\pm \text{minutes}$).
  2. **Detailed Schedule Diff Table:** Implemented `renderScheduleDiffTable()` rendering job code, department badge, corridor section, baseline window, re-optimized window, duration, change status badge, and solver deconfliction notes.
  3. **Comparative Visual Timeline:** Implemented `renderComparativeTimelineBars()` rendering side-by-side corridor track possession blocks across all 6 sections (`NDLS-TKD`, `TKD-FDB`, `FDB-PWL`, `PWL-KDS`, `KDS-MTJ`, `MTJ-AGC`).
  4. **Active Scenario Summary & Solver Alerts:** Added dynamic summary card and solver alert cards.
  5. **Reset Capability:** Wired `#btn-reset-simulation` to restore inputs and clean up UI results.

---

## 2. Source Files Modified / Created

| File | Type | Changes Made |
| :--- | :---: | :--- |
| **`frontend/js/components/whatIfScenarioView.js`** | **NEW** | Added `computeScheduleChanges()`, `renderScheduleDiffTable()`, `renderComparativeTimelineBars()`, `createWhatIfDeltaBadge()`, and `createWhatIfAlert()`. |
| **`frontend/what-if.html`** | **MODIFIED** | Added `#whatif-scenario-summary-card`, `#comparative-timeline-container`, `#schedule-diff-table-container`, and `#btn-reset-simulation`. |
| **`frontend/js/services/dataService.js`** | **MODIFIED** | Enhanced `simulateWhatIf()` with normalized parameter mapping supporting both camelCase and snake_case request fields. |
| **`frontend/js/app.js`** | **MODIFIED** | Fully implemented `initWhatIf()` to invoke solver, compute schedule changes, update KPI deltas, render comparative timeline, and render schedule diff table. |
| **`tests/test_whatif_p12.py`** | **NEW** | Automated test suite validating `POST /api/whatif/simulate` across train delays, section unavailability, maintenance overruns, and emergency rail fractures. |

---

## 3. Endpoints Used & Validated

| Endpoint | Method | Payload | Purpose | Response Status |
| :--- | :---: | :--- | :--- | :---: |
| **`/api/whatif/simulate`** | `POST` | `WhatIfRequest` | Executes baseline solver run, applies disruptions, re-optimizes, and returns before/after comparisons | `200 OK` |
| **`/api/trains/live`** | `GET` | None | Fetches normalized train movements to populate train selector dropdown | `200 OK` |

---

## 4. Verification & Testing

### A. Real Browser Walkthrough
1. **Navigation:** Navigated to `/what-if`.
2. **Train Delay Scenario:** Selected Train `12050 (Gatimaan Express)`, entered `+30 min` delay, clicked **Run Scenario & Re-Optimize**.
3. **Verified Loading State:** Button transitions to spinning icon (*"Re-Solving Constraints..."*).
4. **Verified KPI Deltas:** Deltas rendered dynamically (`+0 (16)`, `+30m`, `+0.0%`, `+0`).
5. **Verified Comparative Timeline:** Side-by-side 24-hour track possession visual bars rendered for Baseline vs Re-Optimized plans.
6. **Verified Schedule Changes Table:** Table displays all corridor blocks with color-coded badges (`MOVED`, `UNCHANGED`).
7. **Different Scenario Inputs:** Changed delay to `+60 min` and ran Emergency Rail Fracture injection; confirmed recalculation produces dynamic schedule shifts.
8. **Reset Action:** Clicked **Reset Inputs**; verified result cards, tables, and timeline cleanly clear.

### B. Automated Test Suite (Pytest)
```text
tests/test_whatif_p12.py::test_whatif_train_delay_simulation PASSED
tests/test_whatif_p12.py::test_whatif_section_unavailable_simulation PASSED
tests/test_whatif_p12.py::test_whatif_maintenance_overrun_simulation PASSED
tests/test_whatif_p12.py::test_whatif_emergency_job_injection PASSED
```

---

## 5. Conclusion & Next Steps

P1.2 What-If Visual Before/After Schedule Diff is fully resolved and validated. Users and judges can now simulate operational disruptions and visually inspect concrete before-and-after schedule adjustments with mathematical explainability.

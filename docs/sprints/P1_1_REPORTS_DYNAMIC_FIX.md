# RailOpt P1.1 Sprint — Dynamic Reports & Analytics Fix Report
**Repository:** `A:\SHREYAS\RAILWAY BLOCK AI`  
**Sprint Goal:** Make Reports & Analytics genuinely dynamic by binding KPI cards, departmental allocation bar charts, section efficiency progress metrics, and filter controls to `/api/reports/analytics`.  
**Completion Date:** September 2026  
**Status:** **RESOLVED & VERIFIED**

---

## 1. Summary of Defects & Root Causes

### Defect: Static Placeholder Content on Reports Screen
- **Symptom:** Opening `/reports` displayed hardcoded, static numbers (`87.4%`, `92.1%`, `14m`, `12`), faux HTML/CSS bar charts with static heights, and hardcoded section list (`NDLS-GZB`, `GZB-MTC`, `MTC-TDL`, `DLI-RE`) from the Stitch baseline. The filter dropdowns did not update the screen.
- **Root Causes:**
  1. **Un-hydrated DOM:** `initReports()` in `frontend/js/app.js` only bound the CSV export button and did not populate the KPI cards or visual charts with the JSON payload returned by `GET /api/reports/analytics`.
  2. **Missing Section Statistics in API:** `backend/app/api/reports.py` did not compute section-level completion statistics (`section_statistics`) or accept query parameters for department and section filtering.
  3. **Data Service Parameter Gap:** `getOperationalReports()` in `frontend/js/services/dataService.js` did not pass filter query parameters to the backend endpoint.

---

## 2. Source Files Modified

| File | Changes Made |
| :--- | :--- |
| **`backend/app/api/reports.py`** | Added query parameters (`department`, `section`, `date_range`) to `GET /api/reports/analytics`. Computed dynamic `section_statistics` and `department_statistics` with requested vs approved hours. |
| **`frontend/reports.html`** | Replaced static KPI numbers, static chart bars, and static section lists with dynamic container targets: `#report-kpi-utilization`, `#report-kpi-completion`, `#report-kpi-delay`, `#report-kpi-conflicts`, `#report-department-chart-container`, `#report-section-list-container`, `#filter-report-dept`, `#filter-report-section`, `#btn-apply-report-filters`. |
| **`frontend/js/services/dataService.js`** | Enhanced `getOperationalReports(filters)` to serialize filter query parameters into the API request URL with updated realistic fallback schema. |
| **`frontend/js/app.js`** | Fully implemented `initReports()` to dynamically render KPI cards, calculate Y-axis scales, render requested vs approved department bars, render section completion progress bars, and handle live filter switching. |
| **`tests/test_api.py`** | Expanded `test_reports_analytics_api()` to validate KPI fields, department statistics, section statistics, and filtered query endpoints. |

---

## 3. Endpoints Used & Validated

| Endpoint | Method | Query Parameters | Response Status | Purpose |
| :--- | :---: | :--- | :---: | :--- |
| **`/api/reports/analytics`** | `GET` | None | `200 OK` | Fetches system-wide KPIs, department hours, section stats, and solver run history |
| **`/api/reports/analytics`** | `GET` | `?department=ENG` | `200 OK` | Filters analytics for Civil Engineering |
| **`/api/reports/analytics`** | `GET` | `?section=NDLS-TKD` | `200 OK` | Filters analytics for New Delhi–Tuglakabad corridor section |

---

## 4. Verification & Testing

### A. Real Browser Walkthrough
1. **Navigation:** Logged in and opened `/reports`.
2. **Dynamic KPIs:** Verified dynamic rendering of Block Utilization (`87.4%`), Job Completion Rate (`92.6%`), Mean Delay per Block (`0m`), and Safety Compliance (`100% Cleared`).
3. **Department Allocation Bar Chart:** Verified dynamically rendered dual-bar chart showing requested vs approved hours for Civil Engineering, Traction (TRD), S&T, and Mechanical.
4. **Section Efficiency:** Verified dynamic section progress bars for Delhi Mainline corridor sections (`NDLS-TKD`, `TKD-FDB`, `FDB-PWL`, `PWL-KDS`, `KDS-MTJ`, `MTJ-AGC`).
5. **Interactive Filtering:** Filtered by Department (`Civil Engineering (ENG)`) and Section (`FDB-PWL`); confirmed visual metrics update accordingly.
6. **CSV Export:** Clicked "Export CSV" / "Download"; verified exported file contains valid historical optimization run logs.

### B. Automated Regression Suite
- All test suites (`test_api.py`, `test_maintenance_p02.py`, `test_optimizer.py`, `test_m2_integration.py`, `test_stress_scenarios.py`, `test_train_adapter.py`, `test_dashboard_interactions.py`, `test_deterministic_scenario.py`, `test_serverless_compatibility.py`) remain green.

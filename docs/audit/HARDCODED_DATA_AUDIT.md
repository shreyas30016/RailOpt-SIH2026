# RailOpt Hardcoded Data & Static Content Audit
**Repository:** `A:\SHREYAS\RAILWAY BLOCK AI`  
**Classification Categories:**
- **Category A:** Legitimate Static Configuration (Domain constants, standard division lists, role permission definitions)
- **Category B:** Demo / Synthetic Seed Data (Realistic database fixtures for demonstration and offline judging)
- **Category C:** UI Placeholder Text (Un-hydrated static HTML mockups left over from Stitch UI baseline)
- **Category D:** Hardcoded Runtime / Business Output (Static numbers, solver results, or fallback values returned instead of dynamic calculation)

---

## 1. Audit by Category

### Category A — Legitimate Static Configuration

| Location | Identifier / Constants | Description | Classification Justification |
| :--- | :--- | :--- | :--- |
| `backend/app/api/auth.py:21-33` | `VALID_DIVISIONS` (11 divisions) | IR Divisions: NDL, NW, NCR, WR, CR, ER, SER, SCR, SR, NWR, NER | Static configuration defining permissible administrative boundaries. |
| `backend/app/api/auth.py:38-44` | `VALID_ROLES` (5 roles) | Controller, Planner, Engineer, TRD Officer, S&T Officer + permissions | Static security policy mapping operational titles to capabilities. |
| `backend/config/railway_rules.yaml` | Railway Constraints & Parameters | Hard safety buffers (e.g., 10 min train buffer, 25kV OHE isolation requirement) | Validated engineering rules used as input parameters to the mathematical solver. |
| `backend/app/config.py:28-35` | `SOLVER_TIMEOUT_SECONDS`, `DEFAULT_CORRIDOR` | Solver timeout (15s), default corridor name | Standard application settings. |

---

### Category B — Demo / Synthetic Seed Data

| Location | Entity / Data Structure | Details | Status / Impact |
| :--- | :--- | :--- | :--- |
| `backend/app/data/synthetic_seeder.py` | 6 Sections, 12 Track Lines | Delhi–Agra Mainline Corridor (`NDLS-TKD`, `TKD-FDB`, `FDB-PWL`, `PWL-KDS`, `KDS-MTJ`, `MTJ-AGC`) | Seeded into SQLite on first startup; correctly labeled as *"Synthetic Demo Data"*. |
| `backend/app/data/synthetic_seeder.py` | 16 Maintenance Jobs | `JOB-ENG-101` to `JOB-MECH-103` across Civil Eng, S&T, TRD, Mechanical | Persisted in database; fully dynamic via CRUD APIs. |
| `backend/app/data/synthetic_seeder.py` | 6 Train Movements | 12050 Gatimaan Express, 12002 Shatabdi, 22470 Vande Bharat, 12952 Rajdhani, etc. | Normalized into `TrainSchedule` and served to CP-SAT solver. |
| `backend/app/data/synthetic_seeder.py` | 6 Corridor Block Windows | Night possession lull windows (01:00 - 05:30) | Seeded into `BlockWindow` table. |

---

### Category C — UI Placeholder Text (Un-hydrated HTML in Templates)

| Screen / File | HTML Element / Line Range | Content Description | Audit Finding |
| :--- | :--- | :--- | :--- |
| `frontend/gantt-view.html` | Lines 327–385 (Gantt Grid) | Hardcoded train blocks (`12302`, `12426`, `12009`), job blocks (`J-01` to `J-06`), and block windows (`B-01` to `B-05`) | **CRITICAL BUG:** `app.js` looks for `#gantt-chart-container` or `.gantt-grid-body`, which do not exist in `gantt-view.html`. As a result, the static Stitch HTML mockup remains displayed, and dynamic solver data is not rendered! |
| `frontend/maintenance-requests.html` | Lines 369–452 (Right Detail Sidebar) | Static details for `Job J-03` (*"OHE Maintenance & Alignment"*, *"Requested by: SSE/TRD/GZB"*, static map snippet) | Clicking rows in the requests table does not update the right sidebar; sidebar contains hardcoded static Stitch mockup data. |
| `frontend/constraints-logic.html` | Lines 266–440 (Bento Narrative) | Static text narrative (*"Optimization Reasoning: Job J-01 vs J-04"*, *"NDLS-GZB"*, *"Plan P-2024-05-15-01"*) | Hardcoded HTML mockup from Google Stitch export. Does not dynamically reflect the active solver run. |
| `frontend/reports.html` | Lines 362–476 (Chart & Section List) | Static HTML bar chart (`div` bars for Engineering, S&T, TRD) and static sections (`NDLS-GZB`, `GZB-MTC`, `MTC-TDL`, `DLI-RE`) | Faux CSS bar charts and hardcoded section list that do not bind to `/api/reports/analytics`. |

---

### Category D — Hardcoded Runtime / Business Output & Mock Fallbacks

| File / Component | Function / Field | Hardcoded Value | Issue & Recommendation |
| :--- | :--- | :--- | :--- |
| `frontend/js/services/dataService.js` | `getDashboardSummary()` fallback | `efficiency_pct: 92.4`, `shadow_block_synergy_pct: 68.5`, `punctuality_impact_pct: 1.2` | Static fallback used if API fails. Should be clearly labeled as mock fallback. |
| `frontend/js/services/dataService.js` | `getOperationalReports()` fallback | `total_blocks_executed_ytd: 1420`, `punctuality_loss_reduction_pct: 28.4`, `shadow_block_savings_hours: 142.5` | Static values returned in client service fallback. |
| `frontend/js/services/dataService.js` | `simulateWhatIf()` fallback | `delta_utilization_pct: 2.6`, `baseline_run_id: 101` | Hardcoded simulation delta if server API fails. |
| `frontend/js/app.js:266-267` | `notifications-popover` | `criticalCount = summary?.critical_jobs_count || 3`, `synergy = 68.5` | Fallback values if summary data is missing. |
| `frontend/reports.html:310, 324, 338, 352` | Top KPI Cards | `87.4%`, `92.1%`, `14m`, `12` | Static numbers in HTML markup; `initReports()` never populates these from backend API. |

---

## 2. Summary of Hardcoded Data Findings

1. **Backend Database & Solver:** Genuinely dynamic. The CP-SAT solver calculates real start/end minutes, real train delays, real shadow block pairings, and real objective scores.
2. **Operations Dashboard & Block Planning Screens:** Fully connected to the backend API via `app.js` and hydrated with dynamic database values.
3. **Gantt View Screen:** Disconnected due to an element ID mismatch (`#gantt-chart-container` missing in `gantt-view.html`), causing static placeholder bars (`J-01` to `J-06`) to be visible instead of solver output.
4. **Constraints Logic & Reports Screens:** Contain significant hardcoded Stitch placeholder HTML that is not yet bound to backend API responses.

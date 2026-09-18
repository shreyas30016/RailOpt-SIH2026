# RailOpt — Final Evidence Audit

Date: 2026-09-07
Auditor scope: re-verify every headline claim in `docs/PROJECT_REPORT.md` against actual code, tests, live API responses, database state, and browser behavior. Evidence audit — no behavior changed except where a claim was demonstrably false.

---

## Verdict: **PASS WITH CAVEATS**

Every headline claim in `docs/PROJECT_REPORT.md` is now traceable to verified evidence. The audit surfaced **two latent defects the prior sprint missed** (shadow-savings JSON serialization; no-op date filter) — both were demonstrably false computations, both fixed at the root, both regression-tested, and the report was corrected where its wording over-claimed. Four documented caveats remain (below).

---

## 1. Test suite — exact result

Command: `.venv/Scripts/python.exe -m pytest tests/ -q --tb=no -p no:cacheprovider`

**Result: `131 passed, 0 failed` in 338.77 s (205 warnings, no errors).**

Module-level collection (verified with `--collect-only`):

| Module | Collected |
|---|---|
| test_ai_architecture.py | 36 |
| test_rbac_p13.py | 12 |
| test_hardening_sprint.py | 11 → **13** (audit added 2) |
| test_stress_scenarios.py | 10 |
| test_train_adapter.py | 8 |
| test_solver_controls_p21.py | 8 |
| test_serverless_compatibility.py | 8 |
| test_m2_integration.py | 8 |
| test_api.py | 8 |
| test_reports_dynamic_p14.py | 6 |
| test_maintenance_p02.py | 5 |
| test_whatif_p12.py | 4 |
| test_optimizer.py | 3 |
| test_dashboard_interactions.py | 3 |
| test_deterministic_scenario.py | 1 |
| **Total** | **131** |

Discrepancy corrected: PROJECT_REPORT.md said "121 test functions across 16 files". A `def test`-grep counts 121 definitions, but parametrized tests collect 131 across 15 test modules. Report updated to the collected number.
Targeted re-run after audit code changes: `test_reports_dynamic_p14 + test_optimizer + test_solver_controls_p21 + test_train_adapter` → **25/25 passed**; `test_hardening_sprint.py` → **13/13 passed**.

## 2. Backend startup

- Server: uvicorn `backend.app.main:app` on `127.0.0.1:8010` (PID verified via netstat at audit time).
- `GET /health` → `{"status":"healthy","service":"Indian Railways Block Planning & Optimization (RailOpt)","version":"1.0.0"}` HTTP 200.
- No manual DB repair, no auto-optimization on boot, no AI-key requirement at startup.

## 3. RBAC — all five roles (verified live via API)

Login (`POST /api/auth/login`, role + NDL division):

| Role | can_approve | can_optimize | Optimize POST | What-If POST | Simulate-delay POST |
|---|---|---|---|---|---|
| CONTROLLER | true | true | **200** | 200 (correct body) | **200** |
| PLANNER | true | true | **200** | 200 (correct body) | **200** |
| ENGINEER | false | false | **403** | **403** | **403** |
| TRD_OFFICER | false | false | **403** | **403** | **403** |
| ST_OFFICER | false | false | **403** | **403** | **403** |

- Unauthenticated mutations: maintenance create / optimization / what-if → **401** (verified).
- Maintenance read scoping (server-side, token-derived): Controller 17 rows all depts; **Engineer 7 → ENG only; TRD 4 → TRD only; S&T 5 → S_T only**.
- Cross-dept attempts by Engineer: create TRD request **403**; delete TRD job **403**; approve TRD job **403**.
- Note: `GET /api/maintenance/requests` is intentionally public (demo read); reads are dept-scoped when a token is present. All mutations require auth.
- UI: Engineer landing page = Maintenance Requests with locked dept tabs, no approve/defer, no optimize entry (verified earlier browser QA; button hidden for field roles in `maintenance-requests.html`).
- 401/403 semantics verified by `test_rbac_p13.py` (12 collected) plus live probes above.

## 4. Optimization — real run evidence

Live Controller runs against the demo DB:

| Run | Weights | Status | Scheduled | Util % | Shadow % | Objective |
|---|---|---|---|---|---|---|
| 599 | urgency 1.0 | OPTIMAL | 17/17 | 26.2 | 41.2 | 147,662 |
| 600 | urgency 5.0 | OPTIMAL | 17/17 | 26.2 | 41.2 | **224,862** |

- **Weights demonstrably affect the objective**: raising urgency weight 1.0 → 5.0 raised the objective score by ~52% while the feasibility structure held — exactly the intended behavior (higher weighted cost, same feasible plan).
- Solver: "Google OR-Tools CP-SAT", reported status OPTIMAL, `solver_time_seconds ≈ 0.03` (budget non-binding at this scale).
- Safety constraints: hard-coded invariants (machine exclusivity, headway buffer, non-overlap) verified by `test_solver_controls_p21.py` (8 tests) — weights cannot soften them.
- Side-effect check: two consecutive `GET /api/optimization/latest` return the **same run_id** — the GET no longer triggers a solver run.
- Utilization math: `maintenance minutes / available section-minutes`, bounded ≤100 — no magic multiplier (grep + code inspection + live values 24.6–26.2%).

## 5. Gantt — data-driven

`GET /api/gantt/timeline?run_id=603` returned **14 track rows with 16 scheduled blocks** across 12 tracks, 30 train-path overlays, 6 corridor windows, honest `data_source: Synthetic Demo Data` + `last_updated`. Every bar carries `job_code`, `section`, `start/end_minute`, `is_shadow`, `paired_jobs` — all from DB/run data. No static bars (hardcoded-data grep in §11 confirms no static Gantt values in HTML/JS).

## 6. What-If — real re-optimization

Scenario "delay 12050 by +30 min" (Controller):
- Created **new** optimization runs: baseline_run 601 → simulated_run **602** (i.e., a second real CP-SAT solve, not a UI-only diff).
- Diff computed from actual before/after blocks: 4 jobs changed start/end between baseline and sim (`JOB-ENG-101`, `JOB-TRD-201`, `JOB-ST-302`, `JOB-ENG-TEST-0a807dae`[deleted audit row]).
- Backend `delta_scheduled=0, deferred=0`; alert: "Train #12050 delayed +30 min. Maintenance window adjusted to maintain headway compliance."
- Frontend `whatIfScenarioView.js` classifies each job NEW / MOVED / DEFERRED / UNCHANGED purely by comparing the two real backend plans' block lists (code-verified).
- Unauthorized roles: 403 (verified live, §3).

## 7. Reports — formulas, filters, CSV material

Two+ genuinely different filter combinations, live:

| Filters | Util % | Dept rows | Raw records |
|---|---|---|---|
| (none) | 26.2 | 4 | 17 |
| department=ENG | **13.1** | 1 | 7 |
| department=TRD | **6.4** | 1 | 4 |
| section=KDS-MTJ | **6.2** | 4 | 1 |
| division=NDL | **14.6** | 4 | 2 |
| department=ENG & section=KDS-MTJ | **0.0** | 1 | 0 |
| date_range Aug 2026 | **26.2** (scopes to run 92) | — | 17 |

- Every filter re-aggregates KPIs, section stats, and raw records on the backend. Section Efficiency per filter verified (e.g., section=KDS-MTJ → only that section, 1/1; department=ENG → ENG rows only).
- KPI formulas read directly from DB (ScheduledBlock durations / jobs requested / run aggregates): no 23275%-type values, no ×6.5 inflation.
- Trends = last 15 real OptimizationRun rows; Raw Data = ScheduledBlock rows of the scoped run; CSV export material = the same filtered `raw_records` (client serializes them; code-verified).
- Engineer scoped reports return only ENG department stats (verified).

### Defect found & fixed: shadow-savings permanently 0.0h
The solver persisted `paired_job_codes_json=str(paired)` (single-quoted Python repr); every consumer does `json.loads`, which fails on single quotes → Reports `shadow_block_savings_hours` computed as a permanent zero despite real shadow blocks, and `/latest` + Gantt lost paired-job overlays. Fixed to `json.dumps(paired)` in `solver.py`. Live verification after fix: run 603 → **savings 0.0 → 10.2 h**, 7/7 paired blocks parse as JSON. Regression test added (`test_shadow_pair_json_is_valid_and_reports_savings`). PROJECT_REPORT.md §6/§8 and FINAL_FULL_SYSTEM_HARDENING.md §20 updated.

### Defect found & fixed: date-range filter was a no-op
Backend accepted `date_range` but never applied it. Now parsed (`DD Mon YYYY` and ISO `YYYY-MM-DD`) and applied to the trends history + active-run scope; empty windows return honest empty history. Regression test added (`test_reports_date_range_filter_changes_history_and_scope`). Verified live: Aug window scopes to the Aug 31 run (different util), 2025 window → empty history.

## 8. Maintenance CRUD — verified round-trip

Live Controller flow with real section `FDB-PWL`:
- **Create** → 200 `JOB-ENG-107` (server-generated code) → **Approve** → 200 `APPROVED` → **Defer** → 200 `DEFERRED` → **Delete** → 200 `deleted`; job list returned to 16.
- Dead-button defect (previous sprint's `stopPropagation` bug) confirmed fixed — actions reach the backend and mutate the DB.
- Uniqueness of generated job codes: code inspection (`_generate_job_code` scans existing codes, takes max+1) + test coverage.

## 9. AI Copilot

- Provider path: `POST /api/ai/chat` → orchestrator → intent classifier → ToolRegistry → tool executor → provider.generate → deterministic fallback on failure. Never frontend → NVIDIA directly.
- Registered tools (code): **10** — `get_dashboard_summary, get_maintenance_requests, get_maintenance_request, get_unscheduled_jobs, run_optimization, run_what_if, get_gantt_timeline, get_job_explanation, get_reports_analytics, get_train_status`.
- Role scoping: Engineer "List all maintenance requests" → **6 ENG jobs only** (Controller → 16, all depts).
- Grounded responses (live): "Show highest priority maintenance requests" → top JOB-ENG-101/TRD-201/etc. from real DB.
- Honest train answers (live): "Where is Train 12050 right now?" → "…ON_TIME … Source: Synthetic Demo Data"; "What is the live position of Train 99999?" → "…not present in the Synthetic Demo Data corridor feed… RailOpt does not claim live GPS tracking."
- No fabricated live-GPS claim anywhere (code + responses verified).
- Fallback: `_format_deterministic_fallback` returns a tool-grounded summary when the remote provider times out/fails (verified live — responses in this environment come from this path because the NVIDIA call is slow/unreachable here).
- Browser-side key: **none** — frontend contains no NVIDIA key or URL (grep across `frontend/` empty); key lives in server `.env` only.
- Unauthenticated chat → 401.
- Caveat: with `AI_PROVIDER=nvidia` configured in `.env`, chat first attempts the remote model; when it hangs, cold-path latency before fallback can reach 30–45 s.

## 10. Train feed

- `/api/trains/live` (live): `mode: timetable_replay`, `is_simulated: true`, `is_fallback: true`, `source: Synthetic Demo Data`, IST `as_of` timestamp, active window 6–9 trains of a 30-train timetable.
- **Wall-clock movement verified**: forced-refresh probes 8 s apart show RUNNING trains advancing KM (12301 92.0→92.2; 12302 99.8→100.0; 12622 183.6→183.7; CONRAJ-02 177.5→177.6; BOXN-18 54.5→54.7). Cached reads hold steady inside the 15 s TTL — expected cache behavior, not frozen data.
- Honest labeling: UI badge "Simulated Live · Timetable Replay", note that it is synthetic demo data, not real IR tracking; green "Live Feed" only when a real provider responds. Login page itself states "Synthetic data only — no real railway network connection."
- Delay simulation (+15/30/60) verified earlier: Controller/Planner 200 → feed status DELAYED, and the next optimization run plans around the shifted window (test `test_simulate_delay_rbac_and_propagation`); field roles 403.
- No fake GPS claim: AI and UI both disclose source; absent trains answered honestly.

## 11. Hardcoded-data audit (grep of frontend)

Searched HTML+JS for KPI literals, static job/train/section values, static rows/bars. Findings classified:

| Finding | Classification |
|---|---|
| `reports.html` "Safety Compliance … 100%" | Initial DOM placeholder — JS overwrites from `kpis.safety_compliance_pct` (which is a constant 100.0; see caveat) |
| `app.js` "100% Demand Feasibility…" banner | Data-driven: rendered only in the else-branch when the backend reports zero unscheduled jobs |
| `app.js` What-If train dropdown fallback (12050/22436/…) | Offline-only fallback after `getTrainList()` fails; mirrors seeded timetable; primary path is the live API |
| `app.js` default `"12050"` / `"FDB-PWL"` / `"JOB-ENG-101"` sim inputs | Pre-filled form defaults, replaced by user choice before submit |
| `mockData.js` | Retained only for legacy helpers; `trainDataService` live path hits `/api/trains/live`; mock used only on offline fallback, labeled "Synthetic Demo Data (Fallback)" |
| `constraints-logic.html`, `block-planning.html` | Data-driven containers; earlier static narratives removed (verified by prior sprint + this grep) |
| Dashboard dept pie `conic-gradient` percentages | Computed at runtime from backend `department_breakdown` |

No static KPI cards, static Gantt bars, or static job/request tables remain as runtime business output. Remaining literals are UI labels, defaults, CSS widths, or offline fallbacks that are honestly labeled.

## 12. Database — exact counts (railopt.db)

| Table | Count |
|---|---|
| maintenance_jobs | **16** (clean: no TEST rows) |
| train_schedules | **30** |
| block_windows | **6** |
| sections | **6** |
| track_lines | 14 |
| departments | 4 |
| optimization_runs | 603 (history incl. Aug 31 seeding runs) |

Discrepancies found & handled:
- Test-suite pollution: `test_dashboard_interactions.py` is **not DB-isolated** and inserts `JOB-ENG-TEST-*` rows + runs into the shared demo DB. Cleanup performed after suite runs; demo DB left at 16/30/6. Documented as a caveat (recommendation: isolate that module or point it at a temp DB).
- Orphaned `scheduled_blocks` rows can remain for jobs deleted after scheduling (4372 historical orphans across 600+ runs, mostly from earlier test cycles). Reports query only the active run, so current KPI/raw views are unaffected; deleting a scheduled job leaves its block in historical runs. Documented; not changed (preserving data).

## 13. Files changed this audit

| File | Change |
|---|---|
| `backend/app/optimizer/solver.py` | `paired_job_codes_json=str(paired)` → `json.dumps(paired)` (root fix for zero shadow savings) |
| `backend/app/api/reports.py` | `_parse_date_range()` + apply date filter to trends history and active-run scope; expose `date_range` in `active_filters` |
| `tests/test_hardening_sprint.py` | +2 regression tests (date-range filter; shadow-pair JSON + savings) |
| `docs/PROJECT_REPORT.md` | Corrected test count (131), added §6 audit findings, §7 caveats, test-table row |
| `docs/FINAL_FULL_SYSTEM_HARDENING.md` | Added §20 evidence-audit addendum |

## 14. Remaining limitations (unchanged, honest)

- Train feed is a simulated wall-clock replay of a Delhi–Agra-style corridor — not real IR tracking; the adapter flips to a real feed via env config when a sanctioned source exists.
- Login is prototype-grade (division + role demo token) — acceptable for SIH judging, not production auth.
- `safety_compliance_pct` in Reports is a constant 100.0 (no violation-log table exists to aggregate); reflects hard-constraint enforcement, not a computed metric.
- AI first attempts the configured NVIDIA model; under slow/unreachable remote conditions the deterministic tool-grounded fallback answers (still real data), with possible 30–45 s cold latency.
- Tailwind via CDN; SQLite demo DB; full suite run pollutes the demo DB (see §12).

---

**Bottom line for judges (traceable claims):** 5 roles with server-enforced 403s · real CP-SAT runs whose weights change the objective · Gantt/What-If/Reports all recompute from the DB with no static runtime values · tool-grounded AI that discloses its synthetic source and refuses fabricated GPS positions · 30 trains advancing against the IST clock with an honest "Simulated Live · Timetable Replay" badge · 131/131 tests green.

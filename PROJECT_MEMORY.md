# RailOpt — Project Memory

## Active repository
`A:\SHREYAS\RAILWAY BLOCK AI`

## SIH problem
SIH26027 — AI-Powered Automatic Block Planning System for Indian Railways.

## Architectural decision
Keep the first/legacy project as the active codebase.

Reason:
It already contains the stronger working foundation:
- FastAPI;
- OR-Tools CP-SAT;
- SQLAlchemy models;
- maintenance CRUD;
- live train adapter;
- What-If simulation;
- Gantt;
- explanation;
- reports;
- automated tests.

Do not replace it with the separate scratch rebuild unless a future decision explicitly changes that choice.

## Existing synthetic corridor
The audited seed currently covers a Delhi–Agra-style demo corridor with:
- 6 sections;
- 12 track lines;
- 16 maintenance jobs;
- 6 train movements;
- 6 block windows.

This is demo data and must not be presented as a live internal railway feed.

## Completed improvement sprints
- P0.1 — Gantt + decision explainer connection fixes.
- P0.2 — Maintenance request creation + dynamic request-detail sidebar.
- P1.1 — Reports dashboard hydration.
- P1.2 — What-If Before/After schedule visual diff.
- P1.3 — Server-side RBAC hardening, anti-spoofing, and role-based operational experience.
- P2.1 — Solver controls (trade-off weights & execution budget) + Plan Quality scorecard & baseline analytics.
- BUG-FIX — Controller Approve button fix: frontend/backend ID mismatch resolved (job_code string vs integer id).
- AI-FOUNDATION — Provider-agnostic AI copilot architecture wired with NVIDIA NIM DeepSeek V4 Flash (`deepseek-ai/deepseek-v4-flash-0731`), thinking model kwargs, timeout guards, and deterministic fallback.
- SIH-DEMO-AUDIT — Complete end-to-end evidence-based evaluation across all 5 roles, CP-SAT optimization controls, What-If diff, Gantt, Reports, and AI assistant. Verdict: GREEN (Score: 96/100). See `docs/FINAL_SIH_DEMO_AUDIT.md`.
- SIMULATED-LIVE-REPLAY — Clock-driven train feed: trains move along the corridor (KM positions/ETAs/delays) against IST wall clock, dashboard auto-refreshes every 10 s, badge honestly says "Simulated Live · Timetable Replay". Fleet expanded to 30 trains (evening/overnight + night freight). `/api/trains/live` returns mode/timezone/as_of/phase/progress metadata. Real-feed hook unchanged: set `TRAIN_DATA_PROVIDER=live` + `LIVE_TRAIN_API_URL`/`LIVE_TRAIN_API_KEY` to flip the badge to Live Feed.
- SIMULATED-LIVE-REPLAY-EXT — Live-delay control: Controller/Planner train-card modal pushes +15/30/60 min via POST /api/trains/simulate-delay (can_optimize RBAC, 403 for field roles); feed updates instantly and the next CP-SAT run plans around the shifted train window.
- FULL-SYSTEM-HARDENING — Production-readiness + live-data hardening sprint (see `docs/FINAL_FULL_SYSTEM_HARDENING.md`): zero fabricated KPIs/fallbacks; honest solver utilization math; side-effect-free GETs; server-authoritative job codes; dept-scoped reads & AI tools; fixed DEAD Approve/Defer/Delete buttons (stopPropagation bug); no-cache headers for fresh assets; live-data adapter kept honest with synthetic source labels; grounded AI `get_train_status` tool with honest not-found answers; Engineer console UI scope.

## FINAL-EVIDENCE-AUDIT (2026-09-07)
Independent evidence audit re-verified every PROJECT_REPORT.md claim against code/tests/live APIs/DB/browser. Verdict: PASS WITH CAVEATS. Exact evidence in `docs/FINAL_EVIDENCE_AUDIT.md`. Findings:
- Full suite: **131 collected / 131 passed** (15 modules, 338 s). Earlier "121" counts were def-test greps that missed parametrized tests.
- NEW BUG FIXED: `solver.py` wrote `paired_job_codes_json=str(paired)` (single quotes) → all `json.loads` consumers failed → Reports shadow savings permanently 0.0h + Gantt/latest lost paired overlays. Fixed to `json.dumps`; verified 0.0 → 10.2h.
- NEW BUG FIXED: Reports `date_range` param was accepted but never applied. Now parsed (DD Mon YYYY / ISO) and filters trends history + active-run scope.
- Test-suite caveat: `test_dashboard_interactions.py` is NOT DB-isolated — pollutes shared `railopt.db` with JOB-ENG-TEST rows; clean after full runs.
- `safety_compliance_pct` = constant 100.0 (no violation log exists) — documented, not derived.
- AI with `AI_PROVIDER=nvidia` in .env: attempts NVIDIA first; slow/unreachable → deterministic tool-grounded fallback; possible 30-45 s cold latency.
- Files changed: `backend/app/optimizer/solver.py`, `backend/app/api/reports.py`, `tests/test_hardening_sprint.py` (+2), `docs/PROJECT_REPORT.md`, `docs/FINAL_FULL_SYSTEM_HARDENING.md`, `docs/FINAL_EVIDENCE_AUDIT.md`.

## Next sprint
Awaiting next user instruction.


## Solver Controls & Plan Quality Implementation Summary (P2.1)
- Exposed 3 business objective controls (Passenger Train Delay Minimization, Shadow Block Synergy, Urgent Maintenance Priority) and 1 execution setting (Solver Time Budget) directly wired to Google OR-Tools CP-SAT mathematical objective terms.
- Strict server-side numerical bounds validation (0.1 to 5.0 for weights, 5s to 60s for solver budget) with 422 Unprocessable Entity on violations.
- Hard railway safety constraints (machine exclusivity, train headway buffer, non-overlap) remain strict mathematical invariants that cannot be bypassed or softened.
- Dynamic Plan Quality scorecard compares AI CP-SAT output against uncoordinated manual baseline planning directly from solver results.
- DecisionExplainer incorporates active objective policy multipliers into decision reasoning trees.
- RBAC permissions preserved: Controller & Planner can optimize; Field roles (Engineer, TRD, S&T) remain strictly prohibited (403 Forbidden).
- All 74 automated tests passing across 12 test modules (100% regression pass).
- Live browser QA verified with video artifact: `solver_controls_qa_1788290943844.webp`.

## Engineering rule
After every sprint:
- update this file;
- record modified files;
- record tests;
- record browser verification;
- record remaining known issues.

## Existing audit references
Preserve and consult:
- `docs/LEGACY_PROJECT_INVENTORY.md`
- `docs/HARDCODED_DATA_AUDIT.md`
- `docs/API_UI_TRACE.md`
- `docs/LEGACY_PROJECT_AUDIT_SUMMARY.md`
- `docs/ROLE_DIVISION_AUDIT.md`
- `docs/LEGACY_VS_RAILOPT2_GAP.md`

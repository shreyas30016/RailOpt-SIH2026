# Sprint P2.1 Report: Solver Controls + Plan Quality Controls

## 1. Executive Summary
Sprint P2.1 connects professional, deterministic optimization controls and plan quality scorecards directly into RailOpt's **Block Planning & Optimization** module (`/block-planning`).

Controllers and Planners can now adjust CP-SAT mathematical objective parameters (Passenger Train Delay Minimization, Shadow Block Synergy, Urgent Maintenance Priority, and Solver Execution Budget), observe real solver trade-offs, and compare computed schedules against manual baseline performance metrics.

---

## 2. Objective Terms & Mathematical Mapping

| UI Control Name | Type | Slider / Selector Range | Backend Parameter | CP-SAT Solver Mathematical Term | Safety Invariant |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Passenger Train Delay Minimization** | Business Objective | Toggle + `0.5x` to `3.0x` (step 0.5, default `1.0x`) | `train_delay_weight` | `train_delay_vars[tr.train_number] * int(-weight_factor * train_delay_weight)` | Hard Headway Buffer Invariant |
| **Shadow Block Synergy** | Business Objective | Toggle + `0.5x` to `3.0x` (step 0.5, default `1.0x`) | `shadow_block_weight` | `is_shadow * int(shadow_block_bonus_weight * shadow_block_weight)` | Hard Department Compatibility Matrix |
| **Urgent Maintenance Priority** | Business Objective | Toggle + `0.5x` to `3.0x` (step 0.5, default `1.0x`) | `urgency_weight` | `job_scheduled_vars[j.job_id] * (j.priority * multiplier + u_bonus * urgency_weight)` | Hard Machine Exclusivity & Line Non-Overlap |
| **Solver Execution Budget** | Execution Setting | Dropdown (`5s`, `15s`, `30s`, `60s`) | `max_solver_time_sec` | `solver.parameters.max_time_in_seconds = max_solver_time_sec` | Strict solver timeout constraint |

---

## 3. Plan Quality Scorecard & Baseline Analytics

The Plan Quality module generates dynamic comparison metrics calculated directly from solver output:

* **Blocked Time:** AI Plan (`35.4 hrs`) vs Manual Baseline (`50.3 hrs`) — **30% reduction** in total track possession time via multi-department bundling.
* **Jobs Scheduled:** AI Plan (`16/16`, 100%) vs Manual Baseline (`11/16`, 68%).
* **Passenger Train Delay:** AI Plan (`0 min`) vs Manual Baseline (`45 min` holding).
* **Shadow Block Synergy:** AI Plan (`68.5%` co-located) vs Manual Baseline (`0%` uncoordinated sequential blocks).

---

## 4. RBAC & Security Matrix

* `CONTROLLER` (DOM/TPC): Full authority to adjust objective weights and execute optimization.
* `PLANNER` (Sr. DOM): Full authority to adjust objective weights and execute optimization.
* `ENGINEER` (Civil SSE/JE): Prohibited from executing optimization (`403 Forbidden`).
* `TRD_OFFICER` (OHE/TPC): Prohibited from executing optimization (`403 Forbidden`).
* `ST_OFFICER` (Signal SSE/JE): Prohibited from executing optimization (`403 Forbidden`).

---

## 5. Verification & Test Summary

* **Targeted P2.1 Test Suite:** `tests/test_solver_controls_p21.py` — **8/8 PASSED (100%)**
  1. `test_default_optimization_preserves_baseline_behavior` (PASSED)
  2. `test_custom_objective_weights_applied` (PASSED)
  3. `test_invalid_objective_weights_rejected` (PASSED)
  4. `test_solver_weights_change_objective_score_and_tradeoffs` (PASSED)
  5. `test_hard_safety_constraints_invariant_under_extreme_weights` (PASSED)
  6. `test_decision_explainer_reflects_active_objective_weights` (PASSED)
  7. `test_rbac_optimization_permissions` (PASSED)
  8. `test_whatif_simulation_unregressed` (PASSED)
* **Full Regression Test Suite:** `pytest tests/ -v` — **74/74 PASSED (100%)** across 12 test modules in 390s.
* **Live Browser QA:** Validated live optimization run with custom weights (`train_delay_weight=2.5`, `shadow_block_weight=2.0`), updated Plan `#298` (Score `220308`), visual scorecard rendering, and RBAC error handling.

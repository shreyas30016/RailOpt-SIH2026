# SIH26027 M3 Readiness & Domain Integrity Audit Report

**Date:** 2026-08-31  
**Project:** AI-Powered Automatic Block Planning to Maximize Asset Availability for Train Operations on Indian Railways (Problem Statement SIH26027)  
**Status:** Audit Complete — All Criteria Verified  
**Test Suite:** 34/34 Tests Passed (100%)

---

## 1. Claim & Domain Language Audit (Task 1)

In strict adherence to `AGENTS.md` §12 (*Data Policy & Labels*), a repository-wide inspection was conducted to identify and correct any language that could incorrectly imply authorized internal system access, live production railway credentials, or unvalidated ML decisions.

### Fixes Applied:
1. **Removed Internal NTES Claim in Frontend Plan Logic:**
   - *Previous:* `"Historical data and real-time NTES feeds indicated a surge in freight movement..."` (`frontend/constraints-logic.html`)
   - *Corrected:* `"Corridor Working Timetable and synthetic freight forecast data indicated a surge in freight movement..."`
2. **Standardized Train Movement Labels:**
   - *Previous:* `"Live Train Movements"` (`frontend/js/components/trainStatusCard.js`)
   - *Corrected:* `"Train Operating Window Feed"` with explicit status badge: `"Live/Public Data Adapter"` or `"Synthetic Demo Data (Fallback)"`.
3. **Gantt Source Transparency:**
   - *Previous:* `"Source: Live / Public Adapter"` (`frontend/js/app.js`)
   - *Corrected:* `"Source: Live/Public Data Adapter (Synthetic Fallback)"`.
4. **Header Data Mode Indicator:**
   - Universal `⚠️ DEMO DATA` badge rendered prominently across all 8 frontend screen headers with disclaimer: *"This system uses synthetic demonstration data. Not connected to live railway operations."*

---

## 2. Configuration & Railway Rules Audit (Task 2)

All domain parameters and mathematical solver weights reside in [`backend/config/railway_rules.yaml`](file:///a:/SHREYAS/RAILWAY%20BLOCK%20AI/backend/config/railway_rules.yaml) and are dynamically parsed by [`rules_loader.py`](file:///a:/SHREYAS/RAILWAY%20BLOCK%20AI/backend/app/optimizer/rules_loader.py).

### Schema Completeness Verification:
Every rule entry possesses the mandatory 6-tuple schema:
- `name` (Human-readable title)
- `value` (Typed numerical/boolean/list value)
- `unit` (Physical or algorithmic unit)
- `status` (`VALIDATED` | `PROTOTYPE_ASSUMPTION` | `UNKNOWN`)
- `source` (Railway manual, working timetable, or model tuning note)
- `notes` (Domain rationale and boundary explanation)

### Summary of Current Assumptions in `railway_rules.yaml`:
| Category | Rule Name | Status | Config Value | Domain Note |
|---|---|---|---|---|
| **Safety & Headway** | Block Release Headway Buffer | `PROTOTYPE_ASSUMPTION` | 3 min | Time between block release and first signal clearance. |
| **Safety & Headway** | TRD Power Block Isolation Margin | `PROTOTYPE_ASSUMPTION` | 10 min | OHE de-energization, earthing, permit-to-work overhead. |
| **Safety & Headway** | Default Caution Order Speed | `VALIDATED` | 30 km/h | Post-tamping speed restriction per IRPWM. |
| **Compatibility** | Multi-Department Co-Location | `PROTOTYPE_ASSUMPTION` | ENG+TRD+S&T+MECH | Shadow block synergy pairs on shared track possession. |
| **Compatibility** | Same Department Co-Location | `VALIDATED` | `false` | Two gangs from same dept cannot work at same km spot. |
| **Resources** | Heavy Machinery Exclusivity | `VALIDATED` | `true` | Tamping (CSM), Tower Wagon, DTS cannot double-book. |
| **Regulation** | Max Permissible Freight Holding | `PROTOTYPE_ASSUMPTION` | 240 min | Maximum loop siding holding time for freight rakes. |
| **Regulation** | Mail/Express Delay Cap | `VALIDATED` | 45 min | COA punctuality regulation ceiling for planned blocks. |
| **Regulation** | Premium (Vande Bharat/Rajdhani) Delay Cap | `VALIDATED` | 25 min | High-speed corridor punctuality directive. |
| **Weights** | Priority Multiplier & Urgency Bonuses | `PROTOTYPE_ASSUMPTION` | 2000 / 3000 / 1500 / 800 | Mathematical tuning for critical vs routine demand. |
| **Weights** | Shadow Block Synergy Bonus | `PROTOTYPE_ASSUMPTION` | 4000 pts | Incentive reward for bundling multi-department blocks. |
| **Weights** | Train Delay Penalties | `PROTOTYPE_ASSUMPTION` | 50 (Prem) / 20 (Exp) / 2 (Frt) | Delay penalty weights per minute. |
| **Block Windows** | Min / Max Block Duration | `VALIDATED` | 30 min / 480 min | Operational minimum and 8-hour mega-block ceiling. |
| **Restoration** | USFD Traffic Block Requirement | `PROTOTYPE_ASSUMPTION` | `false` | Ultrasonic flaw testing running without full closure. |
| **Restoration** | Electronic Interlocking Scope | `UNKNOWN` | `"TURNOUT_ONLY"` | Divisional variation on mainline vs turnout isolation. |
| **Restoration** | Emergency Possession Preemption | `VALIDATED` | `true` | Rail fracture/derailment overrides all timetables. |

### Solver & Constraints Hardcoded Values Inspection:
- **`backend/app/optimizer/constraints.py`**: All 14 operational parameters (headway, max delays, bonuses, penalties, section order, bypass list) are dynamically retrieved from `rules_loader.get_value()`. Zero hardcoded magic numbers.
- **`backend/app/optimizer/solver.py`**: Reads all constraints and weights exclusively through `self.constraint_mgr`. Zero duplicated hardcoded weights.

---

## 3. Duration Predictor Architecture Audit (Task 3)

The duration predictor component in [`backend/app/services/duration_predictor.py`](file:///a:/SHREYAS/RAILWAY%20BLOCK%20AI/backend/app/services/duration_predictor.py) was inspected and refactored into a clean, modular architecture:

1. **`BaseDurationPredictor` (Abstract Base Class)**:
   - Formally defines the contract: `predict(job_data, context) -> Dict[str, Any]`.
   - Returns structured prediction schema: `predictedDuration`, `lowerBound`, `upperBound`, `confidence`, `modelStatus`, `reasoning`.
2. **`DeterministicDurationPredictor` (Active Baseline)**:
   - Explicitly labeled as `modelStatus: "DETERMINISTIC_BASELINE"`.
   - Implements department base heuristics, urgency scaling, and section length adjustments.
   - Decoupled from machine learning frameworks (PyTorch, TensorFlow, Scikit-Learn).
3. **`MLDurationPredictorStub` (Future ML Model Slot)**:
   - Clear placeholder for future data-driven gradient boosting models (XGBoost / LightGBM) trained on historical block execution logs.
4. **`DurationPredictionService` (Singleton Facade)**:
   - Enables the optimizer and REST API (`POST /api/maintenance/predict-duration`) to query predictions without coupling to a specific algorithm.
5. **Optimizer Consumption**:
   - `RailwayBlockOptimizer` in `solver.py` safely queries `duration_predictor.predict()` as a fallback when maintenance requests do not specify an explicit duration.

---

## 4. Test Suite Execution (Task 4)

The automated test suite was executed against the updated codebase:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: A:\SHREYAS\RAILWAY BLOCK AI

tests/test_api.py::test_health_endpoint PASSED                           [  2%]
tests/test_api.py::test_dashboard_summary PASSED                         [  5%]
tests/test_api.py::test_maintenance_requests_api PASSED                  [  8%]
tests/test_api.py::test_optimization_run_api PASSED                      [ 11%]
tests/test_api.py::test_gantt_timeline_api PASSED                        [ 14%]
tests/test_api.py::test_whatif_simulate_api PASSED                       [ 17%]
tests/test_api.py::test_reports_analytics_api PASSED                     [ 20%]
tests/test_deterministic_scenario.py::test_deterministic_benchmark_optimization PASSED [ 23%]
tests/test_m2_integration.py::test_generate_plan_and_gantt PASSED        [ 26%]
tests/test_m2_integration.py::test_why_this_plan_scheduled PASSED        [ 29%]
tests/test_m2_integration.py::test_deferred_job_has_reason_code PASSED   [ 32%]
tests/test_m2_integration.py::test_train_delay_replan PASSED             [ 35%]
tests/test_m2_integration.py::test_block_unavailable_replan PASSED       [ 38%]
tests/test_m2_integration.py::test_kpi_changes_after_replan PASSED       [ 41%]
tests/test_m2_integration.py::test_rule_status_display PASSED            [ 44%]
tests/test_m2_integration.py::test_duration_predictor PASSED             [ 47%]
tests/test_optimizer.py::test_cp_sat_optimizer_feasibility PASSED        [ 50%]
tests/test_optimizer.py::test_shadow_block_pairing PASSED                [ 52%]
tests/test_optimizer.py::test_train_priority_deconfliction PASSED        [ 55%]
tests/test_stress_scenarios.py::test_scenario_1_no_feasible_window PASSED [ 58%]
tests/test_stress_scenarios.py::test_scenario_2_train_conflict PASSED    [ 61%]
tests/test_stress_scenarios.py::test_scenario_3_dependency PASSED        [ 64%]
tests/test_stress_scenarios.py::test_scenario_4_resource_conflict PASSED [ 67%]
tests/test_stress_scenarios.py::test_scenario_5_extended_maintenance PASSED [ 70%]
tests/test_stress_scenarios.py::test_scenario_6_block_unavailable PASSED [ 73%]
tests/test_stress_scenarios.py::test_scenario_7_department_compatibility PASSED [ 76%]
tests/test_stress_scenarios.py::test_scenario_8_high_density PASSED      [ 79%]
tests/test_stress_scenarios.py::test_scenario_9_suburban_high_frequency PASSED [ 82%]
tests/test_stress_scenarios.py::test_scenario_10_dynamic_replan PASSED   [ 85%]
tests/test_train_adapter.py::test_mock_train_provider PASSED             [ 88%]
tests/test_train_adapter.py::test_train_delay_normalization PASSED       [ 91%]
tests/test_train_adapter.py::test_live_provider_fallback_on_unconfigured_or_error PASSED [ 94%]
tests/test_train_adapter.py::test_train_data_adapter_automatic_fallback PASSED [ 97%]
tests/test_train_adapter.py::test_train_delay_simulation_via_adapter PASSED [100%]

====================== 34 passed, 129 warnings in 2.72s =======================
```

---

## 5. Conclusion & Readiness Checklist

- [x] All misleading system claims and unverified integration references removed.
- [x] `railway_rules.yaml` strictly conforms to the required 6-tuple schema with zero hardcoded solver duplicates.
- [x] Deterministic baseline duration predictor clearly separated from future ML interface.
- [x] 34/34 automated tests passing with 100% success.
- [x] Zero unauthorized live train APIs or fake AI implementations present.

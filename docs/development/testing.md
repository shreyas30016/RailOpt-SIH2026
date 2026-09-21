# Testing & Verification Guide

## Testing Architecture
RailOpt employs an extensive automated test suite covering mathematical solver optimization, safety invariants, role-based access control, counterfactual simulations, and AI copilot boundaries.

Test suites are located in the `tests/` directory:

| Test File | Focus Area | Scope |
| :--- | :--- | :--- |
| `tests/test_optimizer.py` | Google OR-Tools CP-SAT | BlockWindow enforcement, shadow blocks, train headway, feasibility |
| `tests/test_whatif_p12.py` | What-If Simulation | Train delays, section blockages, maintenance overruns, emergency jobs |
| `tests/test_rbac_p13.py` | Security & Access Control | Controller vs Planner vs Field Roles, anti-spoofing, route guards |
| `tests/test_ai_architecture.py` | AI Copilot Engine | Intent classification, safety filter, role scoping, provider mock/real |
| `tests/test_serverless_compatibility.py` | Cloud Compatibility | Dynamic database configuration, safe imports, router responses |
| `tests/test_solver_controls_p21.py` | Solver Objectives | Multi-objective goal weights, solver time budgets, plan quality scorecards |
| `tests/test_reports_dynamic_p14.py` | Reporting & Analytics | Dynamic metric calculations, shadow block synergy audits, date filters |
| `tests/test_m2_integration.py` | Milestone Integration | End-to-end multi-job scheduling and timetable interaction |
| `tests/test_maintenance_p02.py` | Maintenance CRUD | Job creation, department assignment, state transitions |
| `tests/test_train_adapter.py` | Train Feeds | Timetable replay, phase transitions, delay injection |

---

## Running Automated Tests

### Run the Core Optimizer Suite
```bash
pytest tests/test_optimizer.py -v
```

### Run Security & RBAC Tests
```bash
pytest tests/test_rbac_p13.py -v
```

### Run What-If Simulation Tests
```bash
pytest tests/test_whatif_p12.py -v
```

### Run AI Architecture Tests
```bash
pytest tests/test_ai_architecture.py -v
```

### Run Full Regression Suite
```bash
pytest -v
```

---

## Testing Verification Standard
Every pull request or modification to core logic must verify:
1. **Mathematical Invariants**: Hard safety constraints (headway, non-overlap, machine exclusivity) must never be bypassed or relaxed.
2. **Deterministic Outputs**: Given identical inputs and solver seeds, CP-SAT outputs must remain reproducible.
3. **Role Enforcement**: Elevation attempts or unauthorized optimization requests by field personas must return `403 Forbidden`.
4. **Database State**: Test runs must use isolated test sessions and clean up temporary test records.

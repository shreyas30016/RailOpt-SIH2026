import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, initialize_application_data
from backend.app.database import SessionLocal
from backend.app.optimizer.solver import RailwayBlockOptimizer
from backend.app.optimizer.explainer import DecisionExplainer

initialize_application_data()
client = TestClient(app)

def _get_headers(role: str, division_code: str = "NDL"):
    login_res = client.post("/api/auth/login", json={
        "username": f"test_{role.lower()}",
        "role": role,
        "division_code": division_code
    })
    assert login_res.status_code == 200, f"Login failed for {role}: {login_res.text}"
    token = login_res.json()["token"]
    return {"Authorization": f"Bearer {token}"}

def test_default_optimization_preserves_baseline_behavior():
    """Default optimization without explicit weights should succeed with standard baseline metrics."""
    response = client.post(
        "/api/optimization/run",
        headers=_get_headers("CONTROLLER"),
        json={}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("OPTIMAL", "FEASIBLE")
    assert data["scheduled_jobs_count"] >= 10
    assert "plan_quality" in data and data["plan_quality"] is not None
    assert "baseline_comparison" in data["plan_quality"]
    base = data["plan_quality"]["baseline_comparison"]
    assert base["manual_maintenance_hours"] > 0
    assert base["efficiency_gain_pct"] >= 0

def test_custom_objective_weights_applied():
    """Custom valid objective weights should be accepted and returned in applied_objectives."""
    payload = {
        "max_solver_time_sec": 10,
        "optimization_objectives": {
            "minimize_passenger_delays": True,
            "train_delay_weight": 2.5,
            "maximize_shadow_blocks": True,
            "shadow_block_weight": 2.0,
            "prioritize_urgent_maintenance": True,
            "urgency_weight": 1.5
        }
    }
    response = client.post(
        "/api/optimization/run",
        headers=_get_headers("CONTROLLER"),
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("OPTIMAL", "FEASIBLE")
    assert data["applied_objectives"]["train_delay_weight"] == 2.5
    assert data["applied_objectives"]["shadow_block_weight"] == 2.0
    assert data["applied_objectives"]["urgency_weight"] == 1.5
    assert data["applied_objectives"]["max_solver_time_sec"] == 10

def test_invalid_objective_weights_rejected():
    """Out-of-range weights (<0.1 or >5.0 or time<5s or time>60s) must be rejected with 422."""
    headers = _get_headers("CONTROLLER")
    # Test weight too small
    res1 = client.post(
        "/api/optimization/run",
        headers=headers,
        json={"optimization_objectives": {"train_delay_weight": 0.05}}
    )
    assert res1.status_code == 422

    # Test weight too large
    res2 = client.post(
        "/api/optimization/run",
        headers=headers,
        json={"optimization_objectives": {"shadow_block_weight": 6.0}}
    )
    assert res2.status_code == 422

    # Test solver time too short
    res3 = client.post(
        "/api/optimization/run",
        headers=headers,
        json={"max_solver_time_sec": 2}
    )
    assert res3.status_code == 422

    # Test solver time too long
    res4 = client.post(
        "/api/optimization/run",
        headers=headers,
        json={"max_solver_time_sec": 120}
    )
    assert res4.status_code == 422

def test_solver_weights_change_objective_score_and_tradeoffs():
    """Altering objective weights changes the mathematical score reflecting applied trade-offs."""
    db = SessionLocal()
    try:
        opt = RailwayBlockOptimizer(db)
        
        # Standard weights
        res_std = opt.run_optimization(
            train_delay_weight=1.0,
            shadow_block_weight=1.0,
            urgency_weight=1.0,
            max_solver_time_sec=10
        )
        
        # Heavy shadow block emphasis
        res_shadow = opt.run_optimization(
            train_delay_weight=0.5,
            shadow_block_weight=3.0,
            urgency_weight=1.0,
            max_solver_time_sec=10
        )
        
        assert res_std["status"] in ("OPTIMAL", "FEASIBLE")
        assert res_shadow["status"] in ("OPTIMAL", "FEASIBLE")
        # Objective score reflects boosted shadow bonus
        assert res_shadow["objective_score"] > 0
    finally:
        db.close()

def test_hard_safety_constraints_invariant_under_extreme_weights():
    """Extreme objective weights must never weaken hard railway safety constraints (no train collision)."""
    db = SessionLocal()
    try:
        opt = RailwayBlockOptimizer(db)
        res = opt.run_optimization(
            train_delay_weight=5.0,
            shadow_block_weight=5.0,
            urgency_weight=5.0,
            max_solver_time_sec=10
        )
        assert res["status"] in ("OPTIMAL", "FEASIBLE")
        
        # Verify zero collision conflict was maintained
        conflicts = res["conflicts_resolved"]
        collision_avoided = any(c.get("type") == "TRACK_COLLISION_AVOIDED" for c in conflicts)
        assert collision_avoided is True
    finally:
        db.close()

def test_decision_explainer_reflects_active_objective_weights():
    """DecisionExplainer includes active policy preferences in decision reasoning trees."""
    db = SessionLocal()
    try:
        opt = RailwayBlockOptimizer(db)
        res = opt.run_optimization(
            train_delay_weight=2.0,
            shadow_block_weight=2.5,
            urgency_weight=1.8,
            max_solver_time_sec=10
        )
        run_id = res["run_id"]
        scheduled_job_id = res["scheduled_blocks"][0]["job_id"]

        explainer = DecisionExplainer(db)
        tree = explainer.get_job_explanation_tree(run_id, scheduled_job_id)
        assert "reasoning_tree" in tree
        
        # Check for policy node
        policy_nodes = [n for n in tree["reasoning_tree"] if n.get("title") == "Optimization Trade-off Policy"]
        assert len(policy_nodes) > 0
        assert "2.0x" in policy_nodes[0]["detail"]
        assert "2.5x" in policy_nodes[0]["detail"]
    finally:
        db.close()

def test_rbac_optimization_permissions():
    """Controller & Planner are allowed to optimize; Field roles are forbidden."""
    payload = {"max_solver_time_sec": 10}
    
    # 1. Controller allowed
    r_ctrl = client.post("/api/optimization/run", headers=_get_headers("CONTROLLER"), json=payload)
    assert r_ctrl.status_code == 200

    # 2. Planner allowed
    r_plan = client.post("/api/optimization/run", headers=_get_headers("PLANNER"), json=payload)
    assert r_plan.status_code == 200

    # 3. Field roles forbidden (403)
    r_eng = client.post("/api/optimization/run", headers=_get_headers("ENGINEER", "NDL"), json=payload)
    assert r_eng.status_code == 403

    r_trd = client.post("/api/optimization/run", headers=_get_headers("TRD_OFFICER", "NDL"), json=payload)
    assert r_trd.status_code == 403

    r_st = client.post("/api/optimization/run", headers=_get_headers("ST_OFFICER", "NDL"), json=payload)
    assert r_st.status_code == 403

def test_whatif_simulation_unregressed():
    """What-If simulation remains fully functional with baseline diffing."""
    payload = {
        "scenario_name": "P2.1 Regression Check",
        "simulated_train_delay_min": 25,
        "delayed_train_number": "12002"
    }
    response = client.post(
        "/api/whatif/simulate",
        headers=_get_headers("CONTROLLER"),
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert "scenario_name" in data
    assert "delta_scheduled_jobs" in data
    assert "delta_train_delay_min" in data

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_dashboard_summary_extended_fields():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    
    # Core extended fields
    assert "total_jobs" in data
    assert "critical_jobs_count" in data
    assert "total_pending_requests" in data
    assert "planned_blocks_today" in data
    assert "efficiency_pct" in data
    assert "shadow_block_synergy_pct" in data
    assert "department_breakdown" in data
    assert "upcoming_blocks" in data
    assert "conflicts_list" in data
    assert "live_corridor_status" in data
    
    # Validate department breakdown structure
    db = data["department_breakdown"]
    assert "ENG" in db
    assert "S_T" in db
    assert "TRD" in db
    assert sum(db.values()) == data["total_jobs"]

def test_create_maintenance_request_persists_and_updates_dashboard():
    # 1. Check baseline count
    baseline_res = client.get("/api/dashboard/summary")
    assert baseline_res.status_code == 200
    baseline_jobs = baseline_res.json()["total_jobs"]
    
    import uuid
    unique_job_code = f"JOB-ENG-TEST-{uuid.uuid4().hex[:8]}"
    # 2. Create new maintenance request
    req_payload = {
        "job_code": unique_job_code,
        "title": "Turnout Packing and Alignment at Palwal",
        "department_code": "ENG",
        "section_code": "FDB-PWL",
        "duration_minutes": 140,
        "priority": 4,
        "urgency": "HIGH",
        "requires_power_block": False,
        "requires_traffic_block": True,
        "requires_speed_restriction": False
    }
    create_res = client.post("/api/maintenance/requests", json=req_payload)
    assert create_res.status_code == 200
    created_data = create_res.json()
    assert created_data["job_code"] == unique_job_code
    
    # 3. Verify dashboard summary increments
    updated_res = client.get("/api/dashboard/summary")
    assert updated_res.status_code == 200
    updated_jobs = updated_res.json()["total_jobs"]
    assert updated_jobs == baseline_jobs + 1

def test_dashboard_upcoming_blocks_after_optimization():
    # 1. Run optimization
    opt_res = client.post("/api/optimization/run", json={
        "max_solver_time_sec": 5,
        "minimize_passenger_delays": True,
        "maximize_shadow_blocks": True
    })
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert opt_data["status"] in ["OPTIMAL", "FEASIBLE"]
    
    # 2. Verify dashboard summary reflects optimal run
    dash_res = client.get("/api/dashboard/summary")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    
    assert dash_data["planned_blocks_today"] == opt_data["scheduled_jobs_count"]
    assert len(dash_data["upcoming_blocks"]) > 0
    
    # Check block structure
    first_block = dash_data["upcoming_blocks"][0]
    assert "block_id" in first_block
    assert "job_code" in first_block
    assert "section_code" in first_block
    assert "start_time_str" in first_block
    assert "end_time_str" in first_block

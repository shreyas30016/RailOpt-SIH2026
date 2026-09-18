import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_pending_requests" in data
    assert "efficiency_pct" in data
    assert "urgent_queue" in data

def test_maintenance_requests_api():
    response = client.get("/api/maintenance/requests")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) > 0
    assert "job_code" in jobs[0]

def test_optimization_run_api():
    response = client.post("/api/optimization/run", json={
        "max_solver_time_sec": 10,
        "minimize_passenger_delays": True,
        "maximize_shadow_blocks": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["OPTIMAL", "FEASIBLE"]
    assert data["scheduled_jobs_count"] > 0

def test_gantt_timeline_api():
    response = client.get("/api/gantt/timeline")
    assert response.status_code == 200
    data = response.json()
    assert "tracks" in data
    assert "trains" in data
    assert len(data["tracks"]) > 0

def test_whatif_simulate_api():
    response = client.post("/api/whatif/simulate", json={
        "scenario_name": "Emergency Broken Rail Incident",
        "emergency_job": {
            "job_code": "JOB-TEST-EMERGENCY",
            "title": "Emergency Broken Rail Repair",
            "department_code": "ENG",
            "section_code": "FDB-PWL",
            "duration_minutes": 150,
            "requires_power_block": False,
            "requires_traffic_block": True,
            "requires_speed_restriction": True,
            "priority": 5,
            "urgency": "CRITICAL"
        },
        "simulated_train_delay_min": 15
    })
    assert response.status_code == 200
    data = response.json()
    assert "delta_scheduled_jobs" in data
    assert "delta_train_delay_min" in data
    assert "critical_alerts" in data

def test_reports_analytics_api():
    response = client.get("/api/reports/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "department_statistics" in data
    assert "section_statistics" in data
    assert "historical_optimization_runs" in data

    kpis = data["kpis"]
    assert "block_utilization_pct" in kpis
    assert "job_completion_rate_pct" in kpis
    assert "mean_delay_per_block_min" in kpis
    assert "safety_compliance_pct" in kpis

    # Validate department stats
    dept_stats = data["department_statistics"]
    assert len(dept_stats) > 0
    assert "requested_hours" in dept_stats[0]
    assert "approved_hours" in dept_stats[0]

    # Validate section stats
    sec_stats = data["section_statistics"]
    assert len(sec_stats) > 0
    assert "completion_rate" in sec_stats[0]

    # Test filtered queries
    res_dept = client.get("/api/reports/analytics?department=ENG")
    assert res_dept.status_code == 200
    assert "kpis" in res_dept.json()

    res_sec = client.get("/api/reports/analytics?section=NDLS-TKD")
    assert res_sec.status_code == 200
    assert "kpis" in res_sec.json()


def test_auth_login_roles_and_divisions():
    # Test 1: Central Railway + Controller
    res_cr = client.post("/api/auth/login", json={
        "username": "Deshmukh",
        "role": "CONTROLLER",
        "division_code": "CR"
    })
    assert res_cr.status_code == 200
    p_cr = res_cr.json()["user_profile"]
    assert p_cr["division_name"] == "Central Railway — Mumbai CST Division"
    assert p_cr["role"] == "CONTROLLER"
    assert p_cr["initial"] == "C"

    # Test 2: Western Railway + TRD Officer
    res_wr = client.post("/api/auth/login", json={
        "username": "Mehta",
        "role": "TRD_OFFICER",
        "division_code": "WR"
    })
    assert res_wr.status_code == 200
    p_wr = res_wr.json()["user_profile"]
    assert p_wr["division_name"] == "Western Railway — Mumbai Central Division"
    assert p_wr["role"] == "TRD_OFFICER"
    assert p_wr["initial"] == "T"

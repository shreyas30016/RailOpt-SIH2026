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

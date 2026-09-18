import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.models import BlockWindow, Section

client = TestClient(app)

def test_whatif_train_delay_simulation():
    payload = {
        "scenario_name": "Test Train Delay Scenario",
        "delayed_train_number": "12050",
        "simulated_train_delay_min": 30
    }
    res = client.post("/api/whatif/simulate", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert "baseline_blocks" in data
    assert "new_blocks" in data
    assert "delta_train_delay_min" in data
    assert "delta_scheduled_jobs" in data
    assert "delta_utilization_pct" in data
    assert "critical_alerts" in data
    assert "impact_summary" in data
    assert len(data["baseline_blocks"]) > 0
    assert len(data["new_blocks"]) > 0

def test_whatif_section_unavailable_simulation():
    payload = {
        "scenario_name": "Test Section Blockage",
        "blocked_section_code": "FDB-PWL"
    }
    res = client.post("/api/whatif/simulate", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert "baseline_blocks" in data
    assert "new_blocks" in data
    assert "critical_alerts" in data
    assert any(block["section_code"] == "FDB-PWL" for block in data["baseline_blocks"])
    assert not any(block["section_code"] == "FDB-PWL" for block in data["new_blocks"])

    # What-If restores the baseline persisted-window state after the scenario.
    db = SessionLocal()
    try:
        section = db.query(Section).filter_by(code="FDB-PWL").one()
        assert all(
            window.is_active
            for window in db.query(BlockWindow).filter_by(section_id=section.id).all()
        )
    finally:
        db.close()

def test_whatif_maintenance_overrun_simulation():
    payload = {
        "scenario_name": "Test Maintenance Overrun",
        "blocked_section_code": "JOB-ENG-101",
        "block_duration_extra_min": 60
    }
    res = client.post("/api/whatif/simulate", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert "baseline_blocks" in data
    assert "new_blocks" in data
    assert "impact_summary" in data

def test_whatif_emergency_job_injection():
    payload = {
        "scenario_name": "Test Emergency Rail Fracture",
        "emergency_job": {
            "job_code": "JOB-EMG-TEST-99",
            "title": "Emergency Rail Fracture Repair",
            "department_code": "ENG",
            "section_code": "FDB-PWL",
            "duration_minutes": 120,
            "priority": 5,
            "urgency": "CRITICAL",
            "requires_power_block": False,
            "requires_traffic_block": True,
            "requires_speed_restriction": True,
            "speed_restriction_kmh": 30
        }
    }
    res = client.post("/api/whatif/simulate", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert "baseline_blocks" in data
    assert "new_blocks" in data
    assert any("Emergency job" in alert for alert in data.get("critical_alerts", []))

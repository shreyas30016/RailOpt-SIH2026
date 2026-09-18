import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_create_maintenance_request_valid():
    unique_code = f"JOB-TEST-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "job_code": unique_code,
        "title": "Turnout Overhaul & Switch Replacement",
        "department_code": "ENG",
        "section_code": "FDB-PWL",
        "track_line": "UP_MAIN",
        "duration_minutes": 180,
        "priority": 4,
        "urgency": "HIGH",
        "requires_power_block": False,
        "requires_traffic_block": True,
        "requires_speed_restriction": True,
        "speed_restriction_kmh": 30,
        "requested_date": "2026-09-01",
        "earliest_start_minute": 60,
        "latest_end_minute": 360,
        "description": "P0.2 test Turnout Overhaul on UP line"
    }
    response = client.post("/api/maintenance/requests", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["job_code"] == unique_code
    assert data["department_code"] == "ENG"
    assert data["section_code"] == "FDB-PWL"
    assert data["status"] == "PENDING"
    assert data["duration_minutes"] == 180

    # Cleanup
    job_id = data["id"]
    client.delete(f"/api/maintenance/requests/{job_id}")

def test_create_maintenance_request_duplicate():
    unique_code = f"JOB-DUP-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "job_code": unique_code,
        "title": "First Creation",
        "department_code": "ENG",
        "section_code": "FDB-PWL",
        "duration_minutes": 120
    }
    r1 = client.post("/api/maintenance/requests", json=payload)
    assert r1.status_code == 200
    job_id = r1.json()["id"]

    # Second creation with identical job_code should return 400
    r2 = client.post("/api/maintenance/requests", json=payload)
    assert r2.status_code == 400
    assert "already exists" in r2.text

    # Cleanup
    client.delete(f"/api/maintenance/requests/{job_id}")

def test_create_maintenance_request_invalid_dept():
    payload = {
        "job_code": f"JOB-INV-{uuid.uuid4().hex[:6].upper()}",
        "title": "Invalid Dept Job",
        "department_code": "NON_EXISTENT_DEPT",
        "section_code": "FDB-PWL",
        "duration_minutes": 120
    }
    response = client.post("/api/maintenance/requests", json=payload)
    assert response.status_code == 400
    assert "Department 'NON_EXISTENT_DEPT' not found" in response.text

def test_create_maintenance_request_invalid_section():
    payload = {
        "job_code": f"JOB-INV-{uuid.uuid4().hex[:6].upper()}",
        "title": "Invalid Section Job",
        "department_code": "ENG",
        "section_code": "NON_EXISTENT_SECTION",
        "duration_minutes": 120
    }
    response = client.post("/api/maintenance/requests", json=payload)
    assert response.status_code == 400
    assert "Section 'NON_EXISTENT_SECTION' not found" in response.text

def test_update_and_delete_maintenance_request():
    unique_code = f"JOB-TEMP-{uuid.uuid4().hex[:6].upper()}"
    # 1. Create temporary job
    payload = {
        "job_code": unique_code,
        "title": "Temporary Test Job",
        "department_code": "TRD",
        "section_code": "NDLS-TKD",
        "duration_minutes": 90
    }
    res = client.post("/api/maintenance/requests", json=payload)
    assert res.status_code == 200
    job = res.json()
    job_id = job["id"]

    # 2. Update status to APPROVED
    update_res = client.put(f"/api/maintenance/requests/{job_id}", json={"status": "APPROVED"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "APPROVED"

    # 3. Update status to DEFERRED
    defer_res = client.put(f"/api/maintenance/requests/{job_id}", json={"status": "DEFERRED"})
    assert defer_res.status_code == 200
    assert defer_res.json()["status"] == "DEFERRED"

    # 4. Delete request
    delete_res = client.delete(f"/api/maintenance/requests/{job_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["status"] == "deleted"

    # 5. Confirm deletion from list
    all_res = client.get("/api/maintenance/requests")
    assert all_res.status_code == 200
    remaining_codes = [j["job_code"] for j in all_res.json()]
    assert unique_code not in remaining_codes

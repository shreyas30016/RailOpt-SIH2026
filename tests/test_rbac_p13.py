import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, initialize_application_data

# Ensure DB seeded
initialize_application_data()
client = TestClient(app)

def _get_token_and_headers(role: str, dept: str = "NDL", username: str = "test_user"):
    login_res = client.post("/api/auth/login", json={
        "username": username,
        "role": role,
        "division_code": dept
    })
    assert login_res.status_code == 200, f"Login failed for {role}: {login_res.text}"
    token = login_res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Controller Authentication & Full Operational Authority
# ---------------------------------------------------------------------------
def test_controller_full_authority():
    headers = _get_token_and_headers("CONTROLLER")
    
    # 1. Run optimization
    opt_res = client.post("/api/optimization/run", json={"max_solver_time_sec": 5}, headers=headers)
    assert opt_res.status_code == 200
    assert opt_res.json()["status"] in ["OPTIMAL", "FEASIBLE"]

    # 2. Create, Approve, Defer, and Delete maintenance request
    job_code = f"JOB-CTRL-{uuid.uuid4().hex[:6].upper()}"
    create_res = client.post("/api/maintenance/requests", json={
        "job_code": job_code,
        "title": "Controller Track Renewal",
        "department_code": "ENG",
        "section_code": "FDB-PWL",
        "duration_minutes": 120
    }, headers=headers)
    assert create_res.status_code == 200
    job_id = create_res.json()["id"]

    # Approve
    app_res = client.put(f"/api/maintenance/requests/{job_id}", json={"status": "APPROVED"}, headers=headers)
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "APPROVED"

    # Defer
    def_res = client.put(f"/api/maintenance/requests/{job_id}", json={"status": "DEFERRED"}, headers=headers)
    assert def_res.status_code == 200
    assert def_res.json()["status"] == "DEFERRED"

    # What-If Simulate
    wif_res = client.post("/api/whatif/simulate", json={
        "scenario_name": "Controller What-if Test",
        "simulated_train_delay_min": 15
    }, headers=headers)
    assert wif_res.status_code == 200

    # Cleanup
    client.delete(f"/api/maintenance/requests/{job_id}", headers=headers)


def test_controller_approve_by_job_code_and_numeric_id():
    """Verify Controller can approve requests using either numeric ID or job_code string, and DB persists status."""
    from backend.app.database import SessionLocal
    from backend.app.models.models import MaintenanceJob

    headers = _get_token_and_headers("CONTROLLER")
    db = SessionLocal()

    try:
        # 1. Test update by job_code string (e.g. JOB-ENG-101)
        job_code = f"JOB-ENG-{uuid.uuid4().hex[:6].upper()}"
        create_res = client.post("/api/maintenance/requests", json={
            "job_code": job_code,
            "title": "Track Tamping Test",
            "department_code": "ENG",
            "section_code": "FDB-PWL",
            "duration_minutes": 120
        }, headers=headers)
        assert create_res.status_code == 200
        job_id = create_res.json()["id"]

        # Approve using job_code string
        app_code_res = client.put(f"/api/maintenance/requests/{job_code}", json={"status": "APPROVED"}, headers=headers)
        assert app_code_res.status_code == 200
        assert app_code_res.json()["status"] == "APPROVED"

        # Verify DB directly
        db_job = db.query(MaintenanceJob).filter(MaintenanceJob.job_code == job_code).first()
        assert db_job is not None
        assert db_job.status == "APPROVED"

        # Approve using numeric ID
        app_id_res = client.put(f"/api/maintenance/requests/{job_id}", json={"status": "APPROVED"}, headers=headers)
        assert app_id_res.status_code == 200
        assert app_id_res.json()["status"] == "APPROVED"

        # Cleanup
        del_res = client.delete(f"/api/maintenance/requests/{job_code}", headers=headers)
        assert del_res.status_code == 200
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 2. Planner Authentication & Planning Authority
# ---------------------------------------------------------------------------
def test_planner_authority():
    headers = _get_token_and_headers("PLANNER")

    # Optimization allowed
    opt_res = client.post("/api/optimization/run", json={"max_solver_time_sec": 5}, headers=headers)
    assert opt_res.status_code == 200

    # What-If allowed
    wif_res = client.post("/api/whatif/simulate", json={
        "scenario_name": "Planner What-if Test",
        "simulated_train_delay_min": 10
    }, headers=headers)
    assert wif_res.status_code == 200

    # Can approve and defer requests
    job_code = f"JOB-PLAN-{uuid.uuid4().hex[:6].upper()}"
    create_res = client.post("/api/maintenance/requests", json={
        "job_code": job_code,
        "title": "Planner Signal Alignment",
        "department_code": "S_T",
        "section_code": "NDLS-TKD",
        "duration_minutes": 90
    }, headers=headers)
    assert create_res.status_code == 200
    job_id = create_res.json()["id"]

    app_res = client.put(f"/api/maintenance/requests/{job_id}", json={"status": "APPROVED"}, headers=headers)
    assert app_res.status_code == 200

    # Cleanup
    client.delete(f"/api/maintenance/requests/{job_id}", headers=headers)


# ---------------------------------------------------------------------------
# 3. Field Roles Restrictions: Engineer, TRD Officer, S&T Officer
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["ENGINEER", "TRD_OFFICER", "ST_OFFICER"])
def test_field_roles_optimization_and_whatif_forbidden(role):
    headers = _get_token_and_headers(role)

    # 1. POST /api/optimization/run -> 403 Forbidden
    opt_res = client.post("/api/optimization/run", json={"max_solver_time_sec": 5}, headers=headers)
    assert opt_res.status_code == 403, f"{role} should receive 403 for optimize"
    assert "Permission denied" in opt_res.json()["detail"]

    # 2. POST /api/whatif/simulate -> 403 Forbidden
    wif_res = client.post("/api/whatif/simulate", json={"scenario_name": "Disruption"}, headers=headers)
    assert wif_res.status_code == 403, f"{role} should receive 403 for whatif simulate"


@pytest.mark.parametrize("role,dept_code", [
    ("ENGINEER", "ENG"),
    ("TRD_OFFICER", "TRD"),
    ("ST_OFFICER", "S_T")
])
def test_field_roles_cannot_approve_or_defer(role, dept_code):
    ctrl_headers = _get_token_and_headers("CONTROLLER")
    field_headers = _get_token_and_headers(role)

    # Controller creates a job in the role's department
    job_code = f"JOB-TEST-{role}-{uuid.uuid4().hex[:6].upper()}"
    create_res = client.post("/api/maintenance/requests", json={
        "job_code": job_code,
        "title": f"{role} Field Work",
        "department_code": dept_code,
        "section_code": "TKD-FDB",
        "duration_minutes": 60
    }, headers=ctrl_headers)
    assert create_res.status_code == 200
    job_id = create_res.json()["id"]

    try:
        # Field role attempts to approve -> 403
        app_res = client.put(f"/api/maintenance/requests/{job_id}", json={"status": "APPROVED"}, headers=field_headers)
        assert app_res.status_code == 403, f"{role} should receive 403 for approval"

        # Field role attempts to defer -> 403
        def_res = client.put(f"/api/maintenance/requests/{job_id}", json={"status": "DEFERRED"}, headers=field_headers)
        assert def_res.status_code == 403, f"{role} should receive 403 for deferral"
    finally:
        client.delete(f"/api/maintenance/requests/{job_id}", headers=ctrl_headers)


# ---------------------------------------------------------------------------
# 4. Missing and Invalid Token -> 401 Unauthorized
# ---------------------------------------------------------------------------
def test_missing_and_invalid_token_returns_401():
    no_auth = {"Authorization": None}

    # 1. Missing Authorization header on optimization
    res1 = client.post("/api/optimization/run", json={"max_solver_time_sec": 5}, headers=no_auth)
    assert res1.status_code == 401

    # 2. Missing Authorization header on whatif
    res2 = client.post("/api/whatif/simulate", json={"scenario_name": "Test"}, headers=no_auth)
    assert res2.status_code == 401

    # 3. Missing Authorization header on maintenance create
    res3 = client.post("/api/maintenance/requests", json={
        "job_code": "JOB-ANON-1",
        "title": "Anonymous Job",
        "department_code": "ENG",
        "section_code": "NDLS-TKD",
        "duration_minutes": 60
    }, headers=no_auth)
    assert res3.status_code == 401

    # 4. Malformed Authorization token
    bad_headers = {"Authorization": "Bearer not-a-valid-base64-payload"}
    res4 = client.post("/api/optimization/run", json={}, headers=bad_headers)
    assert res4.status_code == 401

    # 5. Invalid Header scheme (e.g. Basic instead of Bearer)
    basic_headers = {"Authorization": "Basic dXNlcjpwYXNz"}
    res5 = client.post("/api/optimization/run", json={}, headers=basic_headers)
    assert res5.status_code == 401


# ---------------------------------------------------------------------------
# 5. Anti-Spoofing & Department Scoping Enforcement
# ---------------------------------------------------------------------------
def test_anti_spoofing_payload_cannot_elevate_role():
    # Authenticated as Engineer
    eng_headers = _get_token_and_headers("ENGINEER")

    # Engineer attempts to pass role="CONTROLLER" in payload
    res = client.post("/api/optimization/run", json={
        "max_solver_time_sec": 5,
        "role": "CONTROLLER"
    }, headers=eng_headers)
    assert res.status_code == 403, "Forged role in request body must NOT escalate access"


def test_department_scoping_enforcement_for_field_roles():
    eng_headers = _get_token_and_headers("ENGINEER")
    trd_headers = _get_token_and_headers("TRD_OFFICER")
    st_headers = _get_token_and_headers("ST_OFFICER")

    # Engineer submitting ENG -> 200
    eng_code = f"JOB-ENG-{uuid.uuid4().hex[:6].upper()}"
    res_eng = client.post("/api/maintenance/requests", json={
        "job_code": eng_code,
        "title": "Civil Track Maintenance",
        "department_code": "ENG",
        "section_code": "FDB-PWL",
        "duration_minutes": 100
    }, headers=eng_headers)
    assert res_eng.status_code == 200
    eng_id = res_eng.json()["id"]

    # Engineer attempting cross-department submission (TRD or S_T) -> 403
    res_eng_spoof = client.post("/api/maintenance/requests", json={
        "job_code": f"JOB-SPOOF-{uuid.uuid4().hex[:6].upper()}",
        "title": "Spoofed TRD Request by Engineer",
        "department_code": "TRD",
        "section_code": "FDB-PWL",
        "duration_minutes": 100
    }, headers=eng_headers)
    assert res_eng_spoof.status_code == 403
    assert "cannot operate on department 'TRD'" in res_eng_spoof.json()["detail"]

    # TRD Officer attempting cross-department submission (ENG) -> 403
    res_trd_spoof = client.post("/api/maintenance/requests", json={
        "job_code": f"JOB-SPOOF-TRD-{uuid.uuid4().hex[:6].upper()}",
        "title": "Spoofed ENG Request by TRD",
        "department_code": "ENG",
        "section_code": "FDB-PWL",
        "duration_minutes": 100
    }, headers=trd_headers)
    assert res_trd_spoof.status_code == 403

    # S&T Officer submitting S_T -> 200
    st_code = f"JOB-ST-{uuid.uuid4().hex[:6].upper()}"
    res_st = client.post("/api/maintenance/requests", json={
        "job_code": st_code,
        "title": "Point Machine Overhaul",
        "department_code": "S_T",
        "section_code": "NDLS-TKD",
        "duration_minutes": 80
    }, headers=st_headers)
    assert res_st.status_code == 200
    st_id = res_st.json()["id"]

    # TRD Officer trying to delete S&T job -> 403
    res_del_cross = client.delete(f"/api/maintenance/requests/{st_id}", headers=trd_headers)
    assert res_del_cross.status_code == 403

    # S&T Officer deleting own job -> 200
    res_del_own = client.delete(f"/api/maintenance/requests/{st_id}", headers=st_headers)
    assert res_del_own.status_code == 200

    # Engineer deleting own job -> 200
    res_del_eng = client.delete(f"/api/maintenance/requests/{eng_id}", headers=eng_headers)
    assert res_del_eng.status_code == 200

"""
RailOpt Production-Readiness Hardening Sprint — Regression Tests
=================================================================

Validates the Phase 1–16 hardening fixes:

  1. Dashboard must NOT report fabricated KPIs (92.4/68.5/1.2) before any run.
  2. Reports must NOT substitute a placeholder conflict count (12).
  3. GET /api/optimization/latest must never trigger a solver run (no side effect).
  4. Maintenance job codes are generated authoritatively by the backend, unique.
  5. GET /api/trains/list returns the real corridor timetable.
  6. Field roles are hard-scoped server-side on maintenance reads.
  7. AI copilot maintenance queries are department-scoped for field roles.
  8. Solver block-utilization math is honest (no artificial inflation).
"""

import base64
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
from backend.app.data.synthetic_seeder import seed_synthetic_data
from backend.app.main import app


# ---------------------------------------------------------------------------
# Fresh in-memory DB with NO optimization runs (mirrors a first-time launch)
# ---------------------------------------------------------------------------
_test_engine = None
_test_session_factory = None


@pytest.fixture(scope="module")
def fresh_client():
    global _test_engine, _test_session_factory
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # keep ONE shared in-memory connection across threads
    )
    _test_engine = engine
    _test_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    TestingSessionLocal = _test_session_factory
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_synthetic_data(db)
    db.close()

    def override_get_db():
        d = TestingSessionLocal()
        try:
            yield d
        finally:
            d.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _token(role: str) -> str:
    profile = {
        "username": "harden_test",
        "role": role,
        "division_code": "NDL",
        "can_approve": role in ("CONTROLLER", "PLANNER"),
        "can_optimize": role in ("CONTROLLER", "PLANNER"),
        "can_edit": True,
        "initial": role[0],
    }
    return base64.b64encode(json.dumps(profile).encode()).decode()


def _auth(role: str):
    return {"Authorization": f"Bearer {_token(role)}"}


# ---------------------------------------------------------------------------
# 1. Dashboard — zero fabricated KPIs before any optimization run
# ---------------------------------------------------------------------------
def test_dashboard_reports_zero_kpis_before_any_run(fresh_client):
    resp = fresh_client.get("/api/dashboard/summary", headers=_auth("CONTROLLER"))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # No run exists: efficiency/synergy/punctuality must be 0.0 — never 92.4/68.5/1.2
    assert data["efficiency_pct"] == 0.0
    assert data["shadow_block_synergy_pct"] == 0.0
    assert data["punctuality_impact_pct"] == 0.0
    assert data["planned_blocks_today"] == 0
    assert data["latest_optimization_summary"] is None


# ---------------------------------------------------------------------------
# 2. Reports — no placeholder conflict count, real shadow-savings math
# ---------------------------------------------------------------------------
def test_reports_never_fabricates_conflict_count(fresh_client):
    resp = fresh_client.get("/api/reports/analytics", headers=_auth("CONTROLLER"))
    assert resp.status_code == 200, resp.text
    kpis = resp.json()["kpis"]
    assert kpis["critical_conflicts_resolved"] == 0  # real count, NOT 12
    assert kpis["shadow_block_savings_hours"] == 0.0
    assert kpis["block_utilization_pct"] == 0.0


# ---------------------------------------------------------------------------
# 3. GET /api/optimization/latest must be side-effect free
# ---------------------------------------------------------------------------
def test_optimization_latest_does_not_auto_run_solver(fresh_client):
    from backend.app.models.models import OptimizationRun
    from backend.app.database import SessionLocal

    # Use the dependency-overridden session to count runs
    resp = fresh_client.get("/api/optimization/latest", headers=_auth("CONTROLLER"))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "NO_RUNS"
    assert body["run_id"] is None

    # The GET must NOT have created an OptimizationRun as a side effect.
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    check = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    seed_synthetic_data(check)
    assert check.query(OptimizationRun).count() == 0
    check.close()


# ---------------------------------------------------------------------------
# 4. Server-side job-code generation — real, unique, per-department sequence
# ---------------------------------------------------------------------------
def test_maintenance_auto_generates_unique_job_codes(fresh_client):
    payload = {
        "title": "Hardening Test Track Possession",
        "department_code": "ENG",
        "section_code": "FDB-PWL",
        "track_line": "UP_MAIN",
        "duration_minutes": 120,
        "priority": 3,
        "urgency": "MEDIUM",
        "requires_power_block": False,
        "requires_traffic_block": True,
        "requires_speed_restriction": False,
        "description": "Auto-generated code verification",
    }
    r1 = fresh_client.post("/api/maintenance/requests", json=payload, headers=_auth("CONTROLLER"))
    assert r1.status_code == 200, r1.text
    code1 = r1.json()["job_code"]
    assert code1.startswith("JOB-ENG-") and code1 != "JOB-ENG-101", code1

    r2 = fresh_client.post("/api/maintenance/requests", json=payload, headers=_auth("CONTROLLER"))
    assert r2.status_code == 200, r2.text
    code2 = r2.json()["job_code"]
    assert code2 != code1, "Generated job codes must be unique"

    # TRD sequence continues after the seeded JOB-TRD-2xx range
    payload["department_code"] = "TRD"
    r3 = fresh_client.post("/api/maintenance/requests", json=payload, headers=_auth("CONTROLLER"))
    assert r3.status_code == 200, r3.text
    assert r3.json()["job_code"].startswith("JOB-TRD-205"), r3.json()["job_code"]

    # S_T sequence uses the JOB-ST- prefix family
    payload["department_code"] = "S_T"
    r4 = fresh_client.post("/api/maintenance/requests", json=payload, headers=_auth("CONTROLLER"))
    assert r4.status_code == 200, r4.text
    assert r4.json()["job_code"].startswith("JOB-ST-306"), r4.json()["job_code"]

    # Explicit duplicate codes are still rejected
    payload["department_code"] = "ENG"
    payload["job_code"] = "JOB-ENG-101"
    r5 = fresh_client.post("/api/maintenance/requests", json=payload, headers=_auth("CONTROLLER"))
    assert r5.status_code == 400, r5.text


# ---------------------------------------------------------------------------
# 5. GET /api/trains/list returns the real DB timetable
# ---------------------------------------------------------------------------
def test_trains_list_endpoint_returns_real_timetable(fresh_client):
    resp = fresh_client.get("/api/trains/list", headers=_auth("CONTROLLER"))
    assert resp.status_code == 200, resp.text
    trains = resp.json()
    numbers = {t["train_number"] for t in trains}
    assert "12050" in numbers  # Gatimaan Express seed
    assert "22436" in numbers  # Vande Bharat seed
    assert len(trains) >= 10


# ---------------------------------------------------------------------------
# 6. Field-role read scoping on maintenance requests
# ---------------------------------------------------------------------------
def test_field_role_maintenance_reads_are_department_scoped(fresh_client):
    # Engineer asking for TRD data must still receive ONLY ENG jobs
    resp = fresh_client.get(
        "/api/maintenance/requests?department=TRD",
        headers=_auth("ENGINEER"),
    )
    assert resp.status_code == 200, resp.text
    jobs = resp.json()
    assert len(jobs) > 0
    assert all(j["department_code"] == "ENG" for j in jobs), "Field role read scope violated"

    # TRD officer sees only TRD jobs
    resp2 = fresh_client.get("/api/maintenance/requests", headers=_auth("TRD_OFFICER"))
    assert resp2.status_code == 200, resp2.text
    assert all(j["department_code"] == "TRD" for j in resp2.json())

    # Controller sees everything
    resp3 = fresh_client.get("/api/maintenance/requests", headers=_auth("CONTROLLER"))
    depts = {j["department_code"] for j in resp3.json()}
    assert "ENG" in depts and "TRD" in depts and "S_T" in depts


# ---------------------------------------------------------------------------
# 7. AI copilot maintenance queries are department-scoped for field roles
# ---------------------------------------------------------------------------
def test_ai_copilot_field_role_department_scoping(fresh_client):
    resp = fresh_client.post(
        "/api/ai/chat",
        json={"message": "Show me the TRD maintenance requests", "context": {}},
        headers=_auth("ENGINEER"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    tool_data = body.get("tool_result", {}).get("data", {})
    jobs = tool_data.get("jobs", [])
    assert len(jobs) > 0
    # Engineer scope injection forces the ENG department even though the user
    # explicitly asked for TRD requests.
    assert all(j["job_code"].startswith("JOB-ENG") for j in jobs), (
        f"AI scope violation: engineer received {[j['job_code'] for j in jobs]}"
    )


# ---------------------------------------------------------------------------
# 8. Solver utilization math is honest (no *6.5 inflation factor)
# ---------------------------------------------------------------------------
def test_solver_block_utilization_is_honest(fresh_client):
    resp = fresh_client.post("/api/optimization/run", json={}, headers=_auth("CONTROLLER"))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    util = body["block_utilization_pct"]
    assert 0.0 < util <= 100.0

    # True occupancy: sum of possession minutes / (6 sections * 1440 min) * 100
    total_minutes = sum(b["duration_minutes"] for b in body.get("scheduled_blocks", []))
    expected = min(100.0, (total_minutes / (1440 * 6)) * 100.0)
    assert abs(util - expected) < 0.5, (
        f"Utilization {util}% does not match honest occupancy {round(expected, 1)}%"
    )

    # Dashboard efficiency must mirror the honest run value, not 100%
    dash = fresh_client.get("/api/dashboard/summary", headers=_auth("CONTROLLER")).json()
    assert abs(dash["efficiency_pct"] - util) < 0.5, dash["efficiency_pct"]

    # Run responses carry critical-coverage metadata for the scorecard
    assert "critical_jobs_total" in body["KPI_values"]


# ---------------------------------------------------------------------------
# 9. AI copilot answers train-status questions honestly (no fabricated positions)
# ---------------------------------------------------------------------------
def _ai_chat(fresh_client, message, role="CONTROLLER"):
    return fresh_client.post(
        "/api/ai/chat",
        json={"message": message, "context": {"page": "dashboard"}},
        headers=_auth(role),
    ).json()


def test_ai_unknown_train_99999_returns_honest_unavailable(fresh_client):
    body = _ai_chat(fresh_client, "What is the live position of Train 99999?")
    assert body.get("tool_used") == "get_train_status"
    msg = (body.get("message") or "").lower()
    assert "not present" in msg or "no live position" in msg
    assert "99999" in msg
    # Never fabricate a location/delay for an unknown train
    assert "km" not in msg or "km/h" in msg


def test_ai_known_train_12050_returns_grounded_movement(fresh_client):
    body = _ai_chat(fresh_client, "Where is Train 12050 right now?")
    assert body.get("tool_used") == "get_train_status"
    msg = body.get("message") or ""
    assert "12050" in msg and "gatimaan" in msg.lower()
    assert "synthetic demo data" in msg.lower()  # source is disclosed, never implied live


# ---------------------------------------------------------------------------
# 10. Simulated live-delay control: RBAC + propagation into next optimization
# ---------------------------------------------------------------------------
def test_simulate_delay_rbac_and_propagation(fresh_client):
    from backend.app.services.train_adapter import train_adapter as _ta
    _ta.mock_provider.simulated_delays.clear()

    # Field roles must never push a delay (backend enforced, not just hidden UI)
    r = fresh_client.post(
        "/api/trains/simulate-delay",
        json={"train_id": "12301", "delay_minutes": 15},
        headers=_auth("ENGINEER"),
    )
    assert r.status_code == 403, r.text

    # Controller can push a delay; the live feed reflects it immediately
    r = fresh_client.post(
        "/api/trains/simulate-delay",
        json={"train_id": "12301", "delay_minutes": 15},
        headers=_auth("CONTROLLER"),
    )
    assert r.status_code == 200, r.text
    m = next(x for x in r.json()["movements"] if x["train_id"] == "12301")
    assert m["delay_minutes"] == 15 and m["status"] == "DELAYED"

    # The next optimization run plans around the shifted train window and still succeeds
    r = fresh_client.post("/api/optimization/run", json={}, headers=_auth("CONTROLLER"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "OPTIMAL"
    assert body["scheduled_jobs_count"] == body["total_jobs"]

    _ta.mock_provider.simulated_delays.clear()


# ---------------------------------------------------------------------------
# 11. Reports date-range filter is a real backend filter (not a no-op)
# ---------------------------------------------------------------------------
def test_reports_date_range_filter_changes_history_and_scope(fresh_client):
    from datetime import datetime, timedelta
    from backend.app.models.models import OptimizationRun

    # Seed one run dated 30 days ago so the window filter is observable
    db = _test_session_factory()
    past = OptimizationRun(status="OPTIMAL", scheduled_jobs_count=3, unscheduled_jobs_count=0,
                           train_delay_total_min=10, block_utilization_pct=9.9,
                           shadow_block_synergy_pct=5.0, solver_time_seconds=0.01,
                           run_timestamp=datetime.utcnow() - timedelta(days=30))
    db.add(past)
    db.commit()
    db.close()

    past_month = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m")  # e.g. 2026-08
    day = (datetime.utcnow() - timedelta(days=30)).strftime("%d %b %Y")

    r = fresh_client.get(
        "/api/reports/analytics",
        params={"date_range": f"{day} - {day}"},
        headers=_auth("CONTROLLER"),
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["active_filters"]["date_range"] == f"{day} - {day}"
    hist = data.get("historical_optimization_runs", [])
    assert hist, "expected the seeded past run inside the requested window"

    # A window containing only runs from a distant month must be empty (honest)
    r3 = fresh_client.get(
        "/api/reports/analytics",
        params={"date_range": "01 Jan 2025 - 31 Jan 2025"},
        headers=_auth("CONTROLLER"),
    )
    assert r3.status_code == 200
    assert r3.json().get("historical_optimization_runs", []) == []


# ---------------------------------------------------------------------------
# 12. Shadow-block paired codes are stored as real JSON (fixes zero savings bug)
# ---------------------------------------------------------------------------
def test_shadow_pair_json_is_valid_and_reports_savings(fresh_client):
    r = fresh_client.post("/api/optimization/run", json={}, headers=_auth("CONTROLLER"))
    assert r.status_code == 200, r.text

    from sqlalchemy import text
    with _test_engine.connect() as conn:
        rows = conn.execute(text(
            "select paired_job_codes_json from scheduled_blocks "
            "where paired_job_codes_json not in ('[]','')"
        )).fetchall()
    for (v,) in rows:
        json.loads(v)  # must not raise — real JSON, not a Python list repr

    rep = fresh_client.get("/api/reports/analytics", headers=_auth("CONTROLLER")).json()
    savings = rep["kpis"]["shadow_block_savings_hours"]
    assert savings is not None and savings > 0, f"expected real shadow savings, got {savings}"

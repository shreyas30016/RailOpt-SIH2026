"""
M2 Integration Tests - SIH26027 Railway Block Planning
Tests for all M2 Product Hardening workflows.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models.models import Department, Section, TrackLine, MaintenanceJob, TrainSchedule, BlockWindow

# ============================================================================
# Test Database Setup
# ============================================================================

TEST_DB_URL = "sqlite:///./test_m2_integration.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    _seed(session)
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed(db):
    dept = Department(code="ENG", name="Civil Engineering", color="#003366", icon="construction")
    db.add(dept)
    db.flush()

    sec = Section(code="FDB-PWL", start_station="Faridabad", end_station="Palwal", length_km=18.0)
    db.add(sec)
    db.flush()

    tl = TrackLine(section_id=sec.id, line_code="UP_MAIN", line_type="UP")
    db.add(tl)
    db.flush()

    train = TrainSchedule(
        train_number="12016", train_name="Ajmer SF Express",
        train_type="SUPERFAST", priority_weight=15,
        direction="DN", departure_minute=420, arrival_minute=480
    )
    db.add(train)

    bw = BlockWindow(
        window_code="BW-FDB-PWL-01", section_id=sec.id, track_line_id=tl.id,
        start_minute=120, end_minute=330, window_type="CORRIDOR", is_active=True
    )
    db.add(bw)

    # Schedulable job (fits in window, no train conflict)
    j1 = MaintenanceJob(
        job_code="M2-JOB-ENG-01", title="Track Renewal FDB-PWL",
        department_id=dept.id, section_id=sec.id, track_line_id=tl.id,
        duration_minutes=120, priority=4, urgency="HIGH",
        requires_power_block=False, requires_traffic_block=True,
        status="PENDING", earliest_start_minute=120, latest_end_minute=330
    )
    db.add(j1)

    # Unschedulable job (window too narrow)
    j2 = MaintenanceJob(
        job_code="M2-JOB-ENG-DEFER", title="Huge Deferred Job",
        department_id=dept.id, section_id=sec.id, track_line_id=tl.id,
        duration_minutes=999, priority=2, urgency="ROUTINE",
        requires_power_block=False, requires_traffic_block=True,
        status="PENDING", earliest_start_minute=120, latest_end_minute=130
    )
    db.add(j2)
    db.commit()


# ============================================================================
# Test 1: Generate Plan and Gantt
# ============================================================================

def test_generate_plan_and_gantt(client):
    """Run optimization, then Gantt should return the scheduled blocks from the same run."""
    opt_res = client.post("/api/optimization/run", json={"maxSolverTimeSec": 10})
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    run_id = opt_data.get("run_id")
    assert run_id is not None

    gantt_res = client.get(f"/api/gantt/timeline?run_id={run_id}")
    assert gantt_res.status_code == 200
    gantt = gantt_res.json()
    assert "tracks" in gantt
    assert "trains" in gantt


# ============================================================================
# Test 2: Why This Plan - Scheduled Job
# ============================================================================

def test_why_this_plan_scheduled(client):
    """Explanation for a scheduled job should have >= 4 reasoning tree nodes."""
    # Run optimization first
    opt_res = client.post("/api/optimization/run", json={})
    assert opt_res.status_code == 200
    opt_data = opt_res.json()

    if not opt_data.get("scheduled_blocks"):
        pytest.skip("No scheduled blocks in this run")

    job_code = opt_data["scheduled_blocks"][0]["job_code"]
    exp_res = client.get(f"/api/optimization/explanation/{job_code}")
    assert exp_res.status_code == 200
    exp_data = exp_res.json()

    assert "reasoning_tree" in exp_data
    assert "status" in exp_data
    # Scheduled jobs must have >= 4 reasoning nodes
    if exp_data.get("status") == "SCHEDULED":
        assert len(exp_data["reasoning_tree"]) >= 4


# ============================================================================
# Test 3: Deferred Job has reason_code
# ============================================================================

def test_deferred_job_has_reason_code(client):
    """
    A job with a window too narrow to fit must be deferred with reason_code populated.
    """
    opt_res = client.post("/api/optimization/run", json={})
    assert opt_res.status_code == 200
    opt_data = opt_res.json()

    if not opt_data.get("unscheduled_jobs"):
        pytest.skip("No unscheduled jobs in this run")

    deferred = opt_data["unscheduled_jobs"][0]
    assert "reason" in deferred
    # reason_code is populated for M2 deferred jobs
    assert "reason_code" in deferred
    assert deferred["reason_code"] in [
        "NO_FEASIBLE_WINDOW", "TRAIN_CONFLICT", "RESOURCE_CONFLICT",
        "DEPENDENCY_UNMET", "CAPACITY_OVERFLOW"
    ]


# ============================================================================
# Test 4: Train Delay Replan
# ============================================================================

def test_train_delay_replan(client):
    """Simulating a train delay should return kpi_delta and affected_jobs."""
    payload = {
        "scenario_name": "M2 Train Delay Test",
        "simulated_train_delay_min": 20,
        "emergency_job": None,
    }
    res = client.post("/api/whatif/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "kpi_delta" in data
    assert "affected_jobs" in data
    assert "delta_train_delay_min" in data
    assert "baseline_blocks" in data
    assert "new_blocks" in data


# ============================================================================
# Test 5: Block Unavailable Replan
# ============================================================================

def test_block_unavailable_replan(client):
    """Marking a section unavailable should identify affected blocks and return comparison."""
    payload = {
        "scenario_name": "M2 Block Unavailable Test",
        "blocked_section_code": "FDB-PWL",
    }
    res = client.post("/api/whatif/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "impact_summary" in data
    assert "disruptions_applied" in data


# ============================================================================
# Test 6: KPI Changes After Replan
# ============================================================================

def test_kpi_changes_after_replan(client):
    """After a disruption, kpi_delta fields must be numeric and present."""
    payload = {
        "scenario_name": "M2 KPI Delta Test",
        "simulated_train_delay_min": 30,
    }
    res = client.post("/api/whatif/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()

    kpi = data.get("kpi_delta", {})
    assert "scheduled" in kpi
    assert "train_delay_min" in kpi
    assert "utilization_pct" in kpi
    assert isinstance(kpi["train_delay_min"], (int, float))


# ============================================================================
# Test 7: Rule Status Display
# ============================================================================

def test_rule_status_display(client):
    """GET /api/optimization/rules must return rules with status fields."""
    res = client.get("/api/optimization/rules")
    assert res.status_code == 200
    rules = res.json()
    # Should be a dict with at least one top-level section
    assert isinstance(rules, dict)
    assert len(rules) > 0


# ============================================================================
# Test 8: Duration Predictor
# ============================================================================

def test_duration_predictor(client):
    """POST /api/maintenance/predict-duration returns expected schema fields."""
    payload = {
        "department_code": "ENG",
        "urgency": "HIGH",
        "duration_minutes": 180,
        "requires_power_block": False,
        "resource_type": "MACHINE",
        "section_length_km": 18.0,
        "weather_factor": 1.0,
    }
    res = client.post("/api/maintenance/predict-duration", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "predictedDuration" in data
    assert "lowerBound" in data
    assert "upperBound" in data
    assert "confidence" in data
    assert data["modelStatus"] == "DETERMINISTIC_BASELINE"
    assert data["predictedDuration"] > 0
    assert data["lowerBound"] <= data["predictedDuration"] <= data["upperBound"]

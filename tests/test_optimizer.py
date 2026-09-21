import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models.models import Department, Section, TrackLine, MaintenanceJob, TrainSchedule, OptimizationRun, BlockWindow
from backend.app.data.synthetic_seeder import seed_synthetic_data
from backend.app.optimizer.solver import RailwayBlockOptimizer
from backend.app.optimizer.constraints import RailwayConstraintManager

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    seed_synthetic_data(db, force=True)
    yield db
    db.close()

def test_cp_sat_optimizer_feasibility(db_session):
    optimizer = RailwayBlockOptimizer(db_session)
    result = optimizer.run_optimization(max_solver_time_sec=10)
    
    assert result["status"] in ["OPTIMAL", "FEASIBLE"]
    assert result["scheduled_jobs_count"] > 0
    assert result["total_maintenance_hours"] > 0
    assert result["block_utilization_pct"] > 0
    assert len(result["scheduled_blocks"]) == result["scheduled_jobs_count"]

def test_shadow_block_pairing(db_session):
    optimizer = RailwayBlockOptimizer(db_session)
    result = optimizer.run_optimization(maximize_shadow_blocks=True)
    
    shadow_blocks = [b for b in result["scheduled_blocks"] if b["is_shadow_block"]]
    assert len(shadow_blocks) >= 2
    assert result["shadow_block_synergy_pct"] > 0

def test_train_priority_deconfliction(db_session):
    optimizer = RailwayBlockOptimizer(db_session)
    result = optimizer.run_optimization(minimize_passenger_delays=True)
    
    # Check that total corridor train regulation is within controlled bounds
    assert result["train_delay_total_min"] <= 500


def test_scheduled_blocks_are_constrained_to_active_persisted_windows(db_session):
    """A CP-SAT solution must select an active window, not merely a job range."""
    result = RailwayBlockOptimizer(db_session).run_optimization()

    for block in result["scheduled_blocks"]:
        job = db_session.query(MaintenanceJob).filter_by(id=block["job_id"]).one()
        configured_windows = db_session.query(BlockWindow).filter(
            BlockWindow.section_id == job.section_id,
        ).all()
        matching_windows = [window for window in configured_windows if window.is_active]
        matching_windows = [
            window for window in matching_windows
            if window.track_line_id is None or window.track_line_id == job.track_line_id
        ]
        # Legacy fixture scopes with no matching BlockWindow remain supported;
        # a configured scope is always constrained by its active records.
        if not matching_windows:
            continue
        assert any(
            window.start_minute <= block["start_minute"]
            and block["end_minute"] <= window.end_minute
            for window in matching_windows
        ), block["job_code"]


def test_deactivated_block_window_excludes_its_jobs_from_the_plan(db_session):
    """Disabling a persisted window must have a real solver effect."""
    afternoon_window = db_session.query(BlockWindow).filter_by(
        window_code="WIN-FDB-PWL-AFT"
    ).one()
    afternoon_window.is_active = False
    db_session.commit()

    result = RailwayBlockOptimizer(db_session).run_optimization()
    deferred = {job["job_code"]: job for job in result["unscheduled_jobs"]}

    assert "JOB-ENG-104" not in {block["job_code"] for block in result["scheduled_blocks"]}
    assert deferred["JOB-ENG-104"]["reason_code"] == "NO_ACTIVE_BLOCK_WINDOW"


def test_block_window_enforcement_scenarios(db_session):
    """
    Focused regression test covering BlockWindow enforcement rules:
    A. section has windows + job requires traffic block -> constrained to window
    B. section has windows + job does NOT require traffic block -> not constrained to window
    C. section has no windows -> legacy behavior (schedulable without window)
    D. section has windows but no valid window on the job's track line -> cannot be scheduled
    E. inactive window -> cannot be selected
    """
    from backend.app.models.models import Section, TrackLine, Department

    # Prepare isolated section, track lines, and windows
    sec_configured = Section(code="SEC-CFG", start_station="CFG_A", end_station="CFG_B", length_km=20.0, max_speed_kmh=130)
    sec_legacy = Section(code="SEC-LEG", start_station="LEG_A", end_station="LEG_B", length_km=20.0, max_speed_kmh=130)
    db_session.add_all([sec_configured, sec_legacy])
    db_session.flush()

    line_cfg_up = TrackLine(section_id=sec_configured.id, line_type="UP", line_code="SEC-CFG-UP")
    line_cfg_dn = TrackLine(section_id=sec_configured.id, line_type="DN", line_code="SEC-CFG-DN")
    line_leg_up = TrackLine(section_id=sec_legacy.id, line_type="UP", line_code="SEC-LEG-UP")
    db_session.add_all([line_cfg_up, line_cfg_dn, line_leg_up])
    db_session.flush()

    # Active window ONLY on line_cfg_up: [200, 400]
    win_active = BlockWindow(
        window_code="WIN-CFG-UP-ACTIVE",
        section_id=sec_configured.id,
        track_line_id=line_cfg_up.id,
        start_minute=200,
        end_minute=400,
        is_active=True,
    )
    # Inactive window on line_cfg_dn: [200, 400]
    win_inactive = BlockWindow(
        window_code="WIN-CFG-DN-INACTIVE",
        section_id=sec_configured.id,
        track_line_id=line_cfg_dn.id,
        start_minute=200,
        end_minute=400,
        is_active=False,
    )
    db_session.add_all([win_active, win_inactive])

    dept = db_session.query(Department).first()

    # Scenario A: job on line_cfg_up requiring traffic block, requested range [0, 1440], duration 60.
    # Must be scheduled inside [200, 400].
    job_a = MaintenanceJob(
        job_code="JOB-SCEN-A",
        title="Scenario A Job",
        department_id=dept.id,
        section_id=sec_configured.id,
        track_line_id=line_cfg_up.id,
        duration_minutes=60,
        earliest_start_minute=0,
        latest_end_minute=1440,
        requires_traffic_block=True,
        priority=4,
    )

    # Scenario B: job on line_cfg_up NOT requiring traffic block, requested [500, 600] (completely outside window).
    # Since it does not require traffic block, it is NOT constrained by the window and should be scheduled in [500, 600].
    job_b = MaintenanceJob(
        job_code="JOB-SCEN-B",
        title="Scenario B Job",
        department_id=dept.id,
        section_id=sec_configured.id,
        track_line_id=line_cfg_up.id,
        duration_minutes=60,
        earliest_start_minute=500,
        latest_end_minute=600,
        requires_traffic_block=False,
        priority=4,
    )

    # Scenario C: job in section with NO windows at all, requiring traffic block.
    # Must preserve legacy behavior: scheduled according to requested range [100, 200].
    job_c = MaintenanceJob(
        job_code="JOB-SCEN-C",
        title="Scenario C Job",
        department_id=dept.id,
        section_id=sec_legacy.id,
        track_line_id=line_leg_up.id,
        duration_minutes=60,
        earliest_start_minute=100,
        latest_end_minute=200,
        requires_traffic_block=True,
        priority=4,
    )

    # Scenario D: job on configured section with NO valid active window for its track line.
    # line_cfg_dn only has an INACTIVE window. So no valid active window on line_cfg_dn.
    # Must NOT be scheduled outside the window.
    job_d = MaintenanceJob(
        job_code="JOB-SCEN-D",
        title="Scenario D Job",
        department_id=dept.id,
        section_id=sec_configured.id,
        track_line_id=line_cfg_dn.id,
        duration_minutes=60,
        earliest_start_minute=0,
        latest_end_minute=1440,
        requires_traffic_block=True,
        priority=4,
    )

    db_session.add_all([job_a, job_b, job_c, job_d])
    db_session.commit()

    optimizer = RailwayBlockOptimizer(db_session)
    result = optimizer.run_optimization()

    scheduled = {b["job_code"]: b for b in result["scheduled_blocks"]}
    unscheduled = {u["job_code"]: u for u in result["unscheduled_jobs"]}

    # A: Constrained to active window [200, 400]
    assert "JOB-SCEN-A" in scheduled
    assert scheduled["JOB-SCEN-A"]["start_minute"] >= 200
    assert scheduled["JOB-SCEN-A"]["end_minute"] <= 400

    # B: Scheduled despite being outside window [500, 600] because requires_traffic_block=False
    assert "JOB-SCEN-B" in scheduled
    assert scheduled["JOB-SCEN-B"]["start_minute"] >= 500
    assert scheduled["JOB-SCEN-B"]["end_minute"] <= 600

    # C: Legacy behavior preserved for sections without any BlockWindows
    assert "JOB-SCEN-C" in scheduled
    assert scheduled["JOB-SCEN-C"]["start_minute"] >= 100
    assert scheduled["JOB-SCEN-C"]["end_minute"] <= 200

    # D & E: Unscheduled because no active window on line_cfg_dn (the only one is inactive)
    assert "JOB-SCEN-D" not in scheduled
    assert "JOB-SCEN-D" in unscheduled
    assert unscheduled["JOB-SCEN-D"]["reason_code"] == "NO_ACTIVE_BLOCK_WINDOW"

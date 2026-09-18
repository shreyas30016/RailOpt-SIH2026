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

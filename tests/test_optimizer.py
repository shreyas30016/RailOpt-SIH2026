import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models.models import Department, Section, TrackLine, MaintenanceJob, TrainSchedule, OptimizationRun
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

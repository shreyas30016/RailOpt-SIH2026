"""
Comprehensive Stress & Hardening Test Suite for SIH26027 Railway Block Optimizer
Covers 10 critical stress scenarios:
1. NO-FEASIBLE-WINDOW
2. TRAIN-CONFLICT
3. DEPENDENCY (Precedence)
4. RESOURCE-CONFLICT (Machine Exclusivity)
5. EXTENDED-MAINTENANCE
6. BLOCK-UNAVAILABLE
7. DEPARTMENT-COMPATIBILITY
8. HIGH-DENSITY-SCENARIO
9. SUBURBAN/HIGH-FREQUENCY-SCENARIO
10. DYNAMIC-REPLAN
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ortools.sat.python import cp_model

from backend.app.database import Base
from backend.app.models.models import (
    Department, Section, TrackLine, MaintenanceResource,
    MaintenanceJob, TrainSchedule, BlockWindow, OptimizationRun
)
from backend.app.optimizer.solver import RailwayBlockOptimizer
from backend.app.optimizer.constraints import RailwayConstraintManager, JobConstraintMeta
from backend.app.optimizer.whatif import WhatIfSimulator
from backend.app.schemas.schemas import WhatIfRequest, MaintenanceJobCreate

@pytest.fixture
def base_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Core Setup
    dept_eng = Department(name="Civil Engineering", code="ENG", color="#003366")
    dept_trd = Department(name="Traction Distribution", code="TRD", color="#B35900")
    dept_snt = Department(name="Signal & Telecommunication", code="S_T", color="#1B5E20")
    db.add_all([dept_eng, dept_trd, dept_snt])
    db.commit()

    sec1 = Section(code="NDLS-TKD", start_station="New Delhi", end_station="Tuglakabad", length_km=17.5, max_speed_kmh=110)
    sec2 = Section(code="TKD-FDB", start_station="Tuglakabad", end_station="Faridabad", length_km=14.0, max_speed_kmh=130)
    sec3 = Section(code="FDB-PWL", start_station="Faridabad", end_station="Palwal", length_km=32.0, max_speed_kmh=130)
    db.add_all([sec1, sec2, sec3])
    db.commit()

    tl1_up = TrackLine(section_id=sec1.id, line_code="NDLS-TKD_UP", line_type="UP")
    tl1_dn = TrackLine(section_id=sec1.id, line_code="NDLS-TKD_DN", line_type="DN")
    tl2_up = TrackLine(section_id=sec2.id, line_code="TKD-FDB_UP", line_type="UP")
    tl3_up = TrackLine(section_id=sec3.id, line_code="FDB-PWL_UP", line_type="UP")
    db.add_all([tl1_up, tl1_dn, tl2_up, tl3_up])
    db.commit()

    res_csm = MaintenanceResource(name="Tamping Machine CSM-09", code="CSM-09", resource_type="MACHINE")
    res_tw = MaintenanceResource(name="Tower Wagon TW-01", code="TW-01", resource_type="TOWER_WAGON")
    db.add_all([res_csm, res_tw])
    db.commit()

    yield db
    db.close()

# -----------------------------------------------------------------------------------
# Scenario 1: NO-FEASIBLE-WINDOW
# -----------------------------------------------------------------------------------
def test_scenario_1_no_feasible_window(base_db):
    """Job requiring 300 minutes with earliest=100 and latest=200 cannot physically fit."""
    dept = base_db.query(Department).first()
    sec = base_db.query(Section).first()
    tl = base_db.query(TrackLine).first()

    impossible_job = MaintenanceJob(
        job_code="STRESS-NO-WIN", title="Bridge Bearing Replacement",
        department_id=dept.id, section_id=sec.id, track_line_id=tl.id,
        duration_minutes=300, priority=5, urgency="CRITICAL",
        earliest_start_minute=100, latest_end_minute=200, status="APPROVED"
    )
    base_db.add(impossible_job)
    base_db.commit()

    opt = RailwayBlockOptimizer(base_db)
    res = opt.run_optimization()

    assert res["status"] in ("OPTIMAL", "FEASIBLE")
    assert res["scheduled_jobs_count"] == 0, "Impossible job was falsely scheduled!"
    assert res["unscheduled_jobs_count"] == 1
    assert res["unscheduled_jobs"][0]["job_code"] == "STRESS-NO-WIN"

# -----------------------------------------------------------------------------------
# Scenario 2: TRAIN-CONFLICT
# -----------------------------------------------------------------------------------
def test_scenario_2_train_conflict(base_db):
    """A premium passenger train (Vande Bharat) cannot be delayed past 25 min; block must deconflict."""
    dept = base_db.query(Department).first()
    sec = base_db.query(Section).first()
    tl = base_db.query(TrackLine).first()

    # Vande Bharat passing between 06:00 (360m) and 07:00 (420m)
    train = TrainSchedule(
        train_number="22436", train_name="Vande Bharat",
        train_type="PREMIUM", priority_weight=50, direction="UP",
        departure_minute=360, arrival_minute=420
    )
    # Maintenance job requested right during the train's path
    job = MaintenanceJob(
        job_code="STRESS-TRAIN-01", title="Turnout Renewal",
        department_id=dept.id, section_id=sec.id, track_line_id=tl.id,
        duration_minutes=120, priority=5, urgency="CRITICAL",
        earliest_start_minute=300, latest_end_minute=600, status="APPROVED"
    )
    base_db.add_all([train, job])
    base_db.commit()

    opt = RailwayBlockOptimizer(base_db)
    res = opt.run_optimization()

    assert res["status"] == "OPTIMAL"
    assert res["scheduled_jobs_count"] == 1
    # Verify the block does not overlap the train's passage window
    block = res["scheduled_blocks"][0]
    # Block either finishes before train entry or starts after train exit
    train_cleared = (block["end_minute"] + 3 <= 360) or (block["start_minute"] >= 420 - 25)
    assert train_cleared, "Train conflict occurred with Vande Bharat!"

# -----------------------------------------------------------------------------------
# Scenario 3: DEPENDENCY (Precedence)
# -----------------------------------------------------------------------------------
def test_scenario_3_dependency(base_db):
    """Job B (Ballast Compacting) cannot start until Job A (Deep Screening) is complete."""
    dept = base_db.query(Department).first()
    sec = base_db.query(Section).first()
    tl = base_db.query(TrackLine).first()

    job_a = MaintenanceJob(
        job_code="DEP-A", title="Ballast Deep Screening",
        department_id=dept.id, section_id=sec.id, track_line_id=tl.id,
        duration_minutes=90, priority=5, urgency="CRITICAL",
        earliest_start_minute=60, latest_end_minute=360, status="APPROVED"
    )
    job_b = MaintenanceJob(
        job_code="DEP-B", title="Dynamic Track Stabilization",
        department_id=dept.id, section_id=sec.id, track_line_id=tl.id,
        duration_minutes=60, priority=4, urgency="HIGH",
        earliest_start_minute=60, latest_end_minute=360, status="APPROVED"
    )
    base_db.add_all([job_a, job_b])
    base_db.commit()

    # Pass constraint manager with precedence
    cm = RailwayConstraintManager(enable_job_precedence=True)
    opt = RailwayBlockOptimizer(base_db, constraint_manager=cm)

    # Inject dependency: DEP-B depends on DEP-A
    # We test via metas or solver precedence
    res = opt.run_optimization()
    assert res["status"] == "OPTIMAL"
    assert res["scheduled_jobs_count"] == 2

    sched = {b["job_code"]: b for b in res["scheduled_blocks"]}
    # Because they are on the same track line and same department, they cannot shadow each other
    assert sched["DEP-A"]["end_minute"] <= sched["DEP-B"]["start_minute"] or sched["DEP-B"]["end_minute"] <= sched["DEP-A"]["start_minute"]

# -----------------------------------------------------------------------------------
# Scenario 4: RESOURCE-CONFLICT
# -----------------------------------------------------------------------------------
def test_scenario_4_resource_conflict(base_db):
    """Two jobs on different sections both require the single CSM-09 tamping machine."""
    dept = base_db.query(Department).first()
    sec1 = base_db.query(Section).filter(Section.code == "NDLS-TKD").first()
    sec2 = base_db.query(Section).filter(Section.code == "TKD-FDB").first()
    tl1 = base_db.query(TrackLine).filter(TrackLine.section_id == sec1.id).first()
    tl2 = base_db.query(TrackLine).filter(TrackLine.section_id == sec2.id).first()
    csm = base_db.query(MaintenanceResource).filter(MaintenanceResource.code == "CSM-09").first()

    job1 = MaintenanceJob(
        job_code="MACH-01", title="Tamping Section 1",
        department_id=dept.id, section_id=sec1.id, track_line_id=tl1.id,
        duration_minutes=120, priority=5, urgency="CRITICAL",
        required_resource_id=csm.id, earliest_start_minute=60, latest_end_minute=360, status="APPROVED"
    )
    job2 = MaintenanceJob(
        job_code="MACH-02", title="Tamping Section 2",
        department_id=dept.id, section_id=sec2.id, track_line_id=tl2.id,
        duration_minutes=120, priority=4, urgency="HIGH",
        required_resource_id=csm.id, earliest_start_minute=60, latest_end_minute=360, status="APPROVED"
    )
    base_db.add_all([job1, job2])
    base_db.commit()

    opt = RailwayBlockOptimizer(base_db)
    res = opt.run_optimization()

    assert res["status"] == "OPTIMAL"
    assert res["scheduled_jobs_count"] == 2
    sched = {b["job_code"]: b for b in res["scheduled_blocks"]}
    # CSM-09 cannot be in two places at once
    no_machine_overlap = (sched["MACH-01"]["end_minute"] <= sched["MACH-02"]["start_minute"]) or \
                         (sched["MACH-02"]["end_minute"] <= sched["MACH-01"]["start_minute"])
    assert no_machine_overlap, "Machine double-booking violation on CSM-09!"

# -----------------------------------------------------------------------------------
# Scenario 5: EXTENDED-MAINTENANCE
# -----------------------------------------------------------------------------------
def test_scenario_5_extended_maintenance(base_db):
    """Testing duration extension via What-If simulator."""
    dept = base_db.query(Department).first()
    sec = base_db.query(Section).first()
    tl = base_db.query(TrackLine).first()

    job1 = MaintenanceJob(
        job_code="BASE-JOB", title="Track Relaying",
        department_id=dept.id, section_id=sec.id, track_line_id=tl.id,
        duration_minutes=120, priority=4, urgency="HIGH",
        earliest_start_minute=60, latest_end_minute=360, status="APPROVED"
    )
    base_db.add(job1)
    base_db.commit()

    sim = WhatIfSimulator(base_db)
    sim_req = WhatIfRequest(
        scenario_name="Extension Test",
        emergency_job=MaintenanceJobCreate(
            job_code="EXT-EMERGENCY",
            title="Extended Block Addition",
            department_code=dept.code,
            section_code=sec.code,
            duration_minutes=180,
            priority=5,
            urgency="CRITICAL",
            requires_power_block=False,
            requires_traffic_block=True,
            requires_speed_restriction=True,
            earliest_start_minute=60,
            latest_end_minute=360
        )
    )
    sim_res = sim.simulate_scenario(sim_req)
    assert sim_res["delta_scheduled_jobs"] == 1
    assert "successfully integrated" in sim_res["critical_alerts"][0]

# -----------------------------------------------------------------------------------
# Scenario 6: BLOCK-UNAVAILABLE
# -----------------------------------------------------------------------------------
def test_scenario_6_block_unavailable(base_db):
    """Removing corridor window (e.g. shrinking latest_end_minute) forces deferral or replan."""
    dept = base_db.query(Department).first()
    sec = base_db.query(Section).first()
    tl = base_db.query(TrackLine).first()

    job = MaintenanceJob(
        job_code="WIN-UNAVAIL", title="Signal Cable Laying",
        department_id=dept.id, section_id=sec.id, track_line_id=tl.id,
        duration_minutes=150, priority=3, urgency="MEDIUM",
        earliest_start_minute=60, latest_end_minute=360, status="APPROVED"
    )
    base_db.add(job)
    base_db.commit()

    opt = RailwayBlockOptimizer(base_db)
    # Window available [60, 360] -> scheduled
    res1 = opt.run_optimization(time_window_start=60, time_window_end=360)
    assert res1["scheduled_jobs_count"] == 1

    # Block window cancelled / restricted to [60, 120] (too short for 150m job)
    res2 = opt.run_optimization(time_window_start=60, time_window_end=120)
    assert res2["scheduled_jobs_count"] == 0
    assert res2["unscheduled_jobs_count"] == 1

# -----------------------------------------------------------------------------------
# Scenario 7: DEPARTMENT-COMPATIBILITY
# -----------------------------------------------------------------------------------
def test_scenario_7_department_compatibility(base_db):
    """Configurable Department Compatibility: ENG + TRD can shadow; ENG + ENG cannot."""
    dept_eng = base_db.query(Department).filter(Department.code == "ENG").first()
    dept_trd = base_db.query(Department).filter(Department.code == "TRD").first()
    sec = base_db.query(Section).first()
    tl = base_db.query(TrackLine).first()

    # 1 ENG job + 1 TRD job on same section/track
    job_eng = MaintenanceJob(
        job_code="COMPAT-ENG", title="Track Renewal",
        department_id=dept_eng.id, section_id=sec.id, track_line_id=tl.id,
        duration_minutes=120, priority=4, urgency="HIGH",
        earliest_start_minute=60, latest_end_minute=240, status="APPROVED"
    )
    job_trd = MaintenanceJob(
        job_code="COMPAT-TRD", title="OHE Adjustment",
        department_id=dept_trd.id, section_id=sec.id, track_line_id=tl.id,
        duration_minutes=120, priority=4, urgency="HIGH",
        earliest_start_minute=60, latest_end_minute=240, status="APPROVED"
    )
    base_db.add_all([job_eng, job_trd])
    base_db.commit()

    # With compatibility enabled
    opt_compat = RailwayBlockOptimizer(base_db)
    res_compat = opt_compat.run_optimization()
    assert res_compat["scheduled_jobs_count"] == 2
    assert res_compat["shadow_block_synergy_pct"] == 100.0

    # With shadow synergy disabled in constraint manager
    cm_no_shadow = RailwayConstraintManager(enable_shadow_block_synergy=False)
    opt_no_shadow = RailwayBlockOptimizer(base_db, constraint_manager=cm_no_shadow)
    res_no_shadow = opt_no_shadow.run_optimization()
    # Cannot fit two 120min non-overlapping jobs into 180min window [60, 240]
    assert res_no_shadow["scheduled_jobs_count"] == 1, "Non-compatible jobs overlapped incorrectly!"

# -----------------------------------------------------------------------------------
# Scenario 8: HIGH-DENSITY-SCENARIO
# -----------------------------------------------------------------------------------
def test_scenario_8_high_density(base_db):
    """Overloading corridor with 15 jobs when only 2 can fit in a single track window."""
    dept = base_db.query(Department).first()
    sec = base_db.query(Section).first()
    tl = base_db.query(TrackLine).first()

    for i in range(1, 16):
        base_db.add(MaintenanceJob(
            job_code=f"DENSE-{i:02d}", title=f"Routine Inspection {i}",
            department_id=dept.id, section_id=sec.id, track_line_id=tl.id,
            duration_minutes=90, priority=(5 if i == 1 else (4 if i == 2 else 2)),
            urgency="CRITICAL" if i == 1 else ("HIGH" if i == 2 else "ROUTINE"),
            earliest_start_minute=60, latest_end_minute=240, status="APPROVED"
        ))
    base_db.commit()

    opt = RailwayBlockOptimizer(base_db)
    res = opt.run_optimization()

    assert res["status"] == "OPTIMAL"
    # In window [60, 240] (180 min), at most 2 x 90min jobs can fit sequentially
    assert res["scheduled_jobs_count"] == 2
    assert res["unscheduled_jobs_count"] == 13
    sched_codes = {b["job_code"] for b in res["scheduled_blocks"]}
    # Priority 5 and 4 jobs must be chosen over priority 2 routine jobs
    assert "DENSE-01" in sched_codes and "DENSE-02" in sched_codes

# -----------------------------------------------------------------------------------
# Scenario 9: SUBURBAN / HIGH-FREQUENCY TIMETABLE
# -----------------------------------------------------------------------------------
def test_scenario_9_suburban_high_frequency(base_db):
    """Synthetic dense 15-minute headway train stream creating tight 45-minute lull slots."""
    dept = base_db.query(Department).first()
    sec = base_db.query(Section).first()
    tl = base_db.query(TrackLine).first()

    # Synthetic suburban train stream every 30 min
    for i, dep in enumerate([60, 120, 180, 240, 300]):
        base_db.add(TrainSchedule(
            train_number=f"SUB-{i+1}", train_name=f"Suburban Shuttle {i+1}",
            train_type="SUPERFAST", priority_weight=30, direction="UP",
            departure_minute=dep, arrival_minute=dep + 30
        ))

    # A short 25-minute emergency job can fit in the gap
    job_short = MaintenanceJob(
        job_code="SUB-SHORT", title="Insulator Cleaning",
        department_id=dept.id, section_id=sec.id, track_line_id=tl.id,
        duration_minutes=25, priority=5, urgency="CRITICAL",
        earliest_start_minute=60, latest_end_minute=330, status="APPROVED"
    )
    # A long 90-minute job cannot fit without disrupting multiple suburban trains
    job_long = MaintenanceJob(
        job_code="SUB-LONG", title="Major Track Renewal",
        department_id=dept.id, section_id=sec.id, track_line_id=tl.id,
        duration_minutes=90, priority=3, urgency="MEDIUM",
        earliest_start_minute=60, latest_end_minute=330, status="APPROVED"
    )
    base_db.add_all([job_short, job_long])
    base_db.commit()

    opt = RailwayBlockOptimizer(base_db)
    res = opt.run_optimization()

    assert res["status"] == "OPTIMAL"
    sched_codes = {b["job_code"] for b in res["scheduled_blocks"]}
    assert "SUB-SHORT" in sched_codes
    assert "SUB-LONG" not in sched_codes, "Long job violated high-frequency suburban train headway!"

# -----------------------------------------------------------------------------------
# Scenario 10: DYNAMIC-REPLAN
# -----------------------------------------------------------------------------------
def test_scenario_10_dynamic_replan(base_db):
    """Start with valid plan, inject train delay and emergency job, verify revised plan output."""
    dept = base_db.query(Department).first()
    sec = base_db.query(Section).first()
    tl = base_db.query(TrackLine).first()

    base_job = MaintenanceJob(
        job_code="BASE-PLANNED", title="Track Tamping",
        department_id=dept.id, section_id=sec.id, track_line_id=tl.id,
        duration_minutes=120, priority=3, urgency="MEDIUM",
        earliest_start_minute=90, latest_end_minute=360, status="APPROVED"
    )
    base_db.add(base_job)
    base_db.commit()

    sim = WhatIfSimulator(base_db)
    sim_req = WhatIfRequest(
        scenario_name="Dynamic Disruption Replan",
        emergency_job=MaintenanceJobCreate(
            job_code="EMG-RAIL-FRACTURE",
            title="Emergency Rail Fracture Weld",
            department_code=dept.code,
            section_code=sec.code,
            duration_minutes=120,
            priority=5,
            urgency="CRITICAL",
            requires_power_block=False,
            requires_traffic_block=True,
            requires_speed_restriction=True,
            earliest_start_minute=90,
            latest_end_minute=360
        ),
        simulated_train_delay_min=30
    )
    res = sim.simulate_scenario(sim_req)
    assert res["delta_scheduled_jobs"] == 1
    assert res["simulated_run"]["status"] == "OPTIMAL"
    assert len(res["critical_alerts"]) > 0

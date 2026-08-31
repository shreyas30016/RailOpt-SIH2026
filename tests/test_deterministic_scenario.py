"""
Deterministic Benchmark Scenario Test for SIH26027 Railway Block Planning
Verifies reproducible solver execution, constraint satisfaction, shadow block synergy, and KPI calculation.
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

@pytest.fixture
def deterministic_db():
    # In-memory SQLite database for deterministic isolation
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # 1. Departments (3 Core Departments)
    dept_eng = Department(name="Civil Engineering", code="ENG", color="#003366")
    dept_trd = Department(name="Traction Distribution", code="TRD", color="#B35900")
    dept_snt = Department(name="Signal & Telecommunication", code="S_T", color="#1B5E20")
    db.add_all([dept_eng, dept_trd, dept_snt])
    db.commit()

    # 2. Sections & Track Lines (Delhi - Agra Sections)
    sec1 = Section(code="NDLS-TKD", start_station="New Delhi", end_station="Tuglakabad", length_km=17.5, max_speed_kmh=110)
    sec2 = Section(code="TKD-FDB", start_station="Tuglakabad", end_station="Faridabad", length_km=14.0, max_speed_kmh=130)
    sec3 = Section(code="FDB-PWL", start_station="Faridabad", end_station="Palwal", length_km=32.0, max_speed_kmh=130)
    db.add_all([sec1, sec2, sec3])
    db.commit()

    tl1_up = TrackLine(section_id=sec1.id, line_code="NDLS-TKD_UP", line_type="UP")
    tl1_dn = TrackLine(section_id=sec1.id, line_code="NDLS-TKD_DN", line_type="DN")
    tl2_up = TrackLine(section_id=sec2.id, line_code="TKD-FDB_UP", line_type="UP")
    tl2_dn = TrackLine(section_id=sec2.id, line_code="TKD-FDB_DN", line_type="DN")
    tl3_up = TrackLine(section_id=sec3.id, line_code="FDB-PWL_UP", line_type="UP")
    tl3_dn = TrackLine(section_id=sec3.id, line_code="FDB-PWL_DN", line_type="DN")
    db.add_all([tl1_up, tl1_dn, tl2_up, tl2_dn, tl3_up, tl3_dn])
    db.commit()

    # 3. Resources (Track Machines & Tower Wagons)
    res_csm = MaintenanceResource(name="Continuous Tamping Machine CSM-09", code="CSM-09", resource_type="MACHINE")
    res_tw = MaintenanceResource(name="OHE 8-Wheeler Tower Wagon TW-01", code="TW-01", resource_type="TOWER_WAGON")
    db.add_all([res_csm, res_tw])
    db.commit()

    # 4. 4 Block Windows
    w1 = BlockWindow(window_code="WIN-01", section_id=sec1.id, track_line_id=tl1_up.id, start_minute=90, end_minute=240, window_type="CORRIDOR")
    w2 = BlockWindow(window_code="WIN-02", section_id=sec2.id, track_line_id=tl2_up.id, start_minute=120, end_minute=270, window_type="CORRIDOR")
    w3 = BlockWindow(window_code="WIN-03", section_id=sec3.id, track_line_id=tl3_up.id, start_minute=90, end_minute=300, window_type="CORRIDOR")
    w4 = BlockWindow(window_code="WIN-04", section_id=sec3.id, track_line_id=tl3_dn.id, start_minute=720, end_minute=900, window_type="CORRIDOR")
    db.add_all([w1, w2, w3, w4])
    db.commit()

    # 5. 10 Maintenance Jobs across 3 Departments
    jobs = [
        # Job 1: ENG Tamping on NDLS-TKD UP
        MaintenanceJob(
            job_code="DET-ENG-01", title="Plain Track Tamping",
            department_id=dept_eng.id, section_id=sec1.id, track_line_id=tl1_up.id,
            duration_minutes=120, priority=5, urgency="CRITICAL",
            requires_power_block=False, requires_traffic_block=True, requires_speed_restriction=True,
            required_resource_id=res_csm.id, earliest_start_minute=90, latest_end_minute=240, status="APPROVED"
        ),
        # Job 2: TRD Shadow pair with Job 1 on NDLS-TKD UP
        MaintenanceJob(
            job_code="DET-TRD-01", title="OHE Periodic Overhauling",
            department_id=dept_trd.id, section_id=sec1.id, track_line_id=tl1_up.id,
            duration_minutes=120, priority=4, urgency="HIGH",
            requires_power_block=True, requires_traffic_block=True, requires_speed_restriction=False,
            earliest_start_minute=90, latest_end_minute=240, status="APPROVED"
        ),
        # Job 3: S&T Track Circuit Maintenance on NDLS-TKD UP (Shadow candidate)
        MaintenanceJob(
            job_code="DET-SNT-01", title="Audio Frequency Track Circuit Testing",
            department_id=dept_snt.id, section_id=sec1.id, track_line_id=tl1_up.id,
            duration_minutes=90, priority=4, urgency="HIGH",
            requires_power_block=False, requires_traffic_block=True, requires_speed_restriction=False,
            earliest_start_minute=90, latest_end_minute=240, status="APPROVED"
        ),
        # Job 4: ENG Ballast Regulation on TKD-FDB UP
        MaintenanceJob(
            job_code="DET-ENG-02", title="Ballast Profiling & Dressing",
            department_id=dept_eng.id, section_id=sec2.id, track_line_id=tl2_up.id,
            duration_minutes=120, priority=4, urgency="HIGH",
            requires_power_block=False, requires_traffic_block=True, requires_speed_restriction=False,
            earliest_start_minute=120, latest_end_minute=270, status="APPROVED"
        ),
        # Job 5: TRD Tower Wagon Inspection on TKD-FDB UP (Shadow candidate)
        MaintenanceJob(
            job_code="DET-TRD-02", title="Contact Wire Height Adjustment",
            department_id=dept_trd.id, section_id=sec2.id, track_line_id=tl2_up.id,
            duration_minutes=120, priority=3, urgency="MEDIUM",
            requires_power_block=True, requires_traffic_block=True, requires_speed_restriction=False,
            required_resource_id=res_tw.id, earliest_start_minute=120, latest_end_minute=270, status="APPROVED"
        ),
        # Job 6: S&T Point Machine Lubrication on TKD-FDB DN
        MaintenanceJob(
            job_code="DET-SNT-02", title="Electric Point Machine Overhauling",
            department_id=dept_snt.id, section_id=sec2.id, track_line_id=tl2_dn.id,
            duration_minutes=60, priority=3, urgency="MEDIUM",
            requires_power_block=False, requires_traffic_block=True, requires_speed_restriction=False,
            earliest_start_minute=120, latest_end_minute=300, status="APPROVED"
        ),
        # Job 7: ENG Turnout Tamping on FDB-PWL UP (Requires CSM-09 after Job 1)
        MaintenanceJob(
            job_code="DET-ENG-03", title="1 in 12 Turnout Point Tamping",
            department_id=dept_eng.id, section_id=sec3.id, track_line_id=tl3_up.id,
            duration_minutes=90, priority=5, urgency="CRITICAL",
            requires_power_block=False, requires_traffic_block=True, requires_speed_restriction=True,
            required_resource_id=res_csm.id, earliest_start_minute=90, latest_end_minute=300, status="APPROVED"
        ),
        # Job 8: TRD Isolator Switch Maintenance on FDB-PWL UP (Shadow candidate)
        MaintenanceJob(
            job_code="DET-TRD-03", title="Sectioning Post Isolator Maintenance",
            department_id=dept_trd.id, section_id=sec3.id, track_line_id=tl3_up.id,
            duration_minutes=90, priority=4, urgency="HIGH",
            requires_power_block=True, requires_traffic_block=True, requires_speed_restriction=False,
            earliest_start_minute=90, latest_end_minute=300, status="APPROVED"
        ),
        # Job 9: S&T Digital Axle Counter Calibration on FDB-PWL DN
        MaintenanceJob(
            job_code="DET-SNT-03", title="High Availability Single Section Axle Counter",
            department_id=dept_snt.id, section_id=sec3.id, track_line_id=tl3_dn.id,
            duration_minutes=90, priority=4, urgency="HIGH",
            requires_power_block=False, requires_traffic_block=True, requires_speed_restriction=False,
            earliest_start_minute=720, latest_end_minute=900, status="APPROVED"
        ),
        # Job 10: ENG Ultrasonic Weld Testing on FDB-PWL DN
        MaintenanceJob(
            job_code="DET-ENG-04", title="USFD Weld Defect Detection",
            department_id=dept_eng.id, section_id=sec3.id, track_line_id=tl3_dn.id,
            duration_minutes=90, priority=3, urgency="MEDIUM",
            requires_power_block=False, requires_traffic_block=False, requires_speed_restriction=False,
            earliest_start_minute=720, latest_end_minute=900, status="APPROVED"
        )
    ]
    db.add_all(jobs)
    db.commit()

    # 6. Train Movements (Vande Bharat, Express, Goods)
    trains = [
        TrainSchedule(
            train_number="22436", train_name="Vande Bharat Express",
            train_type="PREMIUM", priority_weight=50, direction="DN",
            departure_minute=360, arrival_minute=450
        ),
        TrainSchedule(
            train_number="12952", train_name="Mumbai Rajdhani",
            train_type="PREMIUM", priority_weight=40, direction="UP",
            departure_minute=480, arrival_minute=570
        ),
        TrainSchedule(
            train_number="12722", train_name="Dakshin Express",
            train_type="EXPRESS", priority_weight=20, direction="DN",
            departure_minute=1320, arrival_minute=1410
        ),
        TrainSchedule(
            train_number="BOXN-901", train_name="Container Goods Rake",
            train_type="FREIGHT", priority_weight=2, direction="UP",
            departure_minute=150, arrival_minute=300
        )
    ]
    db.add_all(trains)
    db.commit()

    yield db
    db.close()

def test_deterministic_benchmark_optimization(deterministic_db):
    """
    Executes the deterministic scenario and verifies:
    1. Solver reaches OPTIMAL status.
    2. All 10 maintenance demands are scheduled.
    3. Machine CSM-09 exclusivity is strictly enforced between DET-ENG-01 and DET-ENG-03.
    4. Multi-department shadow block synergy is maximized.
    5. KPIs match expected benchmark numbers.
    """
    optimizer = RailwayBlockOptimizer(deterministic_db)
    result = optimizer.run_optimization(
        time_window_start=0,
        time_window_end=1440,
        max_solver_time_sec=10,
        minimize_passenger_delays=True,
        maximize_shadow_blocks=True
    )

    # 1. Status & Job Counts
    assert result["status"] == "OPTIMAL", f"Solver did not find optimal plan: {result['status']}"
    assert result["scheduled_jobs_count"] == 10, f"Expected 10 scheduled jobs, got {result['scheduled_jobs_count']}"
    assert result["unscheduled_jobs_count"] == 0, f"Expected 0 unscheduled jobs, got {result['unscheduled_jobs_count']}"

    # 2. Total Maintenance Hours (120+120+90+120+120+60+90+90+90+90 = 990 min = 16.5 hrs)
    assert result["total_maintenance_hours"] == 16.5, f"Expected 16.5 maintenance hours, got {result['total_maintenance_hours']}"

    # 3. Machine Resource Exclusivity: CSM-09 cannot overlap in time
    sched_blocks = {b["job_code"]: b for b in result["scheduled_blocks"]}
    b_eng1 = sched_blocks["DET-ENG-01"]
    b_eng3 = sched_blocks["DET-ENG-03"]

    # Either DET-ENG-01 finishes before DET-ENG-03 starts, or vice versa
    csm_no_overlap = (b_eng1["end_minute"] <= b_eng3["start_minute"]) or (b_eng3["end_minute"] <= b_eng1["start_minute"])
    assert csm_no_overlap, f"Machine collision detected on CSM-09: {b_eng1} vs {b_eng3}"

    # 4. Shadow Block Pairings: DET-ENG-01 + DET-TRD-01 start simultaneously
    b_trd1 = sched_blocks["DET-TRD-01"]
    assert b_eng1["start_minute"] == b_trd1["start_minute"], "Shadow block pair DET-ENG-01 and DET-TRD-01 did not synchronize start times!"

    # 5. Shadow Synergy Percentage should be > 0%
    assert result["shadow_block_synergy_pct"] >= 40.0, f"Shadow synergy too low: {result['shadow_block_synergy_pct']}%"

    print("\n[+] Deterministic Benchmark Plan Verified Successfully!")
    print(f"    - Status: {result['status']}")
    print(f"    - Scheduled Jobs: {result['scheduled_jobs_count']}/10")
    print(f"    - Total Maintenance Hours: {result['total_maintenance_hours']} hrs")
    print(f"    - Train Delays: {result['train_delay_total_min']} min")
    print(f"    - Shadow Block Synergy: {result['shadow_block_synergy_pct']}%")
    print(f"    - Solver Time: {result['solver_time_seconds']}s")

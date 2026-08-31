from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False) # ENG, S_T, TRD, MECH
    name = Column(String(100), nullable=False)
    color = Column(String(20), default="#003366")
    icon = Column(String(50), default="construction")

    jobs = relationship("MaintenanceJob", back_populates="department")

class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # e.g. NDLS-TKD, TKD-FDB, FDB-PWL
    start_station = Column(String(50), nullable=False)
    end_station = Column(String(50), nullable=False)
    length_km = Column(Float, default=15.0)
    num_tracks = Column(Integer, default=2)
    division = Column(String(50), default="Delhi (Northern Railway)")
    max_speed_kmh = Column(Integer, default=130)

    track_lines = relationship("TrackLine", back_populates="section")
    jobs = relationship("MaintenanceJob", back_populates="section")

class TrackLine(Base):
    __tablename__ = "track_lines"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    line_code = Column(String(50), nullable=False) # UP_MAIN, DN_MAIN, 3RD_LINE
    line_type = Column(String(20), default="UP") # UP, DN, BIDIRECTIONAL

    section = relationship("Section", back_populates="track_lines")

class MaintenanceResource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False) # CSM 09-32 Tamping, DTS, Tower Wagon
    resource_type = Column(String(30), default="MACHINE") # MACHINE, CREW, TOWER_WAGON
    department_code = Column(String(20), default="ENG")
    home_depot = Column(String(50), default="Tuglakabad (TKD)")
    transit_speed_kmh = Column(Float, default=40.0)

class MaintenanceJob(Base):
    __tablename__ = "maintenance_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. JOB-ENG-101
    title = Column(String(200), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    track_line_id = Column(Integer, ForeignKey("track_lines.id"), nullable=True)
    
    duration_minutes = Column(Integer, nullable=False, default=180)
    priority = Column(Integer, default=3) # 1 (Lowest) to 5 (Critical/Emergency)
    urgency = Column(String(20), default="MEDIUM") # CRITICAL, HIGH, MEDIUM, ROUTINE
    
    requires_power_block = Column(Boolean, default=False)
    requires_traffic_block = Column(Boolean, default=True)
    requires_speed_restriction = Column(Boolean, default=False)
    speed_restriction_kmh = Column(Integer, default=30)
    
    required_resource_id = Column(Integer, ForeignKey("resources.id"), nullable=True)
    status = Column(String(30), default="PENDING") # PENDING, SCHEDULED, DEFERRED, APPROVED
    
    requested_date = Column(String(20), default="2026-09-01")
    earliest_start_minute = Column(Integer, default=0) # minute offset from 00:00 (0 to 1440)
    latest_end_minute = Column(Integer, default=1440)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=True)

    department = relationship("Department", back_populates="jobs")
    section = relationship("Section", back_populates="jobs")
    track_line = relationship("TrackLine")
    required_resource = relationship("MaintenanceResource")

class TrainSchedule(Base):
    __tablename__ = "train_schedules"

    id = Column(Integer, primary_key=True, index=True)
    train_number = Column(String(20), unique=True, index=True, nullable=False)
    train_name = Column(String(100), nullable=False)
    train_type = Column(String(30), default="EXPRESS") # VANDE_BHARAT, RAJDHANI, SUPERFAST, PASSENGER, FREIGHT
    priority_weight = Column(Integer, default=10) # 30 for Vande Bharat/Rajdhani, 15 for Mail, 5 for Freight
    direction = Column(String(10), default="DN") # UP, DN
    origin_station = Column(String(50), default="NDLS")
    destination_station = Column(String(50), default="AGC")
    departure_minute = Column(Integer, default=360) # 06:00 AM
    arrival_minute = Column(Integer, default=480) # 08:00 AM
    section_path_json = Column(Text, nullable=True) # JSON list of {section_code, line_type, entry_minute, exit_minute}

class BlockWindow(Base):
    __tablename__ = "block_windows"

    id = Column(Integer, primary_key=True, index=True)
    window_code = Column(String(50), unique=True, index=True, nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    track_line_id = Column(Integer, ForeignKey("track_lines.id"), nullable=True)
    start_minute = Column(Integer, nullable=False) # e.g. 120 (02:00)
    end_minute = Column(Integer, nullable=False) # e.g. 330 (05:30)
    window_type = Column(String(30), default="CORRIDOR") # CORRIDOR, SHADOW, EMERGENCY
    is_active = Column(Boolean, default=True)

    section = relationship("Section")
    track_line = relationship("TrackLine")

class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(30), default="OPTIMAL") # OPTIMAL, FEASIBLE, INFEASIBLE
    total_jobs = Column(Integer, default=0)
    scheduled_jobs_count = Column(Integer, default=0)
    unscheduled_jobs_count = Column(Integer, default=0)
    train_delay_total_min = Column(Integer, default=0)
    block_utilization_pct = Column(Float, default=0.0)
    shadow_block_synergy_pct = Column(Float, default=0.0)
    objective_score = Column(Float, default=0.0)
    solver_time_seconds = Column(Float, default=0.0)
    solver_status = Column(String(50), default="OPTIMAL")
    parameters_json = Column(Text, nullable=True)

    scheduled_blocks = relationship("ScheduledBlock", back_populates="optimization_run")
    conflict_logs = relationship("ConflictLog", back_populates="optimization_run")
    explanations = relationship("DecisionExplanation", back_populates="optimization_run")

class ScheduledBlock(Base):
    __tablename__ = "scheduled_blocks"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("optimization_runs.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("maintenance_jobs.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    track_line_id = Column(Integer, ForeignKey("track_lines.id"), nullable=True)
    
    start_minute = Column(Integer, nullable=False)
    end_minute = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    
    department_code = Column(String(20), default="ENG")
    is_shadow_block = Column(Boolean, default=False)
    paired_job_codes_json = Column(Text, nullable=True)
    resource_assigned = Column(String(100), nullable=True)
    train_impacts_json = Column(Text, nullable=True) # affected trains with minute delays

    optimization_run = relationship("OptimizationRun", back_populates="scheduled_blocks")
    job = relationship("MaintenanceJob")
    section = relationship("Section")
    track_line = relationship("TrackLine")

class ConflictLog(Base):
    __tablename__ = "conflict_logs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("optimization_runs.id"), nullable=False)
    conflict_type = Column(String(50), nullable=False) # TRACK_COLLISION, MACHINE_UNAVAILABLE, POWER_BLOCK_MISMATCH, TRAIN_OVERLAP
    severity = Column(String(20), default="RESOLVED") # RESOLVED, PREVENTED, UNRESOLVED
    description = Column(Text, nullable=False)
    involved_entities_json = Column(Text, nullable=True)
    resolution_applied = Column(Text, nullable=True)

    optimization_run = relationship("OptimizationRun", back_populates="conflict_logs")

class DecisionExplanation(Base):
    __tablename__ = "decision_explanations"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("optimization_runs.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("maintenance_jobs.id"), nullable=False)
    decision_type = Column(String(50), default="SCHEDULED") # SCHEDULED, DEFERRED, SHIFTED, SHADOW_PAIRED
    primary_reason = Column(Text, nullable=False)
    reasoning_tree_json = Column(Text, nullable=True)

    optimization_run = relationship("OptimizationRun", back_populates="explanations")
    job = relationship("MaintenanceJob")

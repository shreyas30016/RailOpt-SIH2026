from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Department Schemas
class DepartmentBase(BaseModel):
    code: str
    name: str
    color: str = "#003366"
    icon: str = "construction"

class DepartmentResponse(DepartmentBase):
    id: int
    class Config:
        from_attributes = True

# Section Schemas
class SectionBase(BaseModel):
    code: str
    start_station: str
    end_station: str
    length_km: float = 15.0
    num_tracks: int = 2
    division: str = "Delhi (Northern Railway)"
    max_speed_kmh: int = 130

class SectionResponse(SectionBase):
    id: int
    class Config:
        from_attributes = True

# Maintenance Job Schemas
class MaintenanceJobCreate(BaseModel):
    job_code: str
    title: str
    department_code: str
    section_code: str
    track_line: Optional[str] = "UP_MAIN"
    duration_minutes: int = 180
    priority: int = 3
    urgency: str = "MEDIUM"
    requires_power_block: bool = False
    requires_traffic_block: bool = True
    requires_speed_restriction: bool = False
    speed_restriction_kmh: Optional[int] = 30
    requested_date: Optional[str] = "2026-09-01"
    earliest_start_minute: Optional[int] = 0
    latest_end_minute: Optional[int] = 1440
    description: Optional[str] = None

class MaintenanceJobResponse(BaseModel):
    id: int
    job_code: str
    title: str
    department_code: str
    department_name: str
    section_code: str
    track_line: Optional[str]
    duration_minutes: int
    priority: int
    urgency: str
    requires_power_block: bool
    requires_traffic_block: bool
    requires_speed_restriction: bool
    speed_restriction_kmh: Optional[int]
    status: str
    requested_date: str
    earliest_start_minute: int
    latest_end_minute: int
    description: Optional[str]
    class Config:
        from_attributes = True

# Train Schedule Schemas
class TrainScheduleResponse(BaseModel):
    id: int
    train_number: str
    train_name: str
    train_type: str
    priority_weight: int
    direction: str
    origin_station: str
    destination_station: str
    departure_minute: int
    arrival_minute: int
    departure_time_str: str
    arrival_time_str: str
    class Config:
        from_attributes = True

# Optimization Request & Response Schemas
class OptimizationParams(BaseModel):
    corridor: Optional[str] = "Delhi-Agra Mainline"
    date: Optional[str] = "2026-09-01"
    time_window_start_min: int = 0
    time_window_end_min: int = 1440
    max_solver_time_sec: int = 15
    minimize_passenger_delays: bool = True
    maximize_shadow_blocks: bool = True
    allow_train_speed_restrictions: bool = True

class ScheduledBlockDetail(BaseModel):
    id: Optional[int] = None
    job_id: int
    job_code: str
    title: str
    department_code: str
    department_color: str
    section_code: str
    track_line: str
    start_minute: int
    end_minute: int
    start_time_str: str
    end_time_str: str
    duration_minutes: int
    is_shadow_block: bool
    paired_job_codes: List[str] = []
    resource_assigned: Optional[str] = None
    affected_trains: List[Dict[str, Any]] = []
    explanation: Optional[str] = None

class UnscheduledJobDetail(BaseModel):
    job_id: int
    job_code: str
    title: str
    department_code: str
    section_code: str
    duration_minutes: int
    priority: int
    reason: str
    reason_code: Optional[str] = None          # e.g. NO_FEASIBLE_WINDOW, TRAIN_CONFLICT
    failed_candidate_windows: List[Dict[str, Any]] = []
    next_feasible_window: Optional[Dict[str, Any]] = None
    suggested_alternative: Optional[str] = None

class OptimizationResponse(BaseModel):
    run_id: int
    timestamp: str
    status: str
    total_jobs: int
    scheduled_jobs_count: int
    unscheduled_jobs_count: int
    total_maintenance_hours: float
    train_delay_total_min: int
    block_utilization_pct: float
    shadow_block_synergy_pct: float
    objective_score: float
    solver_time_seconds: float
    scheduled_blocks: List[ScheduledBlockDetail]
    unscheduled_jobs: List[UnscheduledJobDetail]
    conflicts_resolved: List[Dict[str, Any]]
    explanations: List[Dict[str, Any]]

# What-If Simulation Schemas
class WhatIfRequest(BaseModel):
    scenario_name: str
    emergency_job: Optional[MaintenanceJobCreate] = None
    simulated_train_delay_min: int = 0
    delayed_train_number: Optional[str] = None
    blocked_section_code: Optional[str] = None
    block_duration_extra_min: int = 0

class WhatIfComparisonResponse(BaseModel):
    scenario_name: str
    baseline_run_id: int
    simulated_run: Dict[str, Any]          # relaxed type: full optimizer output
    baseline_blocks: List[Dict[str, Any]] = []
    new_blocks: List[Dict[str, Any]] = []
    affected_jobs: List[str] = []
    dropped_jobs: List[str] = []
    gained_jobs: List[str] = []
    delta_scheduled_jobs: int
    delta_train_delay_min: int
    delta_utilization_pct: float
    delta_deferred_jobs: int = 0
    kpi_delta: Dict[str, Any] = {}
    critical_alerts: List[str]
    impact_summary: str
    disruptions_applied: Optional[Dict[str, Any]] = None

# Dashboard Summary Schema
class DashboardSummary(BaseModel):
    total_active_blocks: int
    total_pending_requests: int
    total_jobs: int = 0
    critical_jobs_count: int = 0
    planned_blocks_today: int
    efficiency_pct: float
    shadow_block_synergy_pct: float
    punctuality_impact_pct: float
    conflicts_count: int = 0
    conflicts_list: List[Dict[str, Any]] = []
    upcoming_blocks: List[Dict[str, Any]] = []
    urgent_queue: List[MaintenanceJobResponse]
    department_breakdown: Dict[str, int]
    live_corridor_status: List[Dict[str, Any]]
    latest_optimization_summary: Optional[Dict[str, Any]] = None
    live_trains_feed: Optional[Dict[str, Any]] = None

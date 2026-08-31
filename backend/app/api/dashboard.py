from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import MaintenanceJob, ScheduledBlock, OptimizationRun, Section, Department, ConflictLog, BlockWindow
from ..schemas.schemas import DashboardSummary, MaintenanceJobResponse
from ..services.train_adapter import train_adapter

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

def _min_to_str(m: int) -> str:
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_jobs = db.query(MaintenanceJob).count()
    total_pending = db.query(MaintenanceJob).filter(MaintenanceJob.status == "PENDING").count()
    critical_jobs_count = db.query(MaintenanceJob).filter(
        MaintenanceJob.urgency.in_(["CRITICAL", "HIGH"])
    ).count()
    
    latest_run = db.query(OptimizationRun).order_by(OptimizationRun.id.desc()).first()
    
    total_active_blocks = db.query(BlockWindow).filter(BlockWindow.is_active == True).count()
    planned_blocks_today = 0
    efficiency = 92.4
    shadow_synergy = 68.5
    punctuality_impact = 1.2
    latest_summary = None
    upcoming_blocks = []
    conflicts_list = []

    if latest_run:
        planned_blocks_today = latest_run.scheduled_jobs_count
        efficiency = round(latest_run.block_utilization_pct, 1)
        shadow_synergy = round(latest_run.shadow_block_synergy_pct, 1)
        punctuality_impact = round(max(0.4, (latest_run.train_delay_total_min / 300.0) * 1.5), 1)
        latest_summary = {
            "run_id": latest_run.id,
            "status": latest_run.status,
            "scheduled_count": latest_run.scheduled_jobs_count,
            "unscheduled_count": latest_run.unscheduled_jobs_count,
            "train_delay_min": latest_run.train_delay_total_min,
            "solver_time_sec": latest_run.solver_time_seconds,
            "timestamp": latest_run.run_timestamp.strftime("%Y-%m-%d %H:%M")
        }

        # Upcoming scheduled blocks from latest optimization run
        s_blocks = db.query(ScheduledBlock).filter(ScheduledBlock.run_id == latest_run.id).order_by(ScheduledBlock.start_minute.asc()).limit(6).all()
        for sb in s_blocks:
            j = sb.job
            upcoming_blocks.append({
                "block_id": f"B-{sb.id:02d}",
                "job_code": j.job_code if j else f"JOB-{sb.job_id}",
                "job_title": j.title if j else "Track Maintenance",
                "department_code": sb.department_code,
                "section_code": sb.section.code if sb.section else "CORRIDOR",
                "track_line": sb.track_line.line_code if sb.track_line else "MAIN",
                "start_time_str": _min_to_str(sb.start_minute),
                "end_time_str": _min_to_str(sb.end_minute),
                "duration_minutes": sb.duration_minutes,
                "is_shadow_block": sb.is_shadow_block,
                "status": "APPROVED" if j and j.status == "APPROVED" else "SCHEDULED"
            })

        # Resolved/Active conflicts from latest run
        c_logs = db.query(ConflictLog).filter(ConflictLog.run_id == latest_run.id).limit(6).all()
        for c in c_logs:
            conflicts_list.append({
                "type": c.conflict_type,
                "severity": c.severity,
                "description": c.description,
                "resolution": c.resolution_applied or "Resolved by CP-SAT solver"
            })
    else:
        # Fallback if no run yet: show pending jobs as queue
        p_jobs = db.query(MaintenanceJob).limit(5).all()
        for j in p_jobs:
            upcoming_blocks.append({
                "block_id": f"REQ-{j.id:02d}",
                "job_code": j.job_code,
                "job_title": j.title,
                "department_code": j.department.code if j.department else "ENG",
                "section_code": j.section.code if j.section else "CORRIDOR",
                "track_line": j.track_line.line_code if j.track_line else "MAIN",
                "start_time_str": _min_to_str(j.earliest_start_minute),
                "end_time_str": _min_to_str(j.latest_end_minute),
                "duration_minutes": j.duration_minutes,
                "is_shadow_block": False,
                "status": j.status
            })

    # Urgent Queue (Critical & High priority jobs)
    urgent_jobs_db = db.query(MaintenanceJob).filter(
        MaintenanceJob.urgency.in_(["CRITICAL", "HIGH"])
    ).order_by(MaintenanceJob.priority.desc()).limit(6).all()

    urgent_queue = []
    for j in urgent_jobs_db:
        urgent_queue.append(MaintenanceJobResponse(
            id=j.id,
            job_code=j.job_code,
            title=j.title,
            department_code=j.department.code if j.department else "ENG",
            department_name=j.department.name if j.department else "Civil Engineering",
            section_code=j.section.code if j.section else "UNKNOWN",
            track_line=j.track_line.line_code if j.track_line else "UP_MAIN",
            duration_minutes=j.duration_minutes,
            priority=j.priority,
            urgency=j.urgency,
            requires_power_block=j.requires_power_block,
            requires_traffic_block=j.requires_traffic_block,
            requires_speed_restriction=j.requires_speed_restriction,
            speed_restriction_kmh=j.speed_restriction_kmh,
            status=j.status,
            requested_date=j.requested_date,
            earliest_start_minute=j.earliest_start_minute,
            latest_end_minute=j.latest_end_minute,
            description=j.description
        ))

    # Department breakdown
    dept_breakdown = {}
    for d in db.query(Department).all():
        cnt = db.query(MaintenanceJob).filter(MaintenanceJob.department_id == d.id).count()
        dept_breakdown[d.code] = cnt

    # Live Corridor Status
    sections = db.query(Section).all()
    live_status = []
    for s in sections:
        sec_blocks = db.query(MaintenanceJob).filter(MaintenanceJob.section_id == s.id).count()
        status_tag = "ACTIVE_BLOCK" if sec_blocks > 1 else ("CLEAR" if sec_blocks == 0 else "PLANNED")
        live_status.append({
            "section_code": s.code,
            "name": f"{s.start_station} - {s.end_station}",
            "length_km": s.length_km,
            "max_speed_kmh": s.max_speed_kmh,
            "status": status_tag,
            "pending_jobs": sec_blocks
        })

    # Live train movements feed via adapter
    live_trains = train_adapter.get_movements()

    return DashboardSummary(
        total_active_blocks=total_active_blocks,
        total_pending_requests=total_pending,
        total_jobs=total_jobs,
        critical_jobs_count=critical_jobs_count,
        planned_blocks_today=planned_blocks_today,
        efficiency_pct=efficiency,
        shadow_block_synergy_pct=shadow_synergy,
        punctuality_impact_pct=punctuality_impact,
        conflicts_count=len(conflicts_list),
        conflicts_list=conflicts_list,
        upcoming_blocks=upcoming_blocks,
        urgent_queue=urgent_queue,
        department_breakdown=dept_breakdown,
        live_corridor_status=live_status,
        latest_optimization_summary=latest_summary,
        live_trains_feed=live_trains
    )

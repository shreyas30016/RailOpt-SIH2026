from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import MaintenanceJob, ScheduledBlock, OptimizationRun, Section, Department
from ..schemas.schemas import DashboardSummary, MaintenanceJobResponse
from ..services.train_adapter import train_adapter

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_pending = db.query(MaintenanceJob).filter(MaintenanceJob.status == "PENDING").count()
    
    latest_run = db.query(OptimizationRun).order_by(OptimizationRun.id.desc()).first()
    
    total_active_blocks = 0
    planned_blocks_today = 0
    efficiency = 92.4
    shadow_synergy = 68.5
    punctuality_impact = 1.2
    latest_summary = None

    if latest_run:
        planned_blocks_today = latest_run.scheduled_jobs_count
        total_active_blocks = db.query(ScheduledBlock).filter(ScheduledBlock.run_id == latest_run.id).count()
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
        planned_blocks_today=planned_blocks_today,
        efficiency_pct=efficiency,
        shadow_block_synergy_pct=shadow_synergy,
        punctuality_impact_pct=punctuality_impact,
        urgent_queue=urgent_queue,
        department_breakdown=dept_breakdown,
        live_corridor_status=live_status,
        latest_optimization_summary=latest_summary,
        live_trains_feed=live_trains
    )

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..database import get_db
from ..models.models import OptimizationRun, ScheduledBlock, MaintenanceJob, ConflictLog, DecisionExplanation
from ..schemas.schemas import OptimizationParams, OptimizationResponse
from ..optimizer.solver import RailwayBlockOptimizer
from ..optimizer.explainer import DecisionExplainer
from .auth import require_permission

router = APIRouter(prefix="/optimization", tags=["Optimization"])

class OptimizeRequest(BaseModel):
    maintenance_jobs: Optional[List[Dict[str, Any]]] = None
    train_movements: Optional[List[Dict[str, Any]]] = None
    block_windows: Optional[List[Dict[str, Any]]] = None
    constraints: Optional[Dict[str, Any]] = None
    optimization_objectives: Optional[Dict[str, Any]] = None
    max_solver_time_sec: int = 15

@router.post("/run")
@router.post("")
def optimize_block_plan(
    req: OptimizeRequest = OptimizeRequest(),
    current_user: dict = Depends(require_permission("can_optimize")),
    db: Session = Depends(get_db)
):
    """
    Primary Optimization Endpoint for SIH26027 Block Planning.
    Runs Google OR-Tools CP-SAT Solver to generate a feasible and optimal block plan.
    """
    optimizer = RailwayBlockOptimizer(db)
    
    minimize_delays = True
    train_delay_weight = 1.0
    maximize_shadows = True
    shadow_block_weight = 1.0
    prioritize_urgency = True
    urgency_weight = 1.0

    if req.optimization_objectives:
        objs = req.optimization_objectives
        if isinstance(objs, dict):
            minimize_delays = objs.get("minimize_passenger_delays", True)
            train_delay_weight = float(objs.get("train_delay_weight", 1.0))
            maximize_shadows = objs.get("maximize_shadow_blocks", True)
            shadow_block_weight = float(objs.get("shadow_block_weight", 1.0))
            prioritize_urgency = objs.get("prioritize_urgent_maintenance", True)
            urgency_weight = float(objs.get("urgency_weight", 1.0))
        else:
            minimize_delays = getattr(objs, "minimize_passenger_delays", True)
            train_delay_weight = float(getattr(objs, "train_delay_weight", 1.0))
            maximize_shadows = getattr(objs, "maximize_shadow_blocks", True)
            shadow_block_weight = float(getattr(objs, "shadow_block_weight", 1.0))
            prioritize_urgency = getattr(objs, "prioritize_urgent_maintenance", True)
            urgency_weight = float(getattr(objs, "urgency_weight", 1.0))

    # Safe bounds validation
    if train_delay_weight < 0.1 or train_delay_weight > 5.0 or \
       shadow_block_weight < 0.1 or shadow_block_weight > 5.0 or \
       urgency_weight < 0.1 or urgency_weight > 5.0 or \
       req.max_solver_time_sec < 5 or req.max_solver_time_sec > 60:
        raise HTTPException(
            status_code=422,
            detail="Optimization objective weights must be between 0.1 and 5.0, and solver time must be between 5 and 60 seconds."
        )

    raw_result = optimizer.run_optimization(
        max_solver_time_sec=req.max_solver_time_sec,
        minimize_passenger_delays=minimize_delays,
        train_delay_weight=train_delay_weight,
        maximize_shadow_blocks=maximize_shadows,
        shadow_block_weight=shadow_block_weight,
        prioritize_urgent_maintenance=prioritize_urgency,
        urgency_weight=urgency_weight
    )

    # Critical (CRITICAL/HIGH urgency) coverage — computed from real run data
    scheduled_codes = {sb.get("job_code") for sb in raw_result.get("scheduled_blocks", [])}
    crit_jobs = db.query(MaintenanceJob).filter(MaintenanceJob.urgency.in_(["CRITICAL", "HIGH"])).all()
    crit_jobs_total = len(crit_jobs)
    crit_jobs_scheduled = sum(1 for j in crit_jobs if j.job_code in scheduled_codes)

    # Standardized response format matching SIH26027 specifications
    kpis = {
        "total_jobs_considered": raw_result.get("total_jobs", 0),
        "scheduled_jobs_count": raw_result.get("scheduled_jobs_count", 0),
        "unscheduled_jobs_count": raw_result.get("unscheduled_jobs_count", 0),
        "total_maintenance_hours": raw_result.get("total_maintenance_hours", 0.0),
        "total_train_delay_minutes": raw_result.get("train_delay_total_min", 0),
        "block_utilization_pct": raw_result.get("block_utilization_pct", 0.0),
        "shadow_block_synergy_pct": raw_result.get("shadow_block_synergy_pct", 0.0),
        "objective_score": raw_result.get("objective_score", 0.0),
        "solver_time_seconds": raw_result.get("solver_time_seconds", 0.0),
        "critical_jobs_total": crit_jobs_total,
        "critical_jobs_scheduled": crit_jobs_scheduled
    }

    block_assignments = []
    for sb in raw_result.get("scheduled_blocks", []):
        block_assignments.append({
            "block_id": sb.get("id"),
            "job_id": sb.get("job_id"),
            "job_code": sb.get("job_code"),
            "title": sb.get("title"),
            "department": sb.get("department_code"),
            "department_color": sb.get("department_color"),
            "section": sb.get("section_code"),
            "track_line": sb.get("track_line"),
            "start_time": sb.get("start_time_str"),
            "end_time": sb.get("end_time_str"),
            "start_minute": sb.get("start_minute"),
            "end_minute": sb.get("end_minute"),
            "duration_minutes": sb.get("duration_minutes"),
            "is_shadow_block": sb.get("is_shadow_block", False),
            "paired_jobs": sb.get("paired_job_codes", []),
            "resource_assigned": sb.get("resource_assigned"),
            "reason_code": "CRITICAL_WINDOW_ALLOCATED" if not sb.get("is_shadow_block") else "SHADOW_BLOCK_SYNERGY_OPTIMIZED",
            "decision_explanation": sb.get("explanation")
        })

    response = {
        "status": raw_result.get("status"),
        "run_id": raw_result.get("run_id"),
        "timestamp": raw_result.get("timestamp"),
        "optimized_plan": {
            "run_id": raw_result.get("run_id"),
            "status": raw_result.get("status"),
            "solver": "Google OR-Tools CP-SAT"
        },
        "scheduled_jobs": [sb.get("job_code") for sb in raw_result.get("scheduled_blocks", [])],
        "unscheduled_jobs": raw_result.get("unscheduled_jobs", []),
        "block_assignments": block_assignments,
        "conflicts": raw_result.get("conflicts_resolved", []),
        "KPI_values": kpis,
        "reason_codes": raw_result.get("explanations", []),
        
        # Plan quality scorecard & applied preferences
        "plan_quality": raw_result.get("plan_quality"),
        "applied_objectives": raw_result.get("applied_objectives"),

        # Critical coverage aliases for the Block Planning scorecard
        "critical_jobs_total": crit_jobs_total,
        "critical_jobs_scheduled": crit_jobs_scheduled,

        # Backward-compatibility alias fields for existing UI screens
        "scheduled_blocks": raw_result.get("scheduled_blocks", []),
        "total_jobs": raw_result.get("total_jobs", 0),
        "scheduled_jobs_count": raw_result.get("scheduled_jobs_count", 0),
        "unscheduled_jobs_count": raw_result.get("unscheduled_jobs_count", 0),
        "total_maintenance_hours": raw_result.get("total_maintenance_hours", 0.0),
        "train_delay_total_min": raw_result.get("train_delay_total_min", 0),
        "block_utilization_pct": raw_result.get("block_utilization_pct", 0.0),
        "shadow_block_synergy_pct": raw_result.get("shadow_block_synergy_pct", 0.0),
        "objective_score": raw_result.get("objective_score", 0.0),
        "solver_time_seconds": raw_result.get("solver_time_seconds", 0.0),
        "conflicts_resolved": raw_result.get("conflicts_resolved", []),
        "explanations": raw_result.get("explanations", [])
    }
    return response

@router.get("/latest")
def get_latest_optimization(db: Session = Depends(get_db)):
    latest_run = db.query(OptimizationRun).order_by(OptimizationRun.id.desc()).first()
    if not latest_run:
        # Read endpoint must NEVER trigger a solver run as a side effect.
        # Return a clean, honest empty plan and let the UI prompt the operator
        # to run optimization explicitly (POST /api/optimization/run).
        return {
            "status": "NO_RUNS",
            "run_id": None,
            "timestamp": None,
            "optimized_plan": {"run_id": None, "status": "NO_RUNS", "solver": "Google OR-Tools CP-SAT"},
            "scheduled_jobs": [],
            "unscheduled_jobs": [],
            "block_assignments": [],
            "conflicts": [],
            "KPI_values": {
                "total_jobs_considered": 0, "scheduled_jobs_count": 0,
                "unscheduled_jobs_count": 0, "total_maintenance_hours": 0.0,
                "total_train_delay_minutes": 0, "block_utilization_pct": 0.0,
                "shadow_block_synergy_pct": 0.0, "objective_score": 0.0,
                "solver_time_seconds": 0.0
            },
            "reason_codes": [],
            "plan_quality": None,
            "applied_objectives": None,
            "scheduled_blocks": [],
            "total_jobs": 0,
            "scheduled_jobs_count": 0,
            "unscheduled_jobs_count": 0,
            "total_maintenance_hours": 0.0,
            "train_delay_total_min": 0,
            "block_utilization_pct": 0.0,
            "shadow_block_synergy_pct": 0.0,
            "objective_score": 0.0,
            "solver_time_seconds": 0.0,
            "conflicts_resolved": [],
            "explanations": []
        }

    scheduled_blocks_db = db.query(ScheduledBlock).filter(ScheduledBlock.run_id == latest_run.id).all()
    scheduled_blocks = []
    for sb in scheduled_blocks_db:
        j = sb.job
        s_min = sb.start_minute
        e_min = sb.end_minute
        paired_codes = []
        if sb.paired_job_codes_json:
            try:
                paired_codes = json.loads(sb.paired_job_codes_json)
            except Exception:
                paired_codes = []

        scheduled_blocks.append({
            "id": sb.id,
            "job_id": sb.job_id,
            "job_code": j.job_code if j else "JOB",
            "title": j.title if j else "Track Block",
            "department_code": sb.department_code,
            "department_color": j.department.color if j and j.department else "#003366",
            "section_code": sb.section.code if sb.section else "SEC",
            "track_line": sb.track_line.line_code if sb.track_line else "UP_MAIN",
            "start_minute": s_min,
            "end_minute": e_min,
            "start_time_str": f"{(s_min // 60) % 24:02d}:{s_min % 60:02d}",
            "end_time_str": f"{(e_min // 60) % 24:02d}:{e_min % 60:02d}",
            "duration_minutes": sb.duration_minutes,
            "is_shadow_block": sb.is_shadow_block,
            "paired_job_codes": paired_codes,
            "resource_assigned": sb.resource_assigned,
            "affected_trains": [],
            "explanation": f"Scheduled in corridor window on {sb.section.code if sb.section else 'corridor'}."
        })

    # Critical coverage from the active run
    sched_codes = {j.job_code for j in [sb.job for sb in scheduled_blocks_db] if j}
    crit_jobs = db.query(MaintenanceJob).filter(MaintenanceJob.urgency.in_(["CRITICAL", "HIGH"])).all()
    crit_jobs_total = len(crit_jobs)
    crit_jobs_scheduled = sum(1 for j in crit_jobs if j.job_code in sched_codes)

    # Unscheduled jobs
    sched_job_ids = {sb.job_id for sb in scheduled_blocks_db}
    all_jobs = db.query(MaintenanceJob).filter(MaintenanceJob.status != "CANCELLED").all()
    unscheduled = []
    for j in all_jobs:
        if j.id not in sched_job_ids:
            unscheduled.append({
                "job_id": j.id,
                "job_code": j.job_code,
                "title": j.title,
                "department_code": j.department.code if j.department else "ENG",
                "section_code": j.section.code if j.section else "SEC",
                "duration_minutes": j.duration_minutes,
                "priority": j.priority,
                "reason": "Deferred due to high passenger train traffic density during available window.",
                "suggested_alternative": "Reschedule to next day night window (01:30 - 05:30)."
            })

    conflicts_db = db.query(ConflictLog).filter(ConflictLog.run_id == latest_run.id).all()
    conflicts = [{
        "type": c.conflict_type,
        "severity": c.severity,
        "description": c.description,
        "resolution": c.resolution_applied
    } for c in conflicts_db]

    explanations_db = db.query(DecisionExplanation).filter(DecisionExplanation.run_id == latest_run.id).all()
    explanations = [{
        "job_code": e.job.job_code if e.job else f"JOB-{e.job_id}",
        "decision": e.decision_type,
        "reason": e.primary_reason
    } for e in explanations_db]

    total_maint_hours = sum(sb.duration_minutes for sb in scheduled_blocks_db) / 60.0

    kpis = {
        "total_jobs_considered": len(all_jobs),
        "scheduled_jobs_count": latest_run.scheduled_jobs_count,
        "unscheduled_jobs_count": latest_run.unscheduled_jobs_count,
        "total_maintenance_hours": round(total_maint_hours, 1),
        "total_train_delay_minutes": latest_run.train_delay_total_min,
        "block_utilization_pct": round(latest_run.block_utilization_pct, 1),
        "shadow_block_synergy_pct": round(latest_run.shadow_block_synergy_pct, 1),
        "objective_score": latest_run.objective_score or 0.0,
        "solver_time_seconds": round(latest_run.solver_time_seconds, 2),
        "critical_jobs_total": crit_jobs_total,
        "critical_jobs_scheduled": crit_jobs_scheduled
    }

    return {
        "status": latest_run.status,
        "run_id": latest_run.id,
        "timestamp": latest_run.run_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "optimized_plan": {
            "run_id": latest_run.id,
            "status": latest_run.status,
            "solver": "Google OR-Tools CP-SAT"
        },
        "scheduled_jobs": [sb["job_code"] for sb in scheduled_blocks],
        "unscheduled_jobs": unscheduled,
        "block_assignments": scheduled_blocks,
        "conflicts": conflicts,
        "KPI_values": kpis,
        "reason_codes": explanations,
        "critical_jobs_total": crit_jobs_total,
        "critical_jobs_scheduled": crit_jobs_scheduled,

        # Compatibility aliases
        "scheduled_blocks": scheduled_blocks,
        "total_jobs": len(all_jobs),
        "scheduled_jobs_count": latest_run.scheduled_jobs_count,
        "unscheduled_jobs_count": latest_run.unscheduled_jobs_count,
        "total_maintenance_hours": round(total_maint_hours, 1),
        "train_delay_total_min": latest_run.train_delay_total_min,
        "block_utilization_pct": round(latest_run.block_utilization_pct, 1),
        "shadow_block_synergy_pct": round(latest_run.shadow_block_synergy_pct, 1),
        "objective_score": latest_run.objective_score or 0.0,
        "solver_time_seconds": round(latest_run.solver_time_seconds, 2),
        "conflicts_resolved": conflicts,
        "explanations": explanations
    }

@router.get("/explanation/{job_code}")
def get_decision_explanation(
    job_code: str,
    run_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Return explanation tree for why a job was scheduled or deferred.
    Includes hard constraint checks, priority reason, shadow block info, and deferred reason codes.
    """
    explainer = DecisionExplainer(db)
    return explainer.explain_job_decision(job_code, run_id=run_id)


@router.get("/run/{run_id}")
def get_optimization_run_by_id(run_id: int, db: Session = Depends(get_db)):
    """Fetch a specific optimization run result by run_id."""
    run = db.query(OptimizationRun).filter(OptimizationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Optimization run {run_id} not found")

    scheduled_blocks_db = db.query(ScheduledBlock).filter(ScheduledBlock.run_id == run_id).all()
    import json as _json
    scheduled_blocks = []
    for sb in scheduled_blocks_db:
        j = sb.job
        try:
            paired_codes = _json.loads(sb.paired_job_codes_json) if sb.paired_job_codes_json else []
        except Exception:
            paired_codes = []
        scheduled_blocks.append({
            "id": sb.id,
            "job_id": sb.job_id,
            "job_code": j.job_code if j else "JOB",
            "title": j.title if j else "Track Block",
            "department_code": sb.department_code,
            "section_code": sb.section.code if sb.section else "SEC",
            "track_line": sb.track_line.line_code if sb.track_line else "UP_MAIN",
            "start_minute": sb.start_minute,
            "end_minute": sb.end_minute,
            "start_time_str": f"{(sb.start_minute // 60) % 24:02d}:{sb.start_minute % 60:02d}",
            "end_time_str": f"{(sb.end_minute // 60) % 24:02d}:{sb.end_minute % 60:02d}",
            "duration_minutes": sb.duration_minutes,
            "is_shadow_block": sb.is_shadow_block,
            "paired_job_codes": paired_codes,
            "resource_assigned": sb.resource_assigned,
        })

    return {
        "run_id": run.id,
        "status": run.status,
        "timestamp": run.run_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_jobs_count": run.scheduled_jobs_count,
        "unscheduled_jobs_count": run.unscheduled_jobs_count,
        "train_delay_total_min": run.train_delay_total_min,
        "block_utilization_pct": run.block_utilization_pct,
        "shadow_block_synergy_pct": run.shadow_block_synergy_pct,
        "scheduled_blocks": scheduled_blocks,
    }


@router.get("/rules")
def get_railway_rules():
    from ..optimizer.rules_loader import rules_loader
    return rules_loader.raw_rules

import re
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from ..database import get_db
from ..models.models import MaintenanceJob, Department, Section, TrackLine
from ..schemas.schemas import MaintenanceJobCreate, MaintenanceJobResponse, DepartmentResponse, SectionResponse
from ..services.duration_predictor import duration_predictor
from .auth import get_current_user, validate_department_scope, _decode_token

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


# ---------------------------------------------------------------------------
# Server-side job code generation (authoritative — never trusts the client)
# ---------------------------------------------------------------------------
def _generate_job_code(db: Session, department_code: str) -> str:
    """
    Deterministically generate a UNIQUE job code for the given department
    by scanning existing codes and taking the next sequence number.
      ENG  -> JOB-ENG-<n>   (seed range 101-106)
      TRD  -> JOB-TRD-<n>   (seed range 201-204)
      S_T  -> JOB-ST-<n>    (seed range 301-305)
      MECH -> JOB-MECH-<n>  (seed range 401)
    """
    dept_upper = (department_code or "ENG").upper()
    prefix_groups = {
        "ENG": ["ENG"],
        "TRD": ["TRD"],
        "S_T": ["ST", "S_T", "S&T"],
        "MECH": ["MECH"],
    }
    prefixes = prefix_groups.get(dept_upper, [dept_upper])
    base_seq = {"ENG": 100, "TRD": 200, "S_T": 300, "MECH": 400}.get(dept_upper, 100)

    max_seq = 0
    for j in db.query(MaintenanceJob.job_code).all():
        code = (j[0] or "")
        for p in prefixes:
            marker = f"JOB-{p}-"
            if code.startswith(marker):
                m = re.match(rf"^{re.escape(marker)}(\d+)$", code)
                if m:
                    max_seq = max(max_seq, int(m.group(1)))
    next_seq = max(max_seq + 1, base_seq + 1)
    prefix = "ST" if dept_upper == "S_T" else dept_upper
    return f"JOB-{prefix}-{next_seq}"


class MaintenanceJobUpdate(BaseModel):
    status: Optional[str] = None        # PENDING, APPROVED, DEFERRED, SCHEDULED, CANCELLED
    urgency: Optional[str] = None       # CRITICAL, HIGH, MEDIUM, ROUTINE
    priority: Optional[int] = None      # 1-5
    duration_minutes: Optional[int] = None
    description: Optional[str] = None
    requested_date: Optional[str] = None


class DurationPredictRequest(BaseModel):
    department_code: str = "ENG"
    urgency: str = "MEDIUM"
    duration_minutes: Optional[int] = None
    requires_power_block: bool = False
    resource_type: Optional[str] = "CREW"
    section_length_km: Optional[float] = 15.0
    weather_factor: Optional[float] = 1.0


@router.post("/predict-duration")
def predict_maintenance_duration(req: DurationPredictRequest) -> Dict[str, Any]:
    """
    AI Preparation Interface: predict maintenance duration using deterministic baseline.
    modelStatus=DETERMINISTIC_BASELINE — not ML yet. Returns predictedDuration, bounds, confidence.
    PROTOTYPE_ASSUMPTION: All factors are engineering estimates pending domain validation.
    """
    job_data = {
        "department_code": req.department_code,
        "urgency": req.urgency,
        "duration_minutes": req.duration_minutes or 0,
        "requires_power_block": req.requires_power_block,
        "resource_type": req.resource_type or "CREW",
    }
    context = {
        "section_length_km": req.section_length_km or 15.0,
        "weather_factor": req.weather_factor or 1.0,
    }
    return duration_predictor.predict(job_data, context)


@router.get("/departments", response_model=List[DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    return db.query(Department).all()

@router.get("/sections", response_model=List[SectionResponse])
def get_sections(db: Session = Depends(get_db)):
    return db.query(Section).all()

@router.get("/requests", response_model=List[MaintenanceJobResponse])
def get_maintenance_requests(
    department: Optional[str] = Query(None, description="Filter by department code (ENG, S_T, TRD)"),
    section: Optional[str] = Query(None, description="Filter by section code"),
    urgency: Optional[str] = Query(None, description="Filter by urgency (CRITICAL, HIGH, MEDIUM, ROUTINE)"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, SCHEDULED, DEFERRED)"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    # Server-side department scoping: field roles can ONLY ever see their own
    # department's requests, regardless of the query parameter they pass.
    user_role = ""
    if authorization and authorization.startswith("Bearer "):
        profile = _decode_token(authorization[len("Bearer "):].strip())
        if isinstance(profile, dict):
            user_role = profile.get("role", "").upper()
    role_dept_map = {"ENGINEER": "ENG", "TRD_OFFICER": "TRD", "ST_OFFICER": "S_T"}
    role_dept = role_dept_map.get(user_role)
    if role_dept:
        department = role_dept

    query = db.query(MaintenanceJob)
    if department:
        dept = db.query(Department).filter(Department.code == department).first()
        if dept:
            query = query.filter(MaintenanceJob.department_id == dept.id)
    if section:
        sec = db.query(Section).filter(Section.code == section).first()
        if sec:
            query = query.filter(MaintenanceJob.section_id == sec.id)
    if urgency:
        query = query.filter(MaintenanceJob.urgency == urgency)
    if status:
        query = query.filter(MaintenanceJob.status == status)

    jobs = query.order_by(MaintenanceJob.priority.desc(), MaintenanceJob.id.desc()).all()
    results = []
    for j in jobs:
        results.append(MaintenanceJobResponse(
            id=int(j.id),
            job_code=str(j.job_code),
            title=str(j.title),
            department_code=str(j.department.code) if j.department else "ENG",
            department_name=str(j.department.name) if j.department else "Civil Engineering",
            section_code=str(j.section.code) if j.section else "UNKNOWN",
            track_line=str(j.track_line.line_code) if j.track_line else "UP_MAIN",
            duration_minutes=int(j.duration_minutes),
            priority=int(j.priority),
            urgency=str(j.urgency),
            requires_power_block=bool(j.requires_power_block),
            requires_traffic_block=bool(j.requires_traffic_block),
            requires_speed_restriction=bool(j.requires_speed_restriction),
            speed_restriction_kmh=int(j.speed_restriction_kmh) if j.speed_restriction_kmh is not None else None,
            status=str(j.status),
            requested_date=str(j.requested_date),
            earliest_start_minute=int(j.earliest_start_minute),
            latest_end_minute=int(j.latest_end_minute),
            description=str(j.description) if j.description else None
        ))
    return results

@router.post("/requests", response_model=MaintenanceJobResponse)
def create_maintenance_request(
    job_in: MaintenanceJobCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Server-side department validation derived strictly from authenticated user token
    validate_department_scope(current_user, job_in.department_code)

    # Job code is generated authoritatively by the backend when not supplied,
    # guaranteeing real, unique codes for every newly created record.
    job_code = (job_in.job_code or "").strip() or _generate_job_code(db, job_in.department_code)

    existing = db.query(MaintenanceJob).filter(MaintenanceJob.job_code == job_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Maintenance job with code '{job_code}' already exists.")

    dept = db.query(Department).filter(Department.code == job_in.department_code).first()
    if not dept:
        raise HTTPException(status_code=400, detail=f"Department '{job_in.department_code}' not found.")
    
    sec = db.query(Section).filter(Section.code == job_in.section_code).first()
    if not sec:
        raise HTTPException(status_code=400, detail=f"Section '{job_in.section_code}' not found.")

    track_line = None
    if job_in.track_line:
        track_line = db.query(TrackLine).filter(
            TrackLine.section_id == sec.id,
            TrackLine.line_code.like(f"%{job_in.track_line}%")
        ).first()

    new_job = MaintenanceJob(
        job_code=job_code,
        title=job_in.title,
        department_id=dept.id,
        section_id=sec.id,
        track_line_id=track_line.id if track_line else None,
        duration_minutes=job_in.duration_minutes,
        priority=job_in.priority,
        urgency=job_in.urgency,
        requires_power_block=job_in.requires_power_block,
        requires_traffic_block=job_in.requires_traffic_block,
        requires_speed_restriction=job_in.requires_speed_restriction,
        speed_restriction_kmh=job_in.speed_restriction_kmh,
        requested_date=job_in.requested_date or "2026-09-01",
        earliest_start_minute=job_in.earliest_start_minute or 0,
        latest_end_minute=job_in.latest_end_minute or 1440,
        description=job_in.description,
        status="PENDING"
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return MaintenanceJobResponse(
        id=int(new_job.id),
        job_code=str(new_job.job_code),
        title=str(new_job.title),
        department_code=str(dept.code),
        department_name=str(dept.name),
        section_code=str(sec.code),
        track_line=str(track_line.line_code) if track_line else "UP_MAIN",
        duration_minutes=int(new_job.duration_minutes),
        priority=int(new_job.priority),
        urgency=str(new_job.urgency),
        requires_power_block=bool(new_job.requires_power_block),
        requires_traffic_block=bool(new_job.requires_traffic_block),
        requires_speed_restriction=bool(new_job.requires_speed_restriction),
        speed_restriction_kmh=int(new_job.speed_restriction_kmh) if new_job.speed_restriction_kmh is not None else None,
        status=str(new_job.status),
        requested_date=str(new_job.requested_date),
        earliest_start_minute=int(new_job.earliest_start_minute),
        latest_end_minute=int(new_job.latest_end_minute),
        description=str(new_job.description) if new_job.description else None
    )


@router.put("/requests/{job_id}", response_model=MaintenanceJobResponse)
def update_maintenance_request(
    job_id: str,
    update_data: MaintenanceJobUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update status, urgency, priority, or duration of a maintenance request.
    Used by Approve / Defer / Edit actions in the frontend.
    Supports lookup by numeric ID (e.g., 1) or job code (e.g., 'JOB-ENG-101').
    Enforces server-side role and department permissions.
    """
    job = None
    try:
        job_id_int = int(job_id)
        job = db.query(MaintenanceJob).filter(MaintenanceJob.id == job_id_int).first()
    except (ValueError, TypeError):
        pass
    if not job:
        job = db.query(MaintenanceJob).filter(MaintenanceJob.job_code == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail=f"Maintenance job '{job_id}' not found.")

    dept_code = job.department.code if job.department else "ENG"

    # Status changes to APPROVED or DEFERRED require can_approve permission (Controller/Planner)
    if update_data.status is not None:
        if update_data.status in ("APPROVED", "DEFERRED", "SCHEDULED") and not current_user.get("can_approve", False):
            role_name = current_user.get("role", "UNKNOWN")
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: Role '{role_name}' is not authorized to approve or defer maintenance requests."
            )
        # Any status update by field roles must also belong to their designated department
        validate_department_scope(current_user, dept_code)
    else:
        # Non-status updates (urgency, priority, duration, etc.) by field roles must belong to their department
        validate_department_scope(current_user, dept_code)

    # Apply only the fields that were provided
    if update_data.status is not None:
        valid_statuses = {"PENDING", "APPROVED", "DEFERRED", "SCHEDULED", "CANCELLED"}
        if update_data.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status '{update_data.status}'.")
        job.status = update_data.status  # type: ignore

    if update_data.urgency is not None:
        valid_urgency = {"CRITICAL", "HIGH", "MEDIUM", "ROUTINE"}
        if update_data.urgency not in valid_urgency:
            raise HTTPException(status_code=400, detail=f"Invalid urgency '{update_data.urgency}'.")
        job.urgency = update_data.urgency  # type: ignore

    if update_data.priority is not None:
        if not (1 <= update_data.priority <= 5):
            raise HTTPException(status_code=400, detail="Priority must be between 1 and 5.")
        job.priority = update_data.priority  # type: ignore

    if update_data.duration_minutes is not None:
        if update_data.duration_minutes < 15:
            raise HTTPException(status_code=400, detail="Duration must be at least 15 minutes.")
        job.duration_minutes = update_data.duration_minutes  # type: ignore

    if update_data.description is not None:
        job.description = update_data.description  # type: ignore

    if update_data.requested_date is not None:
        job.requested_date = update_data.requested_date  # type: ignore

    db.commit()
    db.refresh(job)

    return MaintenanceJobResponse(
        id=int(job.id),
        job_code=str(job.job_code),
        title=str(job.title),
        department_code=str(job.department.code) if job.department else "ENG",
        department_name=str(job.department.name) if job.department else "Civil Engineering",
        section_code=str(job.section.code) if job.section else "UNKNOWN",
        track_line=str(job.track_line.line_code) if job.track_line else "UP_MAIN",
        duration_minutes=int(job.duration_minutes),
        priority=int(job.priority),
        urgency=str(job.urgency),
        requires_power_block=bool(job.requires_power_block),
        requires_traffic_block=bool(job.requires_traffic_block),
        requires_speed_restriction=bool(job.requires_speed_restriction),
        speed_restriction_kmh=int(job.speed_restriction_kmh) if job.speed_restriction_kmh is not None else None,
        status=str(job.status),
        requested_date=str(job.requested_date),
        earliest_start_minute=int(job.earliest_start_minute),
        latest_end_minute=int(job.latest_end_minute),
        description=str(job.description) if job.description else None
    )


@router.delete("/requests/{job_id}")
def delete_maintenance_request(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a maintenance job by numeric ID or job code.
    Used by the Delete action in the Maintenance Requests frontend table.
    Enforces that field roles can only delete requests in their department.
    """
    job = None
    try:
        job_id_int = int(job_id)
        job = db.query(MaintenanceJob).filter(MaintenanceJob.id == job_id_int).first()
    except (ValueError, TypeError):
        pass
    if not job:
        job = db.query(MaintenanceJob).filter(MaintenanceJob.job_code == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail=f"Maintenance job '{job_id}' not found.")

    dept_code = job.department.code if job.department else "ENG"
    # Controllers / Planners can delete any request; Field roles can only delete within authorized department
    validate_department_scope(current_user, dept_code)

    db.delete(job)
    db.commit()
    return {
        "status": "deleted",
        "job_id": job_id,
        "job_code": job.job_code,
        "message": f"Maintenance job '{job.job_code}' has been permanently deleted."
    }

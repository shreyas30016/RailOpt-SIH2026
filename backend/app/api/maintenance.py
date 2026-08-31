from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.models import MaintenanceJob, Department, Section, TrackLine
from ..schemas.schemas import MaintenanceJobCreate, MaintenanceJobResponse, DepartmentResponse, SectionResponse

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])

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
    db: Session = Depends(get_db)
):
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
    return results

@router.post("/requests", response_model=MaintenanceJobResponse)
def create_maintenance_request(job_in: MaintenanceJobCreate, db: Session = Depends(get_db)):
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
        job_code=job_in.job_code,
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
        id=new_job.id,
        job_code=new_job.job_code,
        title=new_job.title,
        department_code=dept.code,
        department_name=dept.name,
        section_code=sec.code,
        track_line=track_line.line_code if track_line else "UP_MAIN",
        duration_minutes=new_job.duration_minutes,
        priority=new_job.priority,
        urgency=new_job.urgency,
        requires_power_block=new_job.requires_power_block,
        requires_traffic_block=new_job.requires_traffic_block,
        requires_speed_restriction=new_job.requires_speed_restriction,
        speed_restriction_kmh=new_job.speed_restriction_kmh,
        status=new_job.status,
        requested_date=new_job.requested_date,
        earliest_start_minute=new_job.earliest_start_minute,
        latest_end_minute=new_job.latest_end_minute,
        description=new_job.description
    )

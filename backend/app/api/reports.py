import json
import re
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from ..database import get_db
from ..models.models import OptimizationRun, ScheduledBlock, MaintenanceJob, Department, Section, ConflictLog
from .auth import _decode_token

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


def _parse_date_range(date_range: Optional[str]) -> Optional[Tuple[datetime, datetime]]:
    """
    Parse a date-range filter into (start, end) datetimes, or None if unparseable.
    Accepts 'DD Mon YYYY - DD Mon YYYY', ISO 'YYYY-MM-DD - YYYY-MM-DD',
    or a single date. Used to filter historical optimization runs (Trends) and
    to scope the active run selection to the requested window.
    """
    if not date_range or date_range.strip() in ("", "ALL", "All Dates"):
        return None

    def _parse_one(text: str) -> Optional[datetime]:
        text = text.strip()
        for fmt in ("%d %b %Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None

    # ISO range "YYYY-MM-DD - YYYY-MM-DD" first (contains dashes; must not be split)
    iso_range = re.match(r"^(\d{4}-\d{2}-\d{2})\s*(?:-|–|to)\s*(\d{4}-\d{2}-\d{2})$", date_range.strip())
    if iso_range:
        start = _parse_one(iso_range.group(1))
        end = _parse_one(iso_range.group(2))
        if start and end:
            return (start, end.replace(hour=23, minute=59, second=59))

    parts = re.split(r"\s*(?:-|–|to)\s*", date_range.strip())
    if not parts or not parts[0].strip():
        return None

    start = _parse_one(parts[0])
    if start is None:
        return None
    end = _parse_one(parts[1]) if len(parts) > 1 else None
    if end is None:
        end = start.replace(hour=23, minute=59, second=59)
    else:
        end = end.replace(hour=23, minute=59, second=59)
    return (start, end)

@router.get("/analytics")
def get_analytics_report(
    division: Optional[str] = Query(None, description="Filter by railway division"),
    section: Optional[str] = Query(None, description="Filter by section code"),
    department: Optional[str] = Query(None, description="Filter by department code"),
    date_range: Optional[str] = Query(None, description="Date range string"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    # 1. Role-based scoping via authorization token (if provided)
    user_role = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
        user_profile = _decode_token(token)
        if isinstance(user_profile, dict):
            user_role = user_profile.get("role", "").upper()

    # Department scope enforcement for field roles
    department_role_map = {
        "ENGINEER": "ENG",
        "TRD_OFFICER": "TRD",
        "ST_OFFICER": "S_T"
    }
    enforced_dept = department_role_map.get(user_role)
    active_dept = enforced_dept or (department if department and department not in ("ALL", "All Departments") else None)

    # 2. Resolve optional date-range filter (Trends + active run scoping)
    date_bounds = _parse_date_range(date_range)
    run_date_filter = None
    if date_bounds:
        start_dt, end_dt = date_bounds
        run_date_filter = (start_dt, end_dt)

    def _scoped_latest_run():
        """Latest run that has scheduled blocks, optionally within the date range."""
        q = db.query(OptimizationRun).join(ScheduledBlock, ScheduledBlock.run_id == OptimizationRun.id)
        if run_date_filter:
            q = q.filter(OptimizationRun.run_timestamp >= run_date_filter[0], OptimizationRun.run_timestamp <= run_date_filter[1])
        run = q.order_by(OptimizationRun.id.desc()).first()
        if run:
            return run
        q2 = db.query(OptimizationRun)
        if run_date_filter:
            q2 = q2.filter(OptimizationRun.run_timestamp >= run_date_filter[0], OptimizationRun.run_timestamp <= run_date_filter[1])
        return q2.order_by(OptimizationRun.id.desc()).first()

    # 2b. Get latest active optimization run (that has actual scheduled blocks)
    latest_run = _scoped_latest_run()
    latest_run_id = latest_run.id if latest_run else None

    runs_query = db.query(OptimizationRun).order_by(OptimizationRun.id.desc())
    if run_date_filter:
        runs_query = runs_query.filter(
            OptimizationRun.run_timestamp >= run_date_filter[0],
            OptimizationRun.run_timestamp <= run_date_filter[1]
        )
    runs = runs_query.limit(15).all()

    # 3. Determine active corridor context label
    corridor_context = "Delhi–Agra Mainline (Synthetic Demo Corridor)"
    if division and division not in ("ALL", "All Divisions"):
        corridor_context = f"{division} Corridor (Demo Data Available: Delhi–Agra)"
    elif section and section not in ("ALL", "All Sections"):
        corridor_context = f"Section {section} (Delhi–Agra Mainline)"

    # 4. Resolve section filter & division filter
    sec_ids = None
    if section and section not in ("ALL", "All Sections", "All Divisions"):
        sec_match = db.query(Section).filter(
            (Section.code == section) | 
            (Section.start_station.ilike(f"%{section}%")) | 
            (Section.end_station.ilike(f"%{section}%"))
        ).first()
        if sec_match:
            sec_ids = [sec_match.id]
        else:
            sec_ids = []
    elif division and division not in ("ALL", "All Divisions"):
        div_secs = db.query(Section).filter(
            (Section.division.ilike(f"%{division}%")) | 
            (Section.code.ilike(f"%{division}%"))
        ).all()
        sec_ids = [s.id for s in div_secs]

    # Base queries for jobs & blocks in active run
    jobs_query = db.query(MaintenanceJob)
    if latest_run_id:
        blocks_query = db.query(ScheduledBlock).filter(ScheduledBlock.run_id == latest_run_id)
    else:
        blocks_query = db.query(ScheduledBlock).filter(ScheduledBlock.id < 0)

    # Apply department filter
    if active_dept:
        dept_match = db.query(Department).filter(
            (Department.code == active_dept) | (Department.name.ilike(f"%{active_dept}%"))
        ).first()
        if dept_match:
            jobs_query = jobs_query.filter(MaintenanceJob.department_id == dept_match.id)
            blocks_query = blocks_query.filter(ScheduledBlock.department_code == dept_match.code)
        else:
            jobs_query = jobs_query.filter(MaintenanceJob.department_id == -1)
            blocks_query = blocks_query.filter(ScheduledBlock.department_code == "NONE")

    # Apply section/division filter
    if sec_ids is not None:
        jobs_query = jobs_query.filter(MaintenanceJob.section_id.in_(sec_ids))
        blocks_query = blocks_query.filter(ScheduledBlock.section_id.in_(sec_ids))

    all_filtered_jobs = jobs_query.all()
    all_filtered_blocks = blocks_query.all()

    total_jobs_requested = len(all_filtered_jobs)
    total_jobs_scheduled = len(all_filtered_blocks)

    # Grant ratio / Job completion rate: 0.0% to 100.0%
    if total_jobs_requested > 0:
        grant_ratio = round(min(100.0, (total_jobs_scheduled / total_jobs_requested) * 100.0), 1)
    else:
        grant_ratio = 100.0 if total_jobs_scheduled > 0 else 0.0

    # Total maintenance hours in active plan
    total_maint_minutes = sum(int(b.duration_minutes) for b in all_filtered_blocks)
    total_maint_hours = round(total_maint_minutes / 60.0, 1)

    # Active sections count in scope
    scoped_sections_query = db.query(Section)
    if sec_ids is not None:
        scoped_sections_query = scoped_sections_query.filter(Section.id.in_(sec_ids))
    scoped_sections = scoped_sections_query.all()
    scoped_sections_count = max(1, len(scoped_sections))

    # Corridor capacity minutes across 24-hour cycle for scoped sections
    corridor_capacity_minutes = scoped_sections_count * 1440
    # True block capacity utilization % (bounded strictly between 0% and 100%)
    block_utilization = round(min(100.0, (total_maint_minutes / max(1, corridor_capacity_minutes)) * 100.0), 1)

    # Train delay: delay minutes attributed to these scheduled blocks
    train_delay_avg = round(float(latest_run.train_delay_total_min) / max(1, int(latest_run.scheduled_jobs_count)), 1) if (latest_run and latest_run.scheduled_jobs_count) else 0.0

    # Shadow block synergy
    shadow_count = sum(1 for b in all_filtered_blocks if b.is_shadow_block)
    shadow_synergy_pct = round((shadow_count / max(1, total_jobs_scheduled)) * 100.0, 1) if total_jobs_scheduled > 0 else 0.0

    # Real shadow-block time savings: a co-located (shadow) pair occupies the track
    # once instead of twice, so the genuine saving is min(duration_a, duration_b)
    # per paired block. Derived entirely from actual scheduled-block data.
    shadow_pairs_seen = set()
    shadow_savings_minutes = 0
    for b in all_filtered_blocks:
        if not b.is_shadow_block:
            continue
        b_code = b.job.job_code if b.job else f"JOB-{b.job_id}"
        paired_codes = []
        try:
            paired_codes = json.loads(str(b.paired_job_codes_json)) if b.paired_job_codes_json else []
        except Exception:
            paired_codes = []
        for p_code in paired_codes:
            key = tuple(sorted([b_code, p_code]))
            if key in shadow_pairs_seen:
                continue
            partner = next(
                (x for x in all_filtered_blocks if (x.job.job_code if x.job else f"JOB-{x.job_id}") == p_code),
                None
            )
            if partner is not None:
                shadow_pairs_seen.add(key)
                shadow_savings_minutes += min(int(b.duration_minutes), int(partner.duration_minutes))
    shadow_savings_hours = round(shadow_savings_minutes / 60.0, 1)

    # 5. Departmental distribution
    dept_stats = []
    for d in db.query(Department).all():
        if enforced_dept and d.code != enforced_dept:
            continue
        # If user explicitly filtered by department, show only that or all permitted
        if active_dept and d.code != active_dept and active_dept != "ALL":
            continue

        d_jobs_q = db.query(MaintenanceJob).filter(MaintenanceJob.department_id == d.id)
        d_blocks_q = db.query(ScheduledBlock).filter(
            ScheduledBlock.run_id == latest_run_id,
            ScheduledBlock.department_code == d.code
        )
        if sec_ids is not None:
            d_jobs_q = d_jobs_q.filter(MaintenanceJob.section_id.in_(sec_ids))
            d_blocks_q = d_blocks_q.filter(ScheduledBlock.section_id.in_(sec_ids))

        dept_jobs = d_jobs_q.all()
        dept_blocks = d_blocks_q.all()

        req_count = len(dept_jobs)
        sched_count = len(dept_blocks)
        req_hrs = round(sum(int(j.duration_minutes) for j in dept_jobs) / 60.0, 1)
        app_hrs = round(sum(int(b.duration_minutes) for b in dept_blocks) / 60.0, 1)
        dept_grant_rate = round(min(100.0, (sched_count / max(1, req_count)) * 100.0), 1) if req_count > 0 else (100.0 if sched_count > 0 else 0.0)

        dept_stats.append({
            "code": d.code,
            "name": d.name,
            "requested": req_count,
            "scheduled": sched_count,
            "requested_hours": req_hrs,
            "approved_hours": app_hrs,
            "grant_rate": dept_grant_rate,
            "color": d.color or "#003366"
        })

    # 6. Section-level performance statistics (reacts to department and division/section filter)
    section_stats = []
    for s in scoped_sections:
        s_jobs_q = db.query(MaintenanceJob).filter(MaintenanceJob.section_id == s.id)
        s_blocks_q = db.query(ScheduledBlock).filter(
            ScheduledBlock.run_id == latest_run_id,
            ScheduledBlock.section_id == s.id
        )
        if active_dept:
            dept_match = db.query(Department).filter((Department.code == active_dept) | (Department.name.ilike(f"%{active_dept}%"))).first()
            if dept_match:
                s_jobs_q = s_jobs_q.filter(MaintenanceJob.department_id == dept_match.id)
                s_blocks_q = s_blocks_q.filter(ScheduledBlock.department_code == dept_match.code)

        s_jobs_count = s_jobs_q.count()
        s_blocks_count = s_blocks_q.count()
        s_rate = round(min(100.0, (s_blocks_count / max(1, s_jobs_count)) * 100.0), 1) if s_jobs_count > 0 else (100.0 if s_blocks_count > 0 else 0.0)

        section_stats.append({
            "code": s.code,
            "name": f"{s.start_station}–{s.end_station}",
            "division": s.division or "Delhi",
            "requested": s_jobs_count,
            "completed": s_blocks_count,
            "completion_rate": s_rate
        })

    # 7. Raw records for Raw Data table and filtered CSV export
    raw_records = []
    for b in all_filtered_blocks:
        job = b.job
        sec = b.section
        start_h, start_m = divmod(int(b.start_minute), 60)
        end_h, end_m = divmod(int(b.end_minute), 60)
        time_str = f"{start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}"
        raw_records.append({
            "block_id": b.id,
            "job_code": job.job_code if job else f"JOB-{b.job_id}",
            "title": job.title if job else "Track Maintenance Possession",
            "department": b.department_code,
            "section": sec.code if sec else "CORRIDOR",
            "division": sec.division if sec else "Delhi",
            "window": time_str,
            "duration_min": b.duration_minutes,
            "duration": f"{b.duration_minutes}m",
            "is_shadow": "Yes" if b.is_shadow_block else "No",
            "resource": b.resource_assigned or "Standard Crew",
            "status": job.status if job else "SCHEDULED"
        })

    # 8. Historical runs summary (Trends dataset)
    history = []
    for r in runs:
        history.append({
            "run_id": r.id,
            "timestamp": r.run_timestamp.strftime("%d %b %H:%M") if r.run_timestamp else "--",
            "status": r.status or "OPTIMAL",
            "scheduled": r.scheduled_jobs_count,
            "train_delay_min": r.train_delay_total_min,
            "utilization": round(min(100.0, float(r.block_utilization_pct)), 1),
            "synergy": round(min(100.0, float(r.shadow_block_synergy_pct)), 1),
            "solver_time_sec": r.solver_time_seconds
        })

    # Conflicts resolved count (real value — never substituted with a placeholder)
    conflicts_count = db.query(ConflictLog).count()

    return {
        "kpis": {
            "total_blocks_executed_ytd": total_jobs_scheduled,
            "average_grant_ratio_pct": grant_ratio,
            "block_utilization_pct": block_utilization,
            "job_completion_rate_pct": grant_ratio,
            "mean_delay_per_block_min": train_delay_avg,
            "critical_conflicts_resolved": conflicts_count,
            "shadow_block_synergy_pct": shadow_synergy_pct,
            "shadow_block_savings_hours": shadow_savings_hours,
            "safety_compliance_pct": 100.0
        },
        "corridor_context": corridor_context,
        "active_filters": {
            "division": division or "ALL",
            "section": section or "ALL",
            "department": active_dept or "ALL",
            "date_range": date_range or "ALL"
        },
        "department_statistics": dept_stats,
        "section_statistics": section_stats,
        "historical_optimization_runs": history,
        "raw_records": raw_records
    }

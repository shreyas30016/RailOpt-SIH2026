import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from ..database import get_db
from ..models.models import Section, TrackLine, ScheduledBlock, TrainSchedule, OptimizationRun, BlockWindow
from ..services.train_adapter import train_adapter

router = APIRouter(prefix="/gantt", tags=["Gantt Timeline"])

@router.get("/timeline")
def get_gantt_timeline_data(
    run_id: int | None = None,
    db: Session = Depends(get_db)
):
    """
    Return Gantt timeline data for a specific optimization run (or latest if run_id omitted).
    Includes track-line block assignments, train paths, and corridor windows.
    """
    if run_id:
        run = db.query(OptimizationRun).filter(OptimizationRun.id == run_id).first()
    else:
        run = db.query(OptimizationRun).order_by(OptimizationRun.id.desc()).first()

    sections = db.query(Section).all()
    track_lines = db.query(TrackLine).all()
    trains = db.query(TrainSchedule).all()
    windows = db.query(BlockWindow).all()
    
    scheduled_blocks = []
    if run:
        scheduled_blocks = db.query(ScheduledBlock).filter(ScheduledBlock.run_id == run.id).all()

    # Tracks / Resources structure
    timeline_tracks = []
    for sec in sections:
        sec_tracks = [tl for tl in track_lines if tl.section_id == sec.id]
        for tl in sec_tracks:
            # Get blocks on this track line
            tl_blocks = []
            for sb in scheduled_blocks:
                if sb.track_line_id == tl.id:
                    j = sb.job
                    paired_codes = []
                    if sb.paired_job_codes_json:
                        try:
                            paired_codes = json.loads(str(sb.paired_job_codes_json))
                        except Exception:
                            paired_codes = []

                    tl_blocks.append({
                        "id": sb.id,
                        "job_id": sb.job_id,
                        "job_code": j.job_code if j else "JOB",
                        "title": j.title if j else "Track Block",
                        "department": sb.department_code,
                        "color": j.department.color if j and j.department else "#003366",
                        "start_minute": int(sb.start_minute),
                        "end_minute": int(sb.end_minute),
                        "start_time_str": f"{(int(sb.start_minute) // 60) % 24:02d}:{int(sb.start_minute) % 60:02d}",
                        "end_time_str": f"{(int(sb.end_minute) // 60) % 24:02d}:{int(sb.end_minute) % 60:02d}",
                        "is_shadow": sb.is_shadow_block,
                        "paired_jobs": paired_codes,
                        "resource": sb.resource_assigned,
                        "explanation": f"Scheduled {(int(sb.start_minute) // 60) % 24:02d}:{int(sb.start_minute) % 60:02d}–{(int(sb.end_minute) // 60) % 24:02d}:{int(sb.end_minute) % 60:02d} on {sec.code}."
                    })

            timeline_tracks.append({
                "section_id": sec.id,
                "section_code": sec.code,
                "track_line_id": tl.id,
                "track_line_code": tl.line_code,
                "line_type": tl.line_type,
                "label": f"{sec.code} ({tl.line_code})",
                "blocks": tl_blocks
            })

    # Train paths formatted for timeline overlay from live train adapter
    live_data = train_adapter.get_movements()
    train_paths = []
    for tr in live_data.get("movements", []):
        train_paths.append({
            "train_number": tr.get("train_id"),
            "train_name": tr.get("train_name"),
            "train_type": tr.get("train_type"),
            "priority": tr.get("priority_weight"),
            "direction": tr.get("direction"),
            "departure_minute": tr.get("estimated_departure_min"),
            "arrival_minute": tr.get("estimated_arrival_min"),
            "departure_time_str": tr.get("estimated_departure_str"),
            "arrival_time_str": tr.get("estimated_arrival_str"),
            "delay_minutes": tr.get("delay_minutes", 0),
            "status": tr.get("status", "ON_TIME"),
            "current_location": tr.get("current_location"),
            "source": tr.get("source")
        })

    # Corridor Windows
    window_data = []
    for w in windows:
        window_data.append({
            "window_code": w.window_code,
            "section_code": w.section.code if w.section else "SEC",
            "start_minute": w.start_minute,
            "end_minute": w.end_minute,
            "window_type": w.window_type
        })

    # Available runs for run switcher
    runs = db.query(OptimizationRun).order_by(OptimizationRun.id.desc()).limit(15).all()
    available_runs = [{
        "run_id": r.id,
        "status": r.status or "OPTIMAL",
        "timestamp": r.run_timestamp.strftime("%d %b %H:%M") if r.run_timestamp else f"Run #{r.id}",
        "scheduled_jobs_count": r.scheduled_jobs_count or 0
    } for r in runs]

    last_updated = None
    for tr in live_data.get("movements", []):
        if tr.get("last_updated"):
            last_updated = tr.get("last_updated")
            break

    return {
        "run_id": run.id if run else None,
        "status": run.status if run else "NO_RUNS",
        "available_runs": available_runs,
        "data_source": live_data.get("source", "Synthetic Demo Data"),
        "is_fallback": live_data.get("is_fallback", True),
        "last_updated": last_updated,
        "timeline_start_minute": 0,
        "timeline_end_minute": 1440,
        "tracks": timeline_tracks,
        "trains": train_paths,
        "windows": window_data
    }


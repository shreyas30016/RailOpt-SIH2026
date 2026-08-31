"""
What-If Simulation Engine - SIH26027 Railway Block Planning
Supports 3 disruption types: TRAIN_DELAY, MAINTENANCE_OVERRUN, BLOCK_UNAVAILABLE
Returns full before/after comparison with affected job/block lists.
"""
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from ..models.models import (
    MaintenanceJob, Section, Department, OptimizationRun,
    TrainSchedule, BlockWindow
)
from .solver import RailwayBlockOptimizer
from ..schemas.schemas import WhatIfRequest, MaintenanceJobCreate


class WhatIfSimulator:
    """
    What-if Simulation Engine for Indian Railways Block Planning.
    Compares a baseline schedule against simulated disruptions.
    """
    def __init__(self, db: Session):
        self.db = db

    def simulate_scenario(self, request: WhatIfRequest) -> Dict[str, Any]:
        optimizer = RailwayBlockOptimizer(self.db)

        # 1. Baseline optimization
        baseline = optimizer.run_optimization()
        baseline_blocks = baseline.get("scheduled_blocks", [])
        baseline_sched_ids = {b.get("job_code") for b in baseline_blocks}

        # 2. Inject disruptions
        injected_jobs: List[int] = []
        modified_trains: List[Dict] = []
        modified_windows: List[Dict] = []

        # 2a. Emergency job injection
        if request.emergency_job:
            dept = self.db.query(Department).filter(
                Department.code == request.emergency_job.department_code
            ).first()
            sec = self.db.query(Section).filter(
                Section.code == request.emergency_job.section_code
            ).first()
            if dept and sec:
                new_job = MaintenanceJob(
                    job_code=request.emergency_job.job_code,
                    title=f"[SIM] {request.emergency_job.title}",
                    department_id=dept.id,
                    section_id=sec.id,
                    duration_minutes=request.emergency_job.duration_minutes,
                    priority=5,
                    urgency="CRITICAL",
                    requires_power_block=request.emergency_job.requires_power_block,
                    requires_traffic_block=request.emergency_job.requires_traffic_block,
                    requires_speed_restriction=request.emergency_job.requires_speed_restriction,
                    status="PENDING",
                    earliest_start_minute=request.emergency_job.earliest_start_minute or 0,
                    latest_end_minute=request.emergency_job.latest_end_minute or 1440,
                    description=request.emergency_job.description or "Simulation injection",
                )
                self.db.add(new_job)
                self.db.commit()
                injected_jobs.append(new_job.id)

        # 2b. Train delay injection - shift departure/arrival for delayed train
        delay_min = getattr(request, "simulated_train_delay_min", 0) or 0
        delayed_train_num = getattr(request, "delayed_train_number", None)
        delayed_train_obj = None
        original_dep = None
        original_arr = None

        if delay_min > 0 and delayed_train_num:
            delayed_train_obj = self.db.query(TrainSchedule).filter(
                TrainSchedule.train_number == delayed_train_num
            ).first()
        elif delay_min > 0:
            # Pick the first express-class train
            delayed_train_obj = self.db.query(TrainSchedule).filter(
                TrainSchedule.priority_weight >= 15
            ).order_by(TrainSchedule.departure_minute).first()

        if delayed_train_obj and delay_min > 0:
            original_dep = delayed_train_obj.departure_minute
            original_arr = delayed_train_obj.arrival_minute
            delayed_train_obj.departure_minute = original_dep + delay_min
            delayed_train_obj.arrival_minute = original_arr + delay_min
            self.db.commit()
            modified_trains.append({
                "train_number": delayed_train_obj.train_number,
                "original_dep": original_dep,
                "original_arr": original_arr,
                "delay_min": delay_min,
            })

        # 2c. Maintenance overrun - extend a specific job
        overrun_min = getattr(request, "block_duration_extra_min", 0) or 0
        overrun_job_obj = None
        original_duration = None
        overrun_job_code = getattr(request, "blocked_section_code", None)  # reuse field for overrun job code
        if overrun_min > 0 and overrun_job_code:
            overrun_job_obj = self.db.query(MaintenanceJob).filter(
                MaintenanceJob.job_code == overrun_job_code
            ).first()
            if not overrun_job_obj:
                # try treating as section: pick first job in that section
                overrun_sec = self.db.query(Section).filter(Section.code == overrun_job_code).first()
                if overrun_sec:
                    overrun_job_obj = self.db.query(MaintenanceJob).filter(
                        MaintenanceJob.section_id == overrun_sec.id
                    ).first()
            if overrun_job_obj:
                original_duration = overrun_job_obj.duration_minutes
                overrun_job_obj.duration_minutes = original_duration + overrun_min
                self.db.commit()

        # 2d. Block section unavailable - shrink its block windows to zero
        unavail_section_code = None
        if not overrun_min and hasattr(request, "blocked_section_code") and request.blocked_section_code:
            unavail_section_code = request.blocked_section_code

        unavail_windows_data: List[Dict] = []
        if unavail_section_code:
            unavail_sec = self.db.query(Section).filter(Section.code == unavail_section_code).first()
            if unavail_sec:
                windows = self.db.query(BlockWindow).filter(BlockWindow.section_id == unavail_sec.id).all()
                for w in windows:
                    unavail_windows_data.append({
                        "id": w.id,
                        "orig_start": w.start_minute,
                        "orig_end": w.end_minute
                    })
                    w.is_active = False
                self.db.commit()
                modified_windows.extend([{
                    "section": unavail_section_code,
                    "action": "DEACTIVATED",
                    "window_count": len(windows)
                }])

        # 3. Run simulated optimization
        simulated = optimizer.run_optimization(max_solver_time_sec=15)
        new_blocks = simulated.get("scheduled_blocks", [])
        new_sched_ids = {b.get("job_code") for b in new_blocks}

        # 4. Cleanup injected disruptions
        for jid in injected_jobs:
            tmp = self.db.query(MaintenanceJob).filter(MaintenanceJob.id == jid).first()
            if tmp:
                self.db.delete(tmp)

        if delayed_train_obj and original_dep is not None:
            delayed_train_obj.departure_minute = original_dep
            delayed_train_obj.arrival_minute = original_arr

        if overrun_job_obj and original_duration is not None:
            overrun_job_obj.duration_minutes = original_duration

        if unavail_windows_data:
            for w_data in unavail_windows_data:
                w_obj = self.db.query(BlockWindow).filter(BlockWindow.id == w_data["id"]).first()
                if w_obj:
                    w_obj.is_active = True

        self.db.commit()

        # 5. Compute deltas and affected job lists
        dropped_jobs = list(baseline_sched_ids - new_sched_ids)
        gained_jobs = list(new_sched_ids - baseline_sched_ids)
        affected_jobs = list(set(dropped_jobs) | set(gained_jobs))

        delta_scheduled = simulated["scheduled_jobs_count"] - baseline["scheduled_jobs_count"]
        delta_train_delay = simulated["train_delay_total_min"] - baseline["train_delay_total_min"]
        delta_utilization = round(simulated["block_utilization_pct"] - baseline["block_utilization_pct"], 1)
        delta_deferred = simulated["unscheduled_jobs_count"] - baseline["unscheduled_jobs_count"]

        critical_alerts: List[str] = []
        if request.emergency_job:
            critical_alerts.append(
                f"Emergency job '{request.emergency_job.job_code}' injected into corridor schedule."
            )
        if delay_min > 0 and delayed_train_obj:
            critical_alerts.append(
                f"Train #{delayed_train_obj.train_number} delayed +{delay_min} min. "
                f"Maintenance window adjusted to maintain headway compliance."
            )
        if unavail_section_code:
            critical_alerts.append(
                f"Section {unavail_section_code} marked unavailable. "
                f"{len(unavail_windows_data)} block window(s) deactivated."
            )
        if overrun_min > 0 and overrun_job_obj:
            critical_alerts.append(
                f"Job {overrun_job_obj.job_code} overrun +{overrun_min} min. "
                f"Re-optimized around extended duration."
            )
        if delta_train_delay > 0:
            critical_alerts.append(
                f"Net train regulation increased by {delta_train_delay} min across corridor."
            )
        if delta_scheduled < 0:
            critical_alerts.append(
                f"{abs(delta_scheduled)} job(s) deferred to accommodate disruption."
            )

        impact_summary = (
            f"Scenario '{request.scenario_name}': "
            f"baseline={baseline['scheduled_jobs_count']} scheduled, "
            f"new={simulated['scheduled_jobs_count']} scheduled. "
            f"Delta train delay: {delta_train_delay:+d} min. "
            f"Utilization shift: {delta_utilization:+.1f}%."
        )

        return {
            "scenario_name": request.scenario_name,
            "baseline_run_id": baseline["run_id"],
            "simulated_run": simulated,
            "baseline_blocks": baseline_blocks,
            "new_blocks": new_blocks,
            "affected_jobs": affected_jobs,
            "dropped_jobs": dropped_jobs,
            "gained_jobs": gained_jobs,
            "delta_scheduled_jobs": delta_scheduled,
            "delta_train_delay_min": delta_train_delay,
            "delta_utilization_pct": delta_utilization,
            "delta_deferred_jobs": delta_deferred,
            "kpi_delta": {
                "scheduled": delta_scheduled,
                "train_delay_min": delta_train_delay,
                "utilization_pct": delta_utilization,
                "deferred": delta_deferred,
            },
            "critical_alerts": critical_alerts,
            "impact_summary": impact_summary,
            "disruptions_applied": {
                "emergency_job": request.emergency_job.job_code if request.emergency_job else None,
                "train_delay_min": delay_min if delay_min > 0 else None,
                "block_unavailable_section": unavail_section_code,
                "maintenance_overrun_min": overrun_min if overrun_min > 0 else None,
            }
        }

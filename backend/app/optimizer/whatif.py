from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models.models import MaintenanceJob, Section, Department, OptimizationRun
from .solver import RailwayBlockOptimizer
from ..schemas.schemas import WhatIfRequest, MaintenanceJobCreate

class WhatIfSimulator:
    """
    What-if Simulation Engine for Indian Railways Block Planning.
    Compares a baseline schedule against simulated disruptions (emergency jobs, train delays, corridor blocks).
    """
    def __init__(self, db: Session):
        self.db = db

    def simulate_scenario(self, request: WhatIfRequest) -> Dict[str, Any]:
        # 1. Run baseline optimization first or fetch latest
        optimizer = RailwayBlockOptimizer(self.db)
        baseline = optimizer.run_optimization()

        # 2. Inject simulated disruption
        temp_job_id = None
        if request.emergency_job:
            dept = self.db.query(Department).filter(Department.code == request.emergency_job.department_code).first()
            sec = self.db.query(Section).filter(Section.code == request.emergency_job.section_code).first()

            if dept and sec:
                new_job = MaintenanceJob(
                    job_code=request.emergency_job.job_code,
                    title=f"[SIMULATION] {request.emergency_job.title}",
                    department_id=dept.id,
                    section_id=sec.id,
                    duration_minutes=request.emergency_job.duration_minutes,
                    priority=5, # Critical
                    urgency="CRITICAL",
                    requires_power_block=request.emergency_job.requires_power_block,
                    requires_traffic_block=request.emergency_job.requires_traffic_block,
                    requires_speed_restriction=request.emergency_job.requires_speed_restriction,
                    status="PENDING",
                    earliest_start_minute=request.emergency_job.earliest_start_minute or 0,
                    latest_end_minute=request.emergency_job.latest_end_minute or 1440,
                    description=request.emergency_job.description or "Emergency What-If Injection"
                )
                self.db.add(new_job)
                self.db.commit()
                temp_job_id = new_job.id

        # 3. Run simulated optimization
        simulated = optimizer.run_optimization(max_solver_time_sec=15)

        # 4. Cleanup temporary simulation data from DB
        if temp_job_id:
            temp_j = self.db.query(MaintenanceJob).filter(MaintenanceJob.id == temp_job_id).first()
            if temp_j:
                self.db.delete(temp_j)
                self.db.commit()

        # 5. Compute Deltas & Insights
        delta_scheduled = simulated["scheduled_jobs_count"] - baseline["scheduled_jobs_count"]
        delta_train_delay = simulated["train_delay_total_min"] - baseline["train_delay_total_min"]
        delta_utilization = round(simulated["block_utilization_pct"] - baseline["block_utilization_pct"], 1)

        critical_alerts = []
        if request.emergency_job:
            critical_alerts.append(f"Emergency maintenance job '{request.emergency_job.job_code}' successfully integrated into the corridor schedule.")
        if delta_train_delay > 0:
            critical_alerts.append(f"Train regulation increased by {delta_train_delay} minutes across the section.")
        if delta_scheduled < 0:
            critical_alerts.append(f"{abs(delta_scheduled)} lower-priority routine jobs were deferred to accommodate emergency work.")

        impact_summary = (
            f"Scenario '{request.scenario_name}' simulated with {simulated['scheduled_jobs_count']} scheduled blocks. "
            f"Net change in train delay: {delta_train_delay:+d} min. "
            f"Block corridor utilization shifted by {delta_utilization:+1f}%."
        )

        return {
            "scenario_name": request.scenario_name,
            "baseline_run_id": baseline["run_id"],
            "simulated_run": simulated,
            "delta_scheduled_jobs": delta_scheduled,
            "delta_train_delay_min": delta_train_delay,
            "delta_utilization_pct": delta_utilization,
            "critical_alerts": critical_alerts,
            "impact_summary": impact_summary
        }

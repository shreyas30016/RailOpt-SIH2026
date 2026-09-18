"""
RailOpt AI — Tool Registry
============================

Defines the 9 RailOpt tools that the AI orchestrator may invoke.
Each tool maps to an EXISTING RailOpt backend API — no duplicate logic.

Tool contract:
  - name: unique string identifier
  - description: human-readable purpose
  - required_permission: permission key checked against the authenticated user
  - input_schema: dict of expected parameter names and types
  - execute(args, db): calls the existing backend service and returns structured result

IMPORTANT:
  - Tools NEVER directly mutate the database.
  - All mutations go through existing authenticated backend endpoints.
  - Permission checks here are a PRE-FILTER only.
    The existing backend endpoints enforce RBAC independently.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from sqlalchemy.orm import Session

from .schemas import ToolCallResult


# ---------------------------------------------------------------------------
# Tool descriptor
# ---------------------------------------------------------------------------

@dataclass
class ToolSpec:
    name: str
    description: str
    required_permission: Optional[str]  # None = any authenticated user
    input_schema: Dict[str, Any]
    output_description: str
    _execute_fn: Callable[..., ToolCallResult] = field(repr=False, compare=False)

    def execute(self, args: Dict[str, Any], db: Session) -> ToolCallResult:
        return self._execute_fn(args, db)


# ---------------------------------------------------------------------------
# Individual tool executor functions (delegate to existing services)
# ---------------------------------------------------------------------------

def _exec_get_dashboard_summary(args: Dict[str, Any], db: Session) -> ToolCallResult:
    """Delegate to existing dashboard service logic."""
    try:
        from ..models.models import MaintenanceJob, OptimizationRun, BlockWindow
        total_jobs = db.query(MaintenanceJob).count()
        pending = db.query(MaintenanceJob).filter(MaintenanceJob.status == "PENDING").count()
        critical = db.query(MaintenanceJob).filter(
            MaintenanceJob.urgency.in_(["CRITICAL", "HIGH"])
        ).count()
        latest_run = db.query(OptimizationRun).order_by(OptimizationRun.id.desc()).first()
        return ToolCallResult(
            tool_name="get_dashboard_summary",
            success=True,
            data={
                "total_jobs": total_jobs,
                "pending_jobs": pending,
                "critical_high_jobs": critical,
                "latest_run_id": latest_run.id if latest_run else None,
                "latest_run_status": latest_run.status if latest_run else "NO_RUN",
                "latest_scheduled_count": latest_run.scheduled_jobs_count if latest_run else 0,
            }
        )
    except Exception as e:
        return ToolCallResult(tool_name="get_dashboard_summary", success=False, error=str(e))


def _exec_get_maintenance_requests(args: Dict[str, Any], db: Session) -> ToolCallResult:
    try:
        from ..models.models import MaintenanceJob
        query = db.query(MaintenanceJob)
        if args.get("status"):
            query = query.filter(MaintenanceJob.status == args["status"])
        if args.get("department_code"):
            from ..models.models import Department
            dept = db.query(Department).filter(Department.code == args["department_code"]).first()
            if dept:
                query = query.filter(MaintenanceJob.department_id == dept.id)
        jobs = query.order_by(MaintenanceJob.priority.desc()).limit(20).all()
        return ToolCallResult(
            tool_name="get_maintenance_requests",
            success=True,
            data={
                "count": len(jobs),
                "jobs": [
                    {
                        "id": j.id,
                        "job_code": j.job_code,
                        "title": j.title,
                        "status": j.status,
                        "urgency": j.urgency,
                        "priority": j.priority,
                    }
                    for j in jobs
                ]
            }
        )
    except Exception as e:
        return ToolCallResult(tool_name="get_maintenance_requests", success=False, error=str(e))


def _exec_get_maintenance_request(args: Dict[str, Any], db: Session) -> ToolCallResult:
    try:
        from ..models.models import MaintenanceJob
        job_code = args.get("job_code", "")
        job = db.query(MaintenanceJob).filter(MaintenanceJob.job_code == job_code).first()
        if not job:
            return ToolCallResult(
                tool_name="get_maintenance_request", success=True,
                data_unavailable=True,
                data={"job_code": job_code, "found": False}
            )
        return ToolCallResult(
            tool_name="get_maintenance_request",
            success=True,
            data={
                "id": job.id, "job_code": job.job_code, "title": job.title,
                "status": job.status, "urgency": job.urgency,
                "priority": job.priority, "duration_minutes": job.duration_minutes,
                "description": job.description,
            }
        )
    except Exception as e:
        return ToolCallResult(tool_name="get_maintenance_request", success=False, error=str(e))


def _exec_get_unscheduled_jobs(args: Dict[str, Any], db: Session) -> ToolCallResult:
    return _exec_get_maintenance_requests({"status": "PENDING", **args}, db)


def _exec_run_optimization(args: Dict[str, Any], db: Session) -> ToolCallResult:
    """Delegate to existing RailwayBlockOptimizer."""
    try:
        from ..optimizer.solver import RailwayBlockOptimizer
        optimizer = RailwayBlockOptimizer(db)
        result = optimizer.run_optimization(
            max_solver_time_sec=int(args.get("max_solver_time_sec", 15)),
            minimize_passenger_delays=bool(args.get("minimize_passenger_delays", True)),
            train_delay_weight=float(args.get("train_delay_weight", 1.0)),
            maximize_shadow_blocks=bool(args.get("maximize_shadow_blocks", True)),
            shadow_block_weight=float(args.get("shadow_block_weight", 1.0)),
            prioritize_urgent_maintenance=bool(args.get("prioritize_urgent_maintenance", True)),
            urgency_weight=float(args.get("urgency_weight", 1.0)),
        )
        return ToolCallResult(
            tool_name="run_optimization",
            success=True,
            data={
                "run_id": result.get("run_id"),
                "status": result.get("status"),
                "scheduled_jobs_count": result.get("scheduled_jobs_count"),
                "unscheduled_jobs_count": result.get("unscheduled_jobs_count"),
                "solver_time_seconds": result.get("solver_time_seconds"),
            }
        )
    except Exception as e:
        return ToolCallResult(tool_name="run_optimization", success=False, error=str(e))


def _exec_run_what_if(args: Dict[str, Any], db: Session) -> ToolCallResult:
    try:
        from ..optimizer.whatif import WhatIfSimulator
        from ..schemas.schemas import WhatIfRequest
        req = WhatIfRequest(
            scenario_name=args.get("scenario_name", "TRAIN_DELAY"),
            simulated_train_delay_min=int(args.get("delay_minutes", 30)),
        )
        simulator = WhatIfSimulator(db)
        result = simulator.simulate_scenario(req)
        return ToolCallResult(tool_name="run_what_if", success=True, data=result)
    except Exception as e:
        return ToolCallResult(tool_name="run_what_if", success=False, error=str(e))


def _exec_get_gantt_timeline(args: Dict[str, Any], db: Session) -> ToolCallResult:
    try:
        from ..models.models import OptimizationRun, ScheduledBlock
        run_id = args.get("run_id")
        if run_id:
            run = db.query(OptimizationRun).filter(OptimizationRun.id == run_id).first()
        else:
            run = db.query(OptimizationRun).order_by(OptimizationRun.id.desc()).first()
        if not run:
            return ToolCallResult(
                tool_name="get_gantt_timeline", success=True, data_unavailable=True,
                data={"message": "No optimization run found. Run the block planner first."}
            )
        blocks = db.query(ScheduledBlock).filter(ScheduledBlock.run_id == run.id).count()
        return ToolCallResult(
            tool_name="get_gantt_timeline",
            success=True,
            data={
                "run_id": run.id,
                "status": run.status,
                "scheduled_blocks_count": blocks,
                "gantt_url": "/block-planning",
            }
        )
    except Exception as e:
        return ToolCallResult(tool_name="get_gantt_timeline", success=False, error=str(e))


def _exec_get_job_explanation(args: Dict[str, Any], db: Session) -> ToolCallResult:
    try:
        from ..optimizer.explainer import DecisionExplainer
        job_code = args.get("job_code", "")
        explainer = DecisionExplainer(db)
        result = explainer.explain_job_decision(job_code)
        if "error" in result:
            return ToolCallResult(
                tool_name="get_job_explanation", success=True, data_unavailable=True,
                data={"job_code": job_code, "message": result["error"]}
            )
        return ToolCallResult(tool_name="get_job_explanation", success=True, data=result)
    except Exception as e:
        return ToolCallResult(tool_name="get_job_explanation", success=False, error=str(e))


def _exec_get_reports_analytics(args: Dict[str, Any], db: Session) -> ToolCallResult:
    try:
        from ..models.models import OptimizationRun, MaintenanceJob, ScheduledBlock
        runs = db.query(OptimizationRun).order_by(OptimizationRun.id.desc()).limit(5).all()
        total_jobs = db.query(MaintenanceJob).count()
        scheduled = db.query(ScheduledBlock).count()
        return ToolCallResult(
            tool_name="get_reports_analytics",
            success=True,
            data={
                "total_runs": len(runs),
                "total_maintenance_jobs": total_jobs,
                "total_scheduled_blocks": scheduled,
                "grant_ratio_pct": round(scheduled / max(1, total_jobs) * 100, 1),
                "reports_url": "/reports",
            }
        )
    except Exception as e:
        return ToolCallResult(tool_name="get_reports_analytics", success=False, error=str(e))


def _exec_get_train_status(args: Dict[str, Any], db: Session) -> ToolCallResult:
    """
    Answer train status / live-position questions from the ACTUAL corridor feed.

    Delegates to the same train_adapter used by /api/trains/live and /api/trains/status.
    NEVER fabricates a position: unknown trains return an honest not-found payload
    with the real data source label.
    """
    try:
        from ..services.train_adapter import train_adapter
        from ..models.models import TrainSchedule

        train_number = str(args.get("train_number", "")).strip()
        if not train_number:
            return ToolCallResult(
                tool_name="get_train_status", success=True,
                data={"error": "No train number provided.", "source": "railopt_backend"},
            )

        feed = train_adapter.get_movements()
        source = feed.get("source", "Synthetic Demo Data")
        movements = feed.get("movements", [])
        matched = next(
            (m for m in movements if str(m.get("train_id")) == train_number),
            None,
        )

        timetable = db.query(TrainSchedule).filter(
            TrainSchedule.train_number == train_number
        ).first()

        if matched:
            return ToolCallResult(
                tool_name="get_train_status",
                success=True,
                data={
                    "found_in_feed": True,
                    "train_number": train_number,
                    "train_name": matched.get("train_name"),
                    "status": matched.get("status"),
                    "delay_minutes": matched.get("delay_minutes"),
                    "current_location": matched.get("current_location"),
                    "next_location": matched.get("next_location"),
                    "direction": matched.get("direction"),
                    "source": source,
                },
            )

        if timetable:
            return ToolCallResult(
                tool_name="get_train_status",
                success=True,
                data={
                    "found_in_feed": False,
                    "in_timetable": True,
                    "train_number": timetable.train_number,
                    "train_name": timetable.train_name,
                    "train_type": timetable.train_type,
                    "origin_station": timetable.origin_station,
                    "destination_station": timetable.destination_station,
                    "source": source,
                    "note": "Train exists in the corridor timetable but has no live movement entry in the current feed.",
                },
            )

        return ToolCallResult(
            tool_name="get_train_status",
            success=True,
            data={
                "found_in_feed": False,
                "in_timetable": False,
                "train_number": train_number,
                "source": source,
                "note": f"Train {train_number} is not present in the {source} corridor feed. RailOpt does not claim live GPS tracking of trains outside this dataset.",
            },
        )
    except Exception as e:
        return ToolCallResult(tool_name="get_train_status", success=False, error=str(e))


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------

class RailOptToolRegistry:
    """
    Registry of all RailOpt AI tools.
    Each tool maps 1-to-1 to an existing backend capability.
    No tool implements its own business logic.
    """

    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}
        self._register_all()

    def _register_all(self) -> None:
        specs = [
            ToolSpec(
                name="get_dashboard_summary",
                description="Get the current operational dashboard summary: total jobs, pending count, critical jobs, latest optimization run status.",
                required_permission=None,  # any authenticated user
                input_schema={},
                output_description="Dashboard KPIs including job counts and latest run status.",
                _execute_fn=_exec_get_dashboard_summary,
            ),
            ToolSpec(
                name="get_maintenance_requests",
                description="List maintenance requests, optionally filtered by status (PENDING, APPROVED, SCHEDULED, DEFERRED) or department code (ENG, TRD, S_T).",
                required_permission=None,
                input_schema={
                    "status": {"type": "string", "enum": ["PENDING", "APPROVED", "SCHEDULED", "DEFERRED"], "optional": True},
                    "department_code": {"type": "string", "enum": ["ENG", "TRD", "S_T"], "optional": True},
                },
                output_description="List of maintenance job summaries.",
                _execute_fn=_exec_get_maintenance_requests,
            ),
            ToolSpec(
                name="get_maintenance_request",
                description="Get full details of a single maintenance request by job_code (e.g. JOB-ENG-101).",
                required_permission=None,
                input_schema={"job_code": {"type": "string"}},
                output_description="Detailed maintenance job record.",
                _execute_fn=_exec_get_maintenance_request,
            ),
            ToolSpec(
                name="get_unscheduled_jobs",
                description="Get all maintenance jobs currently in PENDING status — not yet approved or scheduled.",
                required_permission=None,
                input_schema={"department_code": {"type": "string", "optional": True}},
                output_description="List of pending/unscheduled maintenance jobs.",
                _execute_fn=_exec_get_unscheduled_jobs,
            ),
            ToolSpec(
                name="run_optimization",
                description="Run the OR-Tools CP-SAT block planning optimization. Requires can_optimize permission (Controller or Planner only).",
                required_permission="can_optimize",
                input_schema={
                    "max_solver_time_sec": {"type": "integer", "default": 15, "min": 5, "max": 60},
                    "minimize_passenger_delays": {"type": "boolean", "default": True},
                    "train_delay_weight": {"type": "number", "default": 1.0, "min": 0.1, "max": 5.0},
                    "maximize_shadow_blocks": {"type": "boolean", "default": True},
                    "shadow_block_weight": {"type": "number", "default": 1.0, "min": 0.1, "max": 5.0},
                    "prioritize_urgent_maintenance": {"type": "boolean", "default": True},
                    "urgency_weight": {"type": "number", "default": 1.0, "min": 0.1, "max": 5.0},
                },
                output_description="Optimization run result with run_id, status, scheduled count.",
                _execute_fn=_exec_run_optimization,
            ),
            ToolSpec(
                name="run_what_if",
                description="Simulate a disruption scenario (train delay, maintenance overrun, etc.). Requires can_optimize permission.",
                required_permission="can_optimize",
                input_schema={
                    "scenario_name": {"type": "string", "enum": ["TRAIN_DELAY", "MAINTENANCE_OVERRUN", "BLOCK_UNAVAILABLE", "EMERGENCY_JOB"]},
                    "delay_minutes": {"type": "integer", "default": 30, "optional": True},
                },
                output_description="Before/after comparison of the simulated scenario.",
                _execute_fn=_exec_run_what_if,
            ),
            ToolSpec(
                name="get_gantt_timeline",
                description="Get Gantt chart timeline data for the latest (or specific) optimization run.",
                required_permission=None,
                input_schema={"run_id": {"type": "integer", "optional": True}},
                output_description="Gantt timeline metadata and scheduled block count.",
                _execute_fn=_exec_get_gantt_timeline,
            ),
            ToolSpec(
                name="get_job_explanation",
                description="Get the decision explanation tree for why a specific job was scheduled or deferred. Use job_code (e.g. JOB-ENG-101).",
                required_permission=None,
                input_schema={"job_code": {"type": "string"}},
                output_description="Structured decision explanation tree from the DecisionExplainer.",
                _execute_fn=_exec_get_job_explanation,
            ),
            ToolSpec(
                name="get_reports_analytics",
                description="Get reports and analytics summary: run counts, scheduling ratios, departmental performance.",
                required_permission=None,
                input_schema={},
                output_description="Analytics summary with block grant ratio and run statistics.",
                _execute_fn=_exec_get_reports_analytics,
            ),
            ToolSpec(
                name="get_train_status",
                description="Get the current status / live position of a train number (e.g. 12050) from the corridor feed. Unknown trains return an honest not-found answer — never a fabricated position.",
                required_permission=None,
                input_schema={"train_number": {"type": "string"}},
                output_description="Train movement entry from the active corridor feed, or an honest not-found payload with the real data source.",
                _execute_fn=_exec_get_train_status,
            ),
        ]
        for spec in specs:
            self._tools[spec.name] = spec

    def get(self, tool_name: str) -> Optional[ToolSpec]:
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_all_specs(self) -> List[ToolSpec]:
        return list(self._tools.values())

    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def __len__(self) -> int:
        return len(self._tools)

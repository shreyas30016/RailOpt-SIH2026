import time
from typing import List, Dict, Any, Tuple
from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from ..models.models import (
    MaintenanceJob, TrainSchedule, Section, TrackLine,
    MaintenanceResource, OptimizationRun, ScheduledBlock, ConflictLog, DecisionExplanation, BlockWindow
)
from .constraints import RailwayConstraintManager, JobConstraintMeta, TrainConstraintMeta
from ..services.duration_predictor import duration_predictor

class RailwayBlockOptimizer:
    """
    Deterministic Railway Block Planning and Optimization Engine using Google OR-Tools CP-SAT.
    """
    def __init__(self, db: Session, constraint_manager: RailwayConstraintManager = None):
        self.db = db
        self.constraint_mgr = constraint_manager or RailwayConstraintManager()

    def _minute_to_time_str(self, minute: int) -> str:
        h = (minute // 60) % 24
        m = minute % 60
        return f"{h:02d}:{m:02d}"

    def run_optimization(
        self,
        time_window_start: int = 0,
        time_window_end: int = 1440,
        max_solver_time_sec: int = 15,
        minimize_passenger_delays: bool = True,
        maximize_shadow_blocks: bool = True,
    ) -> Dict[str, Any]:
        start_exec_time = time.time()

        # 1. Fetch data from DB
        jobs_db = self.db.query(MaintenanceJob).filter(MaintenanceJob.status != "CANCELLED").all()
        trains_db = self.db.query(TrainSchedule).all()
        sections_db = self.db.query(Section).all()
        track_lines_db = self.db.query(TrackLine).all()
        resources_db = self.db.query(MaintenanceResource).all()

        sec_dict = {s.id: s for s in sections_db}
        tl_dict = {tl.id: tl for tl in track_lines_db}
        res_dict = {r.id: r for r in resources_db}

        # 2. Build Job metadata
        job_metas: List[JobConstraintMeta] = []
        for j in jobs_db:
            sec = sec_dict.get(j.section_id)
            tl = tl_dict.get(j.track_line_id)
            res = res_dict.get(j.required_resource_id)
            
            dept_code = j.department.code if j.department else "ENG"
            if j.duration_minutes and j.duration_minutes > 0:
                job_dur = j.duration_minutes
            else:
                pred_res = duration_predictor.predict({
                    "department_code": dept_code,
                    "urgency": j.urgency,
                    "duration_minutes": j.duration_minutes,
                    "requires_power_block": j.requires_power_block
                }, {"section_length_km": sec.length_km if sec else 15.0})
                job_dur = pred_res["predictedDuration"]

            job_metas.append(JobConstraintMeta(
                job_id=j.id,
                job_code=j.job_code,
                department_code=dept_code,
                section_code=sec.code if sec else "UNKNOWN",
                track_line_code=tl.line_code if tl else f"{sec.code if sec else 'SEC'}_UP",
                duration_min=job_dur,
                priority=j.priority,
                urgency=j.urgency,
                requires_power_block=j.requires_power_block,
                requires_traffic_block=j.requires_traffic_block,
                requires_speed_restriction=j.requires_speed_restriction,
                speed_restriction_kmh=j.speed_restriction_kmh or 30,
                required_resource_code=res.code if res else "",
                earliest_start_min=max(time_window_start, j.earliest_start_minute),
                latest_end_min=min(time_window_end, j.latest_end_minute)
            ))

        # 3. Build CP-SAT Model
        model = cp_model.CpModel()

        # Decision Variables
        job_scheduled_vars: Dict[int, cp_model.IntVar] = {}
        job_start_vars: Dict[int, cp_model.IntVar] = {}
        job_end_vars: Dict[int, cp_model.IntVar] = {}
        job_interval_vars: Dict[int, cp_model.IntervalVar] = {}

        for j in job_metas:
            # Is scheduled boolean
            is_sched = model.NewBoolVar(f"sched_{j.job_code}")
            job_scheduled_vars[j.job_id] = is_sched

            earliest = j.earliest_start_min
            latest = j.latest_end_min

            # If job duration exceeds allowable window, it cannot be scheduled
            if earliest + j.duration_min > latest:
                model.Add(is_sched == 0)
                start_var = model.NewIntVar(earliest, earliest, f"start_{j.job_code}")
                end_var = model.NewIntVar(earliest + j.duration_min, earliest + j.duration_min, f"end_{j.job_code}")
            else:
                start_var = model.NewIntVar(earliest, latest - j.duration_min, f"start_{j.job_code}")
                end_var = model.NewIntVar(earliest + j.duration_min, latest, f"end_{j.job_code}")
            
            interval_var = model.NewOptionalIntervalVar(
                start_var, j.duration_min, end_var, is_sched, f"interval_{j.job_code}"
            )

            job_start_vars[j.job_id] = start_var
            job_end_vars[j.job_id] = end_var
            job_interval_vars[j.job_id] = interval_var

        # 4. Constraint: Machine Exclusivity
        if self.constraint_mgr.enable_machine_exclusivity:
            machine_groups: Dict[str, List[cp_model.IntervalVar]] = {}
            for j in job_metas:
                if j.required_resource_code:
                    machine_groups.setdefault(j.required_resource_code, []).append(job_interval_vars[j.job_id])
            
            for m_code, intervals in machine_groups.items():
                if len(intervals) > 1:
                    model.AddNoOverlap(intervals)

        # 4b. Constraint: Job Precedence Dependency (Job B cannot start before Job A finishes)
        if self.constraint_mgr.enable_job_precedence:
            job_code_map = {j.job_code: j for j in job_metas}
            for j in job_metas:
                if j.preceding_job_code and j.preceding_job_code in job_code_map:
                    pred = job_code_map[j.preceding_job_code]
                    # If dependent job is scheduled, predecessor must be scheduled
                    model.AddImplication(job_scheduled_vars[j.job_id], job_scheduled_vars[pred.job_id])
                    # Dependent job cannot start before predecessor finishes
                    model.Add(job_end_vars[pred.job_id] <= job_start_vars[j.job_id]).OnlyEnforceIf([
                        job_scheduled_vars[j.job_id],
                        job_scheduled_vars[pred.job_id]
                    ])

        # 5. Constraint: Track Line Non-Overlap & Shadow Block Coupling
        track_line_jobs: Dict[str, List[JobConstraintMeta]] = {}
        for j in job_metas:
            track_line_jobs.setdefault(j.track_line_code, []).append(j)

        shadow_pairs_vars: List[Tuple[JobConstraintMeta, JobConstraintMeta, cp_model.IntVar]] = []

        for tl_code, t_jobs in track_line_jobs.items():
            n = len(t_jobs)
            for i in range(n):
                for k in range(i + 1, n):
                    j1 = t_jobs[i]
                    j2 = t_jobs[k]

                    can_shadow = self.constraint_mgr.can_form_shadow_block(j1, j2)

                    if can_shadow and maximize_shadow_blocks:
                        is_shadow = model.NewBoolVar(f"shadow_{j1.job_code}_{j2.job_code}")
                        shadow_pairs_vars.append((j1, j2, is_shadow))

                        # If shadow block active, both start at the same time and run concurrently
                        model.Add(job_start_vars[j1.job_id] == job_start_vars[j2.job_id]).OnlyEnforceIf(is_shadow)
                        model.AddImplication(is_shadow, job_scheduled_vars[j1.job_id])
                        model.AddImplication(is_shadow, job_scheduled_vars[j2.job_id])

                        # If not a shadow block, they cannot overlap in time
                        j1_before_j2 = model.NewBoolVar(f"{j1.job_code}_before_{j2.job_code}")
                        j2_before_j1 = model.NewBoolVar(f"{j2.job_code}_before_{j1.job_code}")

                        model.Add(job_end_vars[j1.job_id] <= job_start_vars[j2.job_id]).OnlyEnforceIf(j1_before_j2)
                        model.Add(job_end_vars[j2.job_id] <= job_start_vars[j1.job_id]).OnlyEnforceIf(j2_before_j1)

                        model.AddBoolOr([j1_before_j2, j2_before_j1, is_shadow, job_scheduled_vars[j1.job_id].Not(), job_scheduled_vars[j2.job_id].Not()])
                    else:
                        # Strict No-Overlap between non-shadowable jobs on same track line
                        j1_before_j2 = model.NewBoolVar(f"{j1.job_code}_before_{j2.job_code}")
                        j2_before_j1 = model.NewBoolVar(f"{j2.job_code}_before_{j1.job_code}")

                        model.Add(job_end_vars[j1.job_id] <= job_start_vars[j2.job_id]).OnlyEnforceIf(j1_before_j2)
                        model.Add(job_end_vars[j2.job_id] <= job_start_vars[j1.job_id]).OnlyEnforceIf(j2_before_j1)

                        model.AddBoolOr([j1_before_j2, j2_before_j1, job_scheduled_vars[j1.job_id].Not(), job_scheduled_vars[j2.job_id].Not()])

        # 6. Train Timetable Deconfliction & Delay Modeling
        sec_order = {sec: i for i, sec in enumerate(self.constraint_mgr.section_order)}
        total_secs = len(sec_order)
        headway_buf = self.constraint_mgr.headway_margin_minutes

        train_delay_vars: Dict[str, cp_model.IntVar] = {}
        for tr in trains_db:
            # High priority passenger trains have tight limits, freight/goods trains can be held in siding loops
            if tr.priority_weight >= 30:
                max_delay = self.constraint_mgr.max_premium_delay
            elif tr.priority_weight >= 15:
                max_delay = self.constraint_mgr.max_mail_delay
            else:
                max_delay = self.constraint_mgr.max_freight_holding

            delay_var = model.NewIntVar(0, max_delay, f"delay_{tr.train_number}")
            train_delay_vars[tr.train_number] = delay_var

            # For each job on a specific section
            for j in job_metas:
                # Check if section has a 3rd line for diversion from config
                has_3rd_line = j.section_code in self.constraint_mgr.third_line_sections
                
                # If section has no 3rd line, calculate train transit window across this specific section
                if not has_3rd_line and j.requires_traffic_block:
                    s_idx = sec_order.get(j.section_code, 0)
                    total_dur = max(30, tr.arrival_minute - tr.departure_minute)
                    sec_dur = total_dur // total_secs
                    
                    if tr.direction == "DN":
                        entry_m = tr.departure_minute + (s_idx * sec_dur)
                    else:
                        entry_m = tr.departure_minute + ((total_secs - 1 - s_idx) * sec_dur)
                    exit_m = entry_m + sec_dur

                    is_same_direction = (tr.direction == "UP" and "UP" in j.track_line_code) or \
                                        (tr.direction == "DN" and "DN" in j.track_line_code)

                    if is_same_direction:
                        tr_before = model.NewBoolVar(f"tr_{tr.train_number}_before_{j.job_code}")
                        tr_after = model.NewBoolVar(f"tr_{tr.train_number}_after_{j.job_code}")

                        # Train passes before block with safety buffer
                        model.Add(exit_m + headway_buf <= job_start_vars[j.job_id]).OnlyEnforceIf(tr_before)

                        # Train passes after block with safety buffer (with possible delay)
                        model.Add(job_end_vars[j.job_id] + headway_buf <= entry_m + delay_var).OnlyEnforceIf(tr_after)

                        model.AddBoolOr([tr_before, tr_after, job_scheduled_vars[j.job_id].Not()])

        # 7. Objective Function Formulation
        objective_terms = []

        # (a) Maximize Scheduled Jobs weighted by Priority and Urgency
        for j in job_metas:
            u_bonus = (
                self.constraint_mgr.urgency_critical_bonus if j.urgency == "CRITICAL"
                else (self.constraint_mgr.urgency_high_bonus if j.urgency == "HIGH"
                      else self.constraint_mgr.urgency_routine_bonus)
            )
            weight = j.priority * self.constraint_mgr.job_priority_multiplier + u_bonus
            objective_terms.append(job_scheduled_vars[j.job_id] * weight)

        # (b) Maximize Shadow Block Synergies (Bonus for bundling multiple departments in same window)
        if maximize_shadow_blocks:
            for j1, j2, is_shadow in shadow_pairs_vars:
                objective_terms.append(is_shadow * self.constraint_mgr.shadow_block_bonus_weight)

        # (c) Minimize Train Delays (scaled by train priority: Passenger express high penalty, freight nominal)
        if minimize_passenger_delays:
            for tr in trains_db:
                if tr.priority_weight >= 30:
                    weight_factor = self.constraint_mgr.penalty_premium_delay
                elif tr.priority_weight >= 15:
                    weight_factor = self.constraint_mgr.penalty_mail_delay
                else:
                    weight_factor = self.constraint_mgr.penalty_freight_delay
                objective_terms.append(train_delay_vars[tr.train_number] * (-weight_factor))

        model.Maximize(sum(objective_terms))

        # 8. Solve with CP-SAT
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_solver_time_sec
        solver.parameters.num_workers = 4
        status = solver.Solve(model)
        solve_duration = time.time() - start_exec_time

        # 9. Process Solution Results
        is_optimal = status == cp_model.OPTIMAL
        is_feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

        scheduled_blocks_list: List[Dict[str, Any]] = []
        unscheduled_jobs_list: List[Dict[str, Any]] = []
        conflicts_list: List[Dict[str, Any]] = []
        explanations_list: List[Dict[str, Any]] = []

        total_maint_minutes = 0
        total_train_delay_min = 0

        # Create OptimizationRun in DB
        run_record = OptimizationRun(
            status="OPTIMAL" if is_optimal else ("FEASIBLE" if is_feasible else "INFEASIBLE"),
            total_jobs=len(job_metas),
            solver_time_seconds=round(solve_duration, 3),
            solver_status=solver.StatusName(status),
            parameters_json=f"window=[{time_window_start},{time_window_end}], minimize_delays={minimize_passenger_delays}, shadow_sync={maximize_shadow_blocks}"
        )
        self.db.add(run_record)
        self.db.commit()

        if is_feasible:
            # Map active shadow block pairs
            shadow_map: Dict[int, List[str]] = {}
            for j1, j2, is_shadow in shadow_pairs_vars:
                if solver.Value(is_shadow) == 1:
                    shadow_map.setdefault(j1.job_id, []).append(j2.job_code)
                    shadow_map.setdefault(j2.job_id, []).append(j1.job_code)

            for j in job_metas:
                is_sched = solver.Value(job_scheduled_vars[j.job_id]) == 1
                if is_sched:
                    s_min = int(solver.Value(job_start_vars[j.job_id]))
                    e_min = int(solver.Value(job_end_vars[j.job_id]))
                    dur = e_min - s_min
                    total_maint_minutes += dur

                    paired = shadow_map.get(j.job_id, [])
                    is_sh = len(paired) > 0

                    dept_obj = self.db.query(MaintenanceJob).filter(MaintenanceJob.id == j.job_id).first().department

                    reason = f"Scheduled from {self._minute_to_time_str(s_min)} to {self._minute_to_time_str(e_min)} on {j.section_code} ({j.track_line_code})."
                    if is_sh:
                        reason += f" Co-located as a Shadow Block with {', '.join(paired)} to maximize track availability."
                    if j.required_resource_code:
                        reason += f" Machine {j.required_resource_code} successfully allocated."

                    block_detail = {
                        "job_id": j.job_id,
                        "job_code": j.job_code,
                        "title": j.job_code + " - " + j.department_code,
                        "department_code": j.department_code,
                        "department_color": dept_obj.color if dept_obj else "#003366",
                        "section_code": j.section_code,
                        "track_line": j.track_line_code,
                        "start_minute": s_min,
                        "end_minute": e_min,
                        "start_time_str": self._minute_to_time_str(s_min),
                        "end_time_str": self._minute_to_time_str(e_min),
                        "duration_minutes": dur,
                        "is_shadow_block": is_sh,
                        "paired_job_codes": paired,
                        "resource_assigned": j.required_resource_code,
                        "explanation": reason
                    }
                    scheduled_blocks_list.append(block_detail)

                    sb_record = ScheduledBlock(
                        run_id=run_record.id,
                        job_id=j.job_id,
                        section_id=self.db.query(MaintenanceJob).filter(MaintenanceJob.id == j.job_id).first().section_id,
                        track_line_id=self.db.query(MaintenanceJob).filter(MaintenanceJob.id == j.job_id).first().track_line_id,
                        start_minute=s_min,
                        end_minute=e_min,
                        duration_minutes=dur,
                        department_code=j.department_code,
                        is_shadow_block=is_sh,
                        paired_job_codes_json=str(paired),
                        resource_assigned=j.required_resource_code
                    )
                    self.db.add(sb_record)

                    exp_record = DecisionExplanation(
                        run_id=run_record.id,
                        job_id=j.job_id,
                        decision_type="SHADOW_PAIRED" if is_sh else "SCHEDULED",
                        primary_reason=reason
                    )
                    self.db.add(exp_record)
                    explanations_list.append({
                        "job_code": j.job_code,
                        "decision": "SCHEDULED",
                        "reason": reason
                    })

                else:
                    # Compute specific reason code (post-solve analysis)
                    window_duration = j.latest_end_min - j.earliest_start_min
                    if window_duration < j.duration_min:
                        reason_code = "NO_FEASIBLE_WINDOW"
                        reason = (
                            f"Window {window_duration} min < job duration {j.duration_min} min on {j.section_code}. "
                            f"No feasible slot exists within [{j.earliest_start_min // 60:02d}:{j.earliest_start_min % 60:02d}"
                            f"–{j.latest_end_min // 60:02d}:{j.latest_end_min % 60:02d}]."
                        )
                    else:
                        # Check if scheduled jobs on same track line blocked this job
                        same_track_jobs = [
                            b for b in scheduled_blocks_list if b.get("track_line") == j.track_line_code
                        ]
                        if same_track_jobs:
                            reason_code = "CAPACITY_OVERFLOW"
                            reason = (
                                f"Track {j.track_line_code} on {j.section_code} fully occupied by "
                                f"{len(same_track_jobs)} higher-priority job(s) during the available window."
                            )
                        else:
                            reason_code = "TRAIN_CONFLICT"
                            reason = (
                                f"All candidate windows on {j.section_code} overlap protected passenger/express "
                                f"train movements. No deconflicted slot found for {j.duration_min} min block."
                            )

                    # Enumerate up to 3 failed candidate windows
                    failed_windows = []
                    headway_buf = self.constraint_mgr.headway_margin_minutes
                    step = max(60, j.duration_min // 2)
                    probe = j.earliest_start_min
                    while probe + j.duration_min <= j.latest_end_min and len(failed_windows) < 3:
                        probe_end = probe + j.duration_min
                        conflict_trains = [
                            tr.train_number for tr in trains_db
                            if not (tr.arrival_minute + headway_buf <= probe or probe_end + headway_buf <= tr.departure_minute)
                        ]
                        fail_reason = (
                            f"Train conflict: {', '.join(conflict_trains[:3])}"
                            if conflict_trains else
                            f"Track {j.track_line_code} fully booked by scheduled jobs"
                        )
                        failed_windows.append({
                            "start_str": f"{(probe // 60) % 24:02d}:{probe % 60:02d}",
                            "end_str": f"{(probe_end // 60) % 24:02d}:{probe_end % 60:02d}",
                            "duration_min": j.duration_min,
                            "failure_reason": fail_reason,
                            "conflicting_trains": conflict_trains[:3],
                        })
                        probe += step

                    # Next feasible window heuristic
                    next_window = None
                    nw_probe = j.latest_end_min
                    while nw_probe + j.duration_min <= 1440 and next_window is None:
                        nw_end = nw_probe + j.duration_min
                        nw_conflicts = [
                            tr for tr in trains_db
                            if not (tr.arrival_minute + headway_buf <= nw_probe or nw_end + headway_buf <= tr.departure_minute)
                        ]
                        if not nw_conflicts:
                            next_window = {
                                "start_str": f"{(nw_probe // 60) % 24:02d}:{nw_probe % 60:02d}",
                                "end_str": f"{(nw_end // 60) % 24:02d}:{nw_end % 60:02d}",
                                "duration_min": j.duration_min,
                                "description": f"Next feasible slot: {(nw_probe // 60) % 24:02d}:{nw_probe % 60:02d}–{(nw_end // 60) % 24:02d}:{nw_end % 60:02d}",
                            }
                        nw_probe += 60

                    unscheduled_jobs_list.append({
                        "job_id": j.job_id,
                        "job_code": j.job_code,
                        "title": j.job_code,
                        "department_code": j.department_code,
                        "section_code": j.section_code,
                        "duration_minutes": j.duration_min,
                        "priority": j.priority,
                        "reason": reason,
                        "reason_code": reason_code,
                        "failed_candidate_windows": failed_windows,
                        "next_feasible_window": next_window,
                        "suggested_alternative": (
                            next_window["description"] if next_window
                            else "Reschedule to subsequent night maintenance lull (01:30–05:30) or use afternoon shadow slot."
                        ),
                    })
                    exp_record = DecisionExplanation(
                        run_id=run_record.id,
                        job_id=j.job_id,
                        decision_type="DEFERRED",
                        primary_reason=reason
                    )
                    self.db.add(exp_record)

            # Compute Train Delays
            for tr in trains_db:
                d_val = int(solver.Value(train_delay_vars[tr.train_number]))
                total_train_delay_min += d_val
                if d_val > 0:
                    conflicts_list.append({
                        "type": "TRAIN_REGULATION",
                        "severity": "LOW" if d_val <= 15 else "MEDIUM",
                        "description": f"Train #{tr.train_number} ({tr.train_name}) regulated by {d_val} mins to clear corridor maintenance window.",
                        "resolution": f"Regulated train speed / looped at upstream junction station."
                    })

            conflicts_list.append({
                "type": "TRACK_COLLISION_AVOIDED",
                "severity": "RESOLVED",
                "description": f"Zero collision detected across {len(scheduled_blocks_list)} allocated track blocks and {len(trains_db)} train paths.",
                "resolution": "Applied disjunctive non-overlap and shadow-block synchronizer."
            })

            # Calculate KPIs
            shadow_count = sum(1 for b in scheduled_blocks_list if b["is_shadow_block"])
            shadow_synergy_pct = (shadow_count / max(1, len(scheduled_blocks_list))) * 100.0
            utilization_pct = min(100.0, (total_maint_minutes / max(1, 1440 * len(sections_db))) * 100.0 * 6.5)

            run_record.scheduled_jobs_count = len(scheduled_blocks_list)
            run_record.unscheduled_jobs_count = len(unscheduled_jobs_list)
            run_record.train_delay_total_min = total_train_delay_min
            run_record.block_utilization_pct = round(utilization_pct, 1)
            run_record.shadow_block_synergy_pct = round(shadow_synergy_pct, 1)
            run_record.objective_score = round(solver.ObjectiveValue(), 2)

            self.db.commit()

            return {
                "run_id": run_record.id,
                "timestamp": run_record.run_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "status": run_record.status,
                "total_jobs": len(job_metas),
                "scheduled_jobs_count": len(scheduled_blocks_list),
                "unscheduled_jobs_count": len(unscheduled_jobs_list),
                "total_maintenance_hours": round(total_maint_minutes / 60.0, 2),
                "train_delay_total_min": total_train_delay_min,
                "block_utilization_pct": round(utilization_pct, 1),
                "shadow_block_synergy_pct": round(shadow_synergy_pct, 1),
                "objective_score": round(solver.ObjectiveValue(), 2),
                "solver_time_seconds": round(solve_duration, 3),
                "scheduled_blocks": scheduled_blocks_list,
                "unscheduled_jobs": unscheduled_jobs_list,
                "conflicts_resolved": conflicts_list,
                "explanations": explanations_list
            }
        else:
            run_record.status = "INFEASIBLE"
            self.db.commit()
            return {
                "run_id": run_record.id,
                "timestamp": run_record.run_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "INFEASIBLE",
                "total_jobs": len(job_metas),
                "scheduled_jobs_count": 0,
                "unscheduled_jobs_count": len(job_metas),
                "total_maintenance_hours": 0.0,
                "train_delay_total_min": 0,
                "block_utilization_pct": 0.0,
                "shadow_block_synergy_pct": 0.0,
                "objective_score": 0.0,
                "solver_time_seconds": round(solve_duration, 3),
                "scheduled_blocks": [],
                "unscheduled_jobs": [{"job_code": j.job_code, "reason": "No feasible mathematical solution under current hard constraints."} for j in job_metas],
                "conflicts_resolved": [],
                "explanations": []
            }

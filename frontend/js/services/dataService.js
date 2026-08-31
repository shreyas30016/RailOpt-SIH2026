/**
 * RailOpt - Data & Optimization Service Layer
 * Clean abstraction separating presentation components from API / Mock data logic.
 */

import {
    mockMaintenanceJobs,
    mockTrainMovements,
    mockBlockWindows,
    mockConstraints,
    mockOptimizedPlan,
    mockPlanChange
} from "../mockData.js";

class DataService {
    constructor() {
        this.apiBase = "";
        this.useMockOnly = false; // Toggle or auto-fallback
    }

    async fetchWithFallback(url, mockFallback, options = {}) {
        if (this.useMockOnly) {
            return mockFallback;
        }
        try {
            const res = await fetch(url, options);
            if (res.ok) {
                return await res.json();
            }
            console.warn(`API ${url} returned status ${res.status}, using mock fallback.`);
            return mockFallback;
        } catch (err) {
            console.warn(`Network fetch failed for ${url}, using mock fallback.`, err);
            return mockFallback;
        }
    }

    // 1. Dashboard Summary
    async getDashboardSummary() {
        const fallback = {
            total_active_blocks: mockOptimizedPlan.scheduledJobsCount,
            total_pending_requests: mockMaintenanceJobs.length,
            planned_blocks_today: mockOptimizedPlan.scheduledJobsCount,
            efficiency_pct: mockOptimizedPlan.blockUtilizationPct,
            shadow_block_synergy_pct: mockOptimizedPlan.shadowBlockSynergyPct,
            punctuality_impact_pct: 1.2,
            urgent_queue: mockMaintenanceJobs.filter(j => j.urgency === "CRITICAL" || j.urgency === "HIGH").map(j => ({
                id: j.id,
                job_code: j.id,
                title: j.title,
                department_code: j.department,
                department_name: j.departmentName,
                section_code: j.section,
                track_line: j.trackLine,
                duration_minutes: j.durationMinutes,
                priority: j.priority,
                urgency: j.urgency,
                requires_power_block: j.requiresPowerBlock,
                requires_traffic_block: j.requiresTrafficBlock,
                requires_speed_restriction: j.requiresSpeedRestriction,
                speed_restriction_kmh: j.speedRestrictionKmh,
                status: j.status,
                requested_date: j.requestedDate,
                earliest_start_minute: j.earliestStartMinute,
                latest_end_minute: j.latestEndMinute,
                description: j.description
            })),
            department_breakdown: {
                "ENG": mockMaintenanceJobs.filter(j => j.department === "ENG").length,
                "TRD": mockMaintenanceJobs.filter(j => j.department === "TRD").length,
                "S_T": mockMaintenanceJobs.filter(j => j.department === "S_T").length,
                "MECH": mockMaintenanceJobs.filter(j => j.department === "MECH").length
            },
            live_corridor_status: [
                { section_code: "NDLS-TKD", name: "New Delhi - Tuglakabad", length_km: 15.5, max_speed_kmh: 130, status: "CLEAR", pending_jobs: 1 },
                { section_code: "TKD-FDB", name: "Tuglakabad - Faridabad", length_km: 14.2, max_speed_kmh: 130, status: "ACTIVE_BLOCK", pending_jobs: 2 },
                { section_code: "FDB-PWL", name: "Faridabad - Palwal", length_km: 32.0, max_speed_kmh: 160, status: "ACTIVE_BLOCK", pending_jobs: 3 },
                { section_code: "PWL-KDS", name: "Palwal - Kosi Kalan", length_km: 42.0, max_speed_kmh: 160, status: "ACTIVE_BLOCK", pending_jobs: 2 },
                { section_code: "KDS-MTJ", name: "Kosi Kalan - Mathura Jn", length_km: 44.5, max_speed_kmh: 160, status: "CLEAR", pending_jobs: 0 },
                { section_code: "MTJ-AGC", name: "Mathura Jn - Agra Cantt", length_km: 53.8, max_speed_kmh: 160, status: "PLANNED", pending_jobs: 1 }
            ]
        };

        return await this.fetchWithFallback(`${this.apiBase}/api/dashboard/summary`, fallback);
    }

    // 2. Maintenance Requests
    async getMaintenanceRequests(filters = {}) {
        let fallback = [...mockMaintenanceJobs];
        if (filters.department) {
            fallback = fallback.filter(j => j.department === filters.department);
        }
        if (filters.urgency) {
            fallback = fallback.filter(j => j.urgency === filters.urgency);
        }
        if (filters.section) {
            fallback = fallback.filter(j => j.section === filters.section);
        }

        const normalizedFallback = fallback.map(j => ({
            id: j.id,
            job_code: j.id,
            title: j.title,
            department_code: j.department,
            department_name: j.departmentName,
            section_code: j.section,
            track_line: j.trackLine,
            duration_minutes: j.durationMinutes,
            priority: j.priority,
            urgency: j.urgency,
            requires_power_block: j.requiresPowerBlock,
            requires_traffic_block: j.requiresTrafficBlock,
            requires_speed_restriction: j.requiresSpeedRestriction,
            speed_restriction_kmh: j.speedRestrictionKmh,
            status: j.status,
            requested_date: j.requestedDate,
            earliest_start_minute: j.earliestStartMinute,
            latest_end_minute: j.latestEndMinute,
            description: j.description
        }));

        let query = new URLSearchParams(filters).toString();
        return await this.fetchWithFallback(`${this.apiBase}/api/maintenance/requests?${query}`, normalizedFallback);
    }

    // 3. Block Windows & Timetable
    async getBlockWindows() {
        return mockBlockWindows;
    }

    async getTrainMovements() {
        return mockTrainMovements;
    }

    // 4. Optimization Plan
    async getOptimizedPlan() {
        const fallback = {
            run_id: mockOptimizedPlan.runId,
            timestamp: mockOptimizedPlan.timestamp,
            status: mockOptimizedPlan.status,
            total_jobs: mockOptimizedPlan.totalJobsConsidered,
            scheduled_jobs_count: mockOptimizedPlan.scheduledJobsCount,
            unscheduled_jobs_count: mockOptimizedPlan.unscheduledJobsCount,
            total_maintenance_hours: mockOptimizedPlan.totalMaintenanceHours,
            train_delay_total_min: mockOptimizedPlan.totalTrainDelayMinutes,
            block_utilization_pct: mockOptimizedPlan.blockUtilizationPct,
            shadow_block_synergy_pct: mockOptimizedPlan.shadowBlockSynergyPct,
            objective_score: mockOptimizedPlan.objectiveScore,
            solver_time_seconds: mockOptimizedPlan.solverTimeSeconds,
            scheduled_blocks: mockOptimizedPlan.scheduledBlocks.map(b => ({
                job_id: b.jobId,
                job_code: b.jobId,
                title: b.title,
                department_code: b.department,
                department_color: b.departmentColor,
                section_code: b.section,
                track_line: b.trackLine,
                start_minute: b.startMinute,
                end_minute: b.endMinute,
                start_time_str: b.startTimeStr,
                end_time_str: b.endTimeStr,
                duration_minutes: b.durationMinutes,
                is_shadow_block: b.isShadowBlock,
                paired_job_codes: b.pairedJobIds,
                resource_assigned: b.resourceAssigned,
                affected_trains: b.affectedTrains,
                explanation: b.decisionExplanation
            })),
            unscheduled_jobs: mockOptimizedPlan.unscheduledJobs,
            conflicts_resolved: mockOptimizedPlan.conflictsResolved.map(c => ({
                type: c.conflictType,
                severity: c.severity,
                description: c.description,
                resolution: c.resolutionApplied
            })),
            explanations: mockOptimizedPlan.scheduledBlocks.map(b => ({
                job_code: b.jobId,
                decision: "SCHEDULED",
                reason: b.decisionExplanation
            }))
        };

        return await this.fetchWithFallback(`${this.apiBase}/api/optimization/latest`, fallback);
    }

    // 5. Trigger Optimization Solver
    async runOptimization(params = {}) {
        const payload = {
            max_solver_time_sec: params.maxSolverTimeSec || 15,
            minimize_passenger_delays: params.minimizePassengerDelays !== false,
            maximize_shadow_blocks: params.maximizeShadowBlocks !== false
        };

        return await this.fetchWithFallback(`${this.apiBase}/api/optimization/run`, mockOptimizedPlan, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
    }

    // 6. Job Decision Audit / Explanation
    async getJobDecisionAudit(jobId) {
        const job = mockMaintenanceJobs.find(j => j.id === jobId);
        const block = mockOptimizedPlan.scheduledBlocks.find(b => b.jobId === jobId);

        const fallback = {
            job_code: jobId,
            status: block ? "SCHEDULED" : "DEFERRED",
            summary: block ? block.decisionExplanation : "Deferred due to high traffic density.",
            reasoning_tree: block ? [
                {
                    step: 1,
                    title: "Corridor Maintenance Window Check",
                    status: "PASSED",
                    detail: `Allocated within approved lull (${block.startTimeStr} - ${block.endTimeStr}) on ${block.section}.`
                },
                {
                    step: 2,
                    title: "Traction & Safety Power Isolation Check",
                    status: "PASSED",
                    detail: job?.requiresPowerBlock ? "Synchronized with Traction OHE power block." : "Standard track circuit protection verified."
                },
                {
                    step: 3,
                    title: "Machine Resource Allocation",
                    status: "PASSED",
                    detail: `Machine '${block.resourceAssigned || 'P-Way Gang'}' confirmed available with 0 conflicts.`
                },
                {
                    step: 4,
                    title: "Shadow Block Synergy Optimization",
                    status: block.isShadowBlock ? "OPTIMIZED" : "STANDALONE",
                    detail: block.isShadowBlock ? `Co-located with ${block.pairedJobIds.join(', ')} to maximize track availability.` : "Dedicated block allocated."
                }
            ] : [
                {
                    step: 1,
                    title: "Track Section Capacity Check",
                    status: "CONFLICT",
                    detail: "Corridor capacity exceeded by higher priority passenger traffic."
                }
            ]
        };

        return await this.fetchWithFallback(`${this.apiBase}/api/optimization/explanation/${jobId}`, fallback);
    }

    // 7. Gantt Timeline Data
    async getGanttTimelineData() {
        const sections = [
            { id: 1, code: "NDLS-TKD" },
            { id: 2, code: "TKD-FDB" },
            { id: 3, code: "FDB-PWL" },
            { id: 4, code: "PWL-KDS" },
            { id: 5, code: "KDS-MTJ" },
            { id: 6, code: "MTJ-AGC" }
        ];

        const tracks = [];
        sections.forEach(s => {
            ["UP", "DN"].forEach(dir => {
                const lineCode = `${s.code}_${dir}`;
                const blocks = mockOptimizedPlan.scheduledBlocks
                    .filter(b => b.trackLine === lineCode)
                    .map(b => ({
                        id: b.blockId,
                        job_code: b.jobId,
                        title: b.title,
                        department: b.department,
                        color: b.departmentColor,
                        start_minute: b.startMinute,
                        end_minute: b.endMinute,
                        start_time_str: b.startTimeStr,
                        end_time_str: b.endTimeStr,
                        is_shadow: b.isShadowBlock,
                        paired_jobs: b.pairedJobIds,
                        resource: b.resourceAssigned
                    }));

                tracks.push({
                    section_code: s.code,
                    track_line_code: lineCode,
                    line_type: dir,
                    label: `${s.code} (${dir}_MAIN)`,
                    blocks: blocks
                });
            });

            if (["TKD-FDB", "FDB-PWL"].includes(s.code)) {
                const lineCode = `${s.code}_3RD`;
                const blocks = mockOptimizedPlan.scheduledBlocks
                    .filter(b => b.trackLine === lineCode)
                    .map(b => ({
                        id: b.blockId,
                        job_code: b.jobId,
                        title: b.title,
                        department: b.department,
                        color: b.departmentColor,
                        start_minute: b.startMinute,
                        end_minute: b.endMinute,
                        start_time_str: b.startTimeStr,
                        end_time_str: b.endTimeStr,
                        is_shadow: b.isShadowBlock,
                        paired_jobs: b.pairedJobIds,
                        resource: b.resourceAssigned
                    }));

                tracks.push({
                    section_code: s.code,
                    track_line_code: lineCode,
                    line_type: "3RD",
                    label: `${s.code} (3RD_LINE)`,
                    blocks: blocks
                });
            }
        });

        const fallback = {
            timeline_start_minute: 0,
            timeline_end_minute: 1440,
            tracks: tracks,
            trains: mockTrainMovements.map(t => ({
                train_number: t.trainNumber,
                train_name: t.trainName,
                train_type: t.trainType,
                priority: t.priorityWeight,
                direction: t.direction,
                departure_minute: t.departureMinute,
                arrival_minute: t.arrivalMinute,
                departure_time_str: t.departureTimeStr,
                arrival_time_str: t.arrivalTimeStr
            })),
            windows: mockBlockWindows.map(w => ({
                window_code: w.id,
                section_code: w.section,
                start_minute: w.startMinute,
                end_minute: w.endMinute,
                window_type: w.windowType
            }))
        };

        return await this.fetchWithFallback(`${this.apiBase}/api/gantt/timeline`, fallback);
    }

    // 8. What-If Simulation
    async simulateWhatIf(scenarioParams) {
        const payload = {
            scenario_name: scenarioParams.scenarioName || "Emergency What-If Injection",
            emergency_job: scenarioParams.emergencyJob,
            simulated_train_delay_min: scenarioParams.trainDelayMin || 20
        };

        const fallback = {
            scenario_name: payload.scenario_name,
            baseline_run_id: 101,
            simulated_run: {
                ...mockOptimizedPlan,
                scheduled_jobs_count: mockOptimizedPlan.scheduledJobsCount + (scenarioParams.emergencyJob ? 1 : 0),
                total_maintenance_hours: mockOptimizedPlan.totalMaintenanceHours + (scenarioParams.emergencyJob ? scenarioParams.emergencyJob.duration_minutes / 60 : 0),
                train_delay_total_min: mockOptimizedPlan.totalTrainDelayMinutes + (scenarioParams.trainDelayMin || 0)
            },
            delta_scheduled_jobs: scenarioParams.emergencyJob ? 1 : 0,
            delta_train_delay_min: scenarioParams.trainDelayMin || 20,
            delta_utilization_pct: 2.6,
            critical_alerts: mockPlanChange.criticalAlerts,
            impact_summary: mockPlanChange.impactSummary
        };

        return await this.fetchWithFallback(`${this.apiBase}/api/whatif/simulate`, fallback, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
    }

    // 9. Operational Reports & Analytics
    async getOperationalReports() {
        const fallback = {
            kpis: {
                total_blocks_executed_ytd: 1420,
                average_grant_ratio_pct: 95.8,
                punctuality_loss_reduction_pct: 28.4,
                shadow_block_savings_hours: 142.5,
                safety_compliance_pct: 100.0
            },
            department_statistics: [
                { code: "ENG", name: "Civil Engineering", requested: 4, scheduled: 4, grant_rate: 100.0, color: "#003366" },
                { code: "TRD", name: "Traction Distribution", requested: 2, scheduled: 2, grant_rate: 100.0, color: "#d97706" },
                { code: "S_T", name: "Signaling & Telecom", requested: 3, scheduled: 3, grant_rate: 100.0, color: "#0284c7" },
                { code: "MECH", name: "Mechanical", requested: 1, scheduled: 1, grant_rate: 100.0, color: "#4b5563" }
            ],
            historical_optimization_runs: [
                { run_id: 101, timestamp: "01 Sep 06:00", status: "OPTIMAL", scheduled: 10, train_delay_min: 92, utilization: 94.2, synergy: 70.0, solver_time_sec: 0.84 },
                { run_id: 100, timestamp: "31 Aug 06:00", status: "OPTIMAL", scheduled: 9, train_delay_min: 75, utilization: 88.5, synergy: 66.7, solver_time_sec: 0.72 },
                { run_id: 99, timestamp: "30 Aug 06:00", status: "FEASIBLE", scheduled: 8, train_delay_min: 110, utilization: 84.0, synergy: 50.0, solver_time_sec: 1.15 }
            ]
        };

        return await this.fetchWithFallback(`${this.apiBase}/api/reports/analytics`, fallback);
    }
}

export const dataService = new DataService();

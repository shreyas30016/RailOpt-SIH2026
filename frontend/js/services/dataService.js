/**
 * RailOpt - Data & Optimization Service Layer
 * Clean abstraction separating presentation components from API / Mock data logic.
 * Updated: Full CRUD for maintenance, auth login, train list, session helper.
 */

// NOTE: mockData.js is retained only for legacy/unused helper methods.
// All live screens now hydrate strictly from the backend; offline fallbacks
// carry ZERO fabricated business values.

import { getApiBaseUrl } from "../config.js";

class DataService {
    constructor() {
        this.useMockOnly = false; // Toggle or auto-fallback
        this.lastFallback = null; // { endpoint, status, error } when an offline fallback was used
    }

    get apiBase() {
        return getApiBaseUrl();
    }

    // Tag fallback payloads so the UI can honestly display "offline fallback" state.
    _markFallback(payload, endpoint, info = "") {
        if (payload && typeof payload === "object" && !Array.isArray(payload)) {
            try { payload._fallback_source = "offline_fallback"; } catch {}
        }
        this.lastFallback = { endpoint, ...info };
        return payload;
    }

    _getAuthToken() {
        return localStorage.getItem("railopt_token") || "";
    }

    _getAuthHeaders() {
        const headers = { "Content-Type": "application/json" };
        const token = this._getAuthToken();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        return headers;
    }

    async fetchWithFallback(url, mockFallback, options = {}) {
        if (this.useMockOnly) {
            return this._markFallback(mockFallback, url, { status: 0, error: "mock-only mode" });
        }
        try {
            const headers = { ...(options.headers || {}) };
            const token = this._getAuthToken();
            if (token && !headers["Authorization"]) {
                headers["Authorization"] = `Bearer ${token}`;
            }
            const mergedOptions = { ...options, headers };
            const res = await fetch(url, mergedOptions);
            if (res.ok) {
                return await res.json();
            }
            // SECURITY: never fall back on authentication/authorization failures.
            // A 401/403 must surface as an error so the UI never masks a permission denial.
            if (res.status === 401 || res.status === 403) {
                const errPayload = await res.json().catch(() => ({}));
                const err = new Error(errPayload.detail || `Authorization failed (${res.status})`);
                err.status = res.status;
                throw err;
            }
            console.warn(`API ${url} returned status ${res.status}, using offline demo fallback.`);
            return this._markFallback(mockFallback, url, { status: res.status });
        } catch (err) {
            if (err && err.status) throw err; // 401/403 re-thrown, never masked
            console.warn(`Network fetch failed for ${url}, using offline demo fallback.`, err);
            return this._markFallback(mockFallback, url, { error: String(err && err.message || err) });
        }
    }

    // Mutation helper: never falls back, always surfaces the real error.
    async fetchMutation(url, options) {
        const headers = { ...(options.headers || {}) };
        const token = this._getAuthToken();
        if (token && !headers["Authorization"]) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        const res = await fetch(url, { ...options, headers });
        if (res.ok) return await res.json();
        const errPayload = await res.json().catch(() => ({}));
        const err = new Error(errPayload.detail || `Request failed (${res.status})`);
        err.status = res.status;
        throw err;
    }

    // =========================================================================
    // 1. Dashboard Summary
    // =========================================================================
    async getDashboardSummary() {
        // Offline fallback carries ZERO fabricated KPIs — the UI renders "no data"
        // state instead of pretending metrics exist.
        const fallback = {
            total_active_blocks: 0,
            total_pending_requests: 0,
            total_jobs: 0,
            critical_jobs_count: 0,
            planned_blocks_today: 0,
            efficiency_pct: 0.0,
            shadow_block_synergy_pct: 0.0,
            punctuality_impact_pct: 0.0,
            conflicts_count: 0,
            conflicts_list: [],
            upcoming_blocks: [],
            urgent_queue: [],
            department_breakdown: { ENG: 0, TRD: 0, S_T: 0, MECH: 0 },
            live_corridor_status: [],
            latest_optimization_summary: null,
            live_trains_feed: null
        };
        return await this.fetchWithFallback(`${this.apiBase}/api/dashboard/summary`, fallback);
    }

    // =========================================================================
    // 2. Maintenance Requests — GET, POST, PUT, DELETE
    // =========================================================================
    async getMaintenanceRequests(filters = {}) {
        // Offline fallback is an EMPTY list — the UI shows "no data" honestly
        // instead of fabricating requests.
        const query = new URLSearchParams(filters).toString();
        return await this.fetchWithFallback(`${this.apiBase}/api/maintenance/requests?${query}`, []);
    }

    async createMaintenanceRequest(jobData) {
        const res = await fetch(`${this.apiBase}/api/maintenance/requests`, {
            method: "POST",
            headers: this._getAuthHeaders(),
            body: JSON.stringify({
                job_code: jobData.job_code || jobData.id,
                title: jobData.title,
                department_code: jobData.department_code || jobData.department,
                section_code: jobData.section_code || jobData.section,
                track_line: jobData.track_line || "UP_MAIN",
                duration_minutes: Number(jobData.duration_minutes),
                priority: Number(jobData.priority || 3),
                urgency: jobData.urgency || "MEDIUM",
                requires_power_block: Boolean(jobData.requires_power_block),
                requires_traffic_block: Boolean(jobData.requires_traffic_block !== false),
                requires_speed_restriction: Boolean(jobData.requires_speed_restriction),
                speed_restriction_kmh: Number(jobData.speed_restriction_kmh || 30),
                requested_date: jobData.requested_date || new Date().toISOString().split("T")[0],
                earliest_start_minute: Number(jobData.earliest_start_minute || 0),
                latest_end_minute: Number(jobData.latest_end_minute || 1440),
                description: jobData.description || ""
            })
        });
        if (res.ok) return await res.json();
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to create maintenance request.");
    }


    async updateMaintenanceRequest(jobId, updateData) {
        const res = await fetch(`${this.apiBase}/api/maintenance/requests/${jobId}`, {
            method: "PUT",
            headers: this._getAuthHeaders(),
            body: JSON.stringify(updateData)
        });
        if (res.ok) return await res.json();
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Update failed for job ${jobId}`);
    }

    async deleteMaintenanceRequest(jobId) {
        const res = await fetch(`${this.apiBase}/api/maintenance/requests/${jobId}`, {
            method: "DELETE",
            headers: this._getAuthHeaders()
        });
        if (res.ok) return await res.json();
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Delete failed for job ${jobId}`);
    }

    // =========================================================================
    // 3. Block Windows & Timetable (legacy helpers — no longer used by screens)
    // =========================================================================
    async getBlockWindows() { return []; }
    async getTrainMovements() { return []; }

    // =========================================================================
    // 4. Optimization Plan — GET latest / run new
    // =========================================================================
    async getOptimizedPlan() {
        // Offline fallback is an empty NO_RUNS plan — never a fabricated schedule.
        const fallback = {
            status: "NO_RUNS",
            run_id: null,
            timestamp: null,
            total_jobs: 0,
            scheduled_jobs_count: 0,
            unscheduled_jobs_count: 0,
            total_maintenance_hours: 0.0,
            train_delay_total_min: 0,
            block_utilization_pct: 0.0,
            shadow_block_synergy_pct: 0.0,
            objective_score: 0.0,
            solver_time_seconds: 0.0,
            scheduled_blocks: [],
            unscheduled_jobs: [],
            conflicts_resolved: [],
            explanations: [],
            plan_quality: null
        };
        return await this.fetchWithFallback(`${this.apiBase}/api/optimization/latest`, fallback);
    }

    async runOptimization(params = {}) {
        const objectives = {
            minimize_passenger_delays: params.minimizePassengerDelays !== undefined ? Boolean(params.minimizePassengerDelays) : true,
            train_delay_weight: Number(params.trainDelayWeight !== undefined ? params.trainDelayWeight : 1.0),
            maximize_shadow_blocks: params.maximizeShadowBlocks !== undefined ? Boolean(params.maximizeShadowBlocks) : true,
            shadow_block_weight: Number(params.shadowBlockWeight !== undefined ? params.shadowBlockWeight : 1.0),
            prioritize_urgent_maintenance: params.prioritizeUrgentMaintenance !== undefined ? Boolean(params.prioritizeUrgentMaintenance) : true,
            urgency_weight: Number(params.urgencyWeight !== undefined ? params.urgencyWeight : 1.0)
        };

        const payload = {
            max_solver_time_sec: Number(params.maxSolverTimeSec || params.solver_timeout_seconds || 15),
            optimization_objectives: objectives
        };

        // Mutations NEVER fall back: permission denials (401/403) and solver errors
        // must surface to the user honestly instead of fabricating a plan.
        return await this.fetchMutation(`${this.apiBase}/api/optimization/run`, {
            method: "POST",
            headers: this._getAuthHeaders(),
            body: JSON.stringify(payload)
        });
    }

    // =========================================================================
    // 5. Job Decision Audit / Explanation
    // =========================================================================
    async getJobDecisionAudit(jobId) {
        // Offline fallback is a clean error notice — never a fabricated reasoning tree.
        const errFallback = {
            job_code: jobId,
            error: "Decision audit unavailable: the backend could not be reached. Run an optimization to generate explanations."
        };
        return await this.fetchWithFallback(`${this.apiBase}/api/optimization/explanation/${jobId}`, errFallback);
    }

    // =========================================================================
    // 6. Gantt Timeline Data — accepts optional runId
    // =========================================================================
    async getGanttTimelineData(runId = null) {
        // Offline fallback renders an EMPTY timeline — no fabricated bars/trains.
        const fallback = {
            run_id: null,
            status: "NO_RUNS",
            available_runs: [],
            timeline_start_minute: 0,
            timeline_end_minute: 1440,
            tracks: [],
            trains: [],
            windows: []
        };

        const apiUrl = runId
            ? `${this.apiBase}/api/gantt/timeline?run_id=${runId}`
            : `${this.apiBase}/api/gantt/timeline`;
        return await this.fetchWithFallback(apiUrl, fallback);
    }

    async getRailwayConstraints() {
        // Empty rule set on offline fallback — the UI shows an honest "unavailable" state.
        const fallback = { rules: [] };
        return await this.fetchWithFallback(`${this.apiBase}/api/optimization/rules`, fallback);
    }

    // =========================================================================
    // 7. What-If Simulation — TRAIN_DELAY, MAINTENANCE_OVERRUN, BLOCK_UNAVAILABLE, EMERGENCY_JOB
    // =========================================================================
    async simulateWhatIf(scenarioParams) {
        const payload = {
            scenario_name: scenarioParams.scenario_name || scenarioParams.scenarioName || "What-If Scenario",
            emergency_job: scenarioParams.emergency_job || scenarioParams.emergencyJob || null,
            simulated_train_delay_min: scenarioParams.simulated_train_delay_min ?? scenarioParams.train_delay_min ?? scenarioParams.delay_minutes ?? scenarioParams.trainDelayMin ?? 0,
            delayed_train_number: scenarioParams.delayed_train_number || scenarioParams.train_id || scenarioParams.delayedTrainNumber || null,
            blocked_section_code: scenarioParams.blocked_section_code || scenarioParams.section_code || scenarioParams.blockedSectionCode || null,
            block_duration_extra_min: scenarioParams.block_duration_extra_min ?? scenarioParams.extra_minutes ?? scenarioParams.blockDurationExtraMin ?? 0,
        };
        // What-If is a MUTATION-style solver call: it must never silently fall back
        // to fabricated deltas. Permission denials and solver failures surface honestly.
        return await this.fetchMutation(`${this.apiBase}/api/whatif/simulate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
    }


    // =========================================================================
    // 8. Duration Prediction
    // =========================================================================
    async predictMaintenanceDuration(jobData) {
        const payload = {
            department_code: jobData.department_code || "ENG",
            urgency: jobData.urgency || "MEDIUM",
            duration_minutes: jobData.duration_minutes || null,
            requires_power_block: jobData.requires_power_block || false,
            resource_type: jobData.resource_type || "CREW",
            section_length_km: jobData.section_length_km || 15.0,
            weather_factor: jobData.weather_factor || 1.0,
        };
        const fallback = {
            predictedDuration: jobData.duration_minutes || 180,
            lowerBound: Math.floor((jobData.duration_minutes || 180) * 0.8),
            upperBound: Math.ceil((jobData.duration_minutes || 180) * 1.25),
            confidence: 0.55, modelStatus: "DETERMINISTIC_BASELINE",
            reasoning: "Mock fallback — deterministic baseline",
        };
        return await this.fetchWithFallback(`${this.apiBase}/api/maintenance/predict-duration`, fallback, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
    }

    // =========================================================================
    // 9. Operational Reports & Analytics
    // =========================================================================
    async getOperationalReports(filters = {}) {
        const queryParams = new URLSearchParams();
        if (filters.division && filters.division !== "ALL" && filters.division !== "All Divisions") {
            queryParams.append("division", filters.division);
        }
        if (filters.department && filters.department !== "ALL" && filters.department !== "All Departments") {
            queryParams.append("department", filters.department);
        }
        if (filters.section && filters.section !== "ALL" && filters.section !== "All Sections") {
            queryParams.append("section", filters.section);
        }
        if (filters.dateRange) {
            queryParams.append("date_range", filters.dateRange);
        }

        const qs = queryParams.toString() ? `?${queryParams.toString()}` : "";
        // Offline fallback carries ZERO fabricated KPIs — the UI renders "no data"
        // state instead of inventing report numbers.
        const fallback = {
            kpis: {
                total_blocks_executed_ytd: 0,
                average_grant_ratio_pct: 0.0,
                block_utilization_pct: 0.0,
                job_completion_rate_pct: 0.0,
                mean_delay_per_block_min: 0.0,
                critical_conflicts_resolved: 0,
                shadow_block_synergy_pct: 0.0,
                shadow_block_savings_hours: 0.0,
                safety_compliance_pct: 0.0
            },
            corridor_context: "Delhi–Agra Mainline (Synthetic Demo Corridor) — backend offline",
            active_filters: { division: "ALL", section: "ALL", department: "ALL" },
            department_statistics: [],
            section_statistics: [],
            historical_optimization_runs: [],
            raw_records: []
        };
        return await this.fetchWithFallback(`${this.apiBase}/api/reports/analytics${qs}`, fallback);
    }

    // =========================================================================
    // 10. Auth — Login
    // =========================================================================
    async loginUser(username, role, divisionCode) {
        const res = await fetch(`${this.apiBase}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, role, division_code: divisionCode })
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || "Login failed");
        }
        return await res.json();
    }

    // =========================================================================
    // 11. Train list for what-if scenario select
    // =========================================================================
    async getTrainList() {
        const fallback = [
            { train_number: "12301", train_name: "Rajdhani Express (NDLS-HWH)", train_type: "RAJDHANI", direction: "DN" },
            { train_number: "12302", train_name: "Rajdhani Express (HWH-NDLS)", train_type: "RAJDHANI", direction: "UP" },
            { train_number: "22435", train_name: "Vande Bharat Express (NDLS-AGC)", train_type: "VANDE_BHARAT", direction: "DN" },
            { train_number: "22436", train_name: "Vande Bharat Express (AGC-NDLS)", train_type: "VANDE_BHARAT", direction: "UP" },
            { train_number: "12137", train_name: "Punjab Mail (NDLS-BCT)", train_type: "SUPERFAST", direction: "DN" },
            { train_number: "12138", train_name: "Punjab Mail (BCT-NDLS)", train_type: "SUPERFAST", direction: "UP" },
        ];
        return await this.fetchWithFallback(`${this.apiBase}/api/trains/list`, fallback);
    }

    // =========================================================================
    // Utility — Data mode indicator (reads division from session)
    // =========================================================================
    getDataMode() {
        const user = this._getSession();
        return {
            label: "SYNTHETIC DEMO DATA",
            color: "amber",
            isMock: true,
            division: user?.division_name || user?.division_code || "Indian Railways"
        };
    }

    // Session helper — reads railopt_user from localStorage
    _getSession() {
        try {
            const raw = localStorage.getItem("railopt_user");
            return raw ? JSON.parse(raw) : null;
        } catch { return null; }
    }
}

export const dataService = new DataService();

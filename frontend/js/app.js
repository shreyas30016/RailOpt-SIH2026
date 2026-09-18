/**
 * RailOpt - Frontend Application Logic & Event Orchestration
 * Full-Stack integration coordinating Real Backend APIs, Role-Based Session,
 * Dynamic Filters, CP-SAT Optimization, Gantt Visualization, and What-if Analysis.
 */

import { dataService } from "./services/dataService.js";
import { trainDataService } from "./services/trainDataService.js";
import { createJobTableRow } from "./components/jobRow.js";
import { createScheduledBlockRow, createConflictCard } from "./components/planRow.js";
import { createLiveTrainFeedContainer } from "./components/trainStatusCard.js";
import { createGanttRow, createGanttTrainRow, createGanttWindowRow } from "./components/ganttRow.js";
import { renderDecisionAuditModal } from "./components/optimizationResultView.js";
import { renderNewRequestModal } from "./components/newRequestModal.js";
import { renderRequestDetailSidebar, renderEmptyRequestDetailSidebar } from "./components/requestDetailSidebar.js";
import { computeScheduleChanges, renderScheduleDiffTable, renderComparativeTimelineBars, createWhatIfAlert } from "./components/whatIfScenarioView.js";
import { appState } from "./appState.js";


// Global Decision Explainer Modal Handler
window.showJobExplanation = async function(jobCode) {
    if (!jobCode) return;
    try {
        const auditData = await dataService.getJobDecisionAudit(jobCode);
        renderDecisionAuditModal(auditData);
    } catch (err) {
        console.error("Error loading decision explanation for " + jobCode + ":", err);
        renderDecisionAuditModal({
            job_code: jobCode,
            error: `Could not fetch explanation from server (${err.message}).`
        });
    }
};

// Global New Maintenance Request Modal Trigger
window.triggerNewRequestModal = function() {
    renderNewRequestModal({
        onSuccess: async (newJob) => {
            _showToast(`Maintenance request ${newJob.job_code} created successfully!`, "success");
            if (window.location.pathname.includes("maintenance-requests") || window.location.pathname.endsWith("/maintenance-requests.html")) {
                await initMaintenanceRequests(newJob.id);
            }
        }
    });
};



// ============================================================
// Auth Guard & Session Helpers
// ============================================================
function _getSession() {
    try {
        const raw = localStorage.getItem("railopt_user");
        if (!raw) return null;
        const user = JSON.parse(raw);
        if (user && user.role) {
            const roleUpper = user.role.toUpperCase();
            if (user.can_approve === undefined) {
                user.can_approve = (roleUpper === "CONTROLLER" || roleUpper === "PLANNER");
            }
            if (user.can_optimize === undefined) {
                user.can_optimize = (roleUpper === "CONTROLLER" || roleUpper === "PLANNER");
            }
        }
        return user;
    } catch { return null; }
}

function _requireAuth() {
    const path = window.location.pathname.toLowerCase();
    if (path === "/login" || path.includes("login.html")) return;
    const user = _getSession();
    if (!user) {
        window.location.href = "/login";
        return;
    }

    // Role-based route guard: field submitters cannot open planner or what-if
    const fieldRoles = ["ENGINEER", "TRD_OFFICER", "ST_OFFICER"];
    if (fieldRoles.includes(user.role)) {
        if (path.includes("block-planning") || path.includes("what-if")) {
            window.location.href = "/maintenance-requests";
        }
    }
}

// Immediate top-level auth guard execution
_requireAuth();

function _logout() {
    localStorage.removeItem("railopt_user");
    localStorage.removeItem("railopt_token");
    sessionStorage.removeItem("railopt_active_run_id");
    _showToast("Signed out successfully. Redirecting...", "warning");
    setTimeout(() => {
        window.location.href = "/login";
    }, 400);
}

function _updateHeaderFromSession() {
    const user = _getSession();
    if (!user) return;

    // Division badge in top header
    const divBadge = document.getElementById("header-division-badge");
    if (divBadge) divBadge.textContent = user.division_name || user.division_code || "Indian Railways";

    // User avatar letter
    const avatar = document.getElementById("header-user-avatar");
    if (avatar) avatar.textContent = user.initial || (user.role ? user.role[0] : "C");

    // Role text in desktop & mobile chips
    const roleLabel = user.role_label || user.role || "Controller";
    const cleanRoleName = roleLabel.includes("(") ? roleLabel.split(" (")[0].trim() : roleLabel;
    const deskRole = document.getElementById("header-user-role");
    if (deskRole) deskRole.textContent = cleanRoleName;

    const mobRole = document.getElementById("mobile-user-role");
    if (mobRole) mobRole.textContent = cleanRoleName;

    // Live clock update
    const dtEl = document.getElementById("header-datetime");
    if (dtEl) {
        const now = new Date();
        const dStr = now.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
        const tStr = now.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
        dtEl.textContent = `${dStr} | ${tStr}`;
    }
}

// Toast helper
function _showToast(message, type = "success") {
    const COLORS = {
        success: { bg: "bg-emerald-700", icon: "check_circle", iconColor: "text-emerald-300" },
        warning: { bg: "bg-amber-700", icon: "warning", iconColor: "text-amber-300" },
        error: { bg: "bg-red-700", icon: "error", iconColor: "text-red-300" }
    };
    const c = COLORS[type] || COLORS.success;
    const toast = document.createElement("div");
    toast.className = `fixed bottom-5 right-5 ${c.bg} text-white px-5 py-3.5 rounded-xl shadow-2xl z-50 flex items-center gap-3 animate-slide-up`;
    toast.innerHTML = `
        <span class="material-symbols-outlined ${c.iconColor} text-[20px]">${c.icon}</span>
        <span class="text-[13px] font-semibold">${message}</span>
        <button onclick="this.parentElement.remove()" class="ml-3 opacity-70 hover:opacity-100 font-bold">✕</button>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4500);
}

// ============================================================
// 1. Navigation, Header Synchronization, Popovers & Dialogs
// ============================================================
function setupNavigation() {
    const path = window.location.pathname.toLowerCase();
    const user = _getSession();
    const fieldRoles = ["ENGINEER", "TRD_OFFICER", "ST_OFFICER"];
    
    // Sidebar Active State Sync
    const navMap = {
        "/dashboard": "nav-dashboard",
        "/": "nav-dashboard",
        "/maintenance-requests": "nav-maintenance-requests",
        "/block-planning": "nav-block-planning",
        "/gantt-view": "nav-gantt-view",
        "/what-if": "nav-what-if",
        "/constraints-logic": "nav-constraints-logic",
        "/reports": "nav-reports"
    };

    document.querySelectorAll(".sidebar-item a").forEach(el => {
        el.className = "flex items-center gap-sm px-md py-sm rounded-lg text-on-primary-container opacity-70 hover:bg-primary-container hover:opacity-100 transition-all duration-150 active:scale-[0.98]";
    });

    for (const [route, id] of Object.entries(navMap)) {
        if (path === route || path.endsWith(route) || (route !== "/" && path.includes(route))) {
            const activeEl = document.getElementById(id);
            if (activeEl) {
                activeEl.className = "flex items-center gap-sm px-md py-sm rounded-lg bg-primary-container text-on-primary-container border-l-4 border-on-primary-container font-semibold transition-all duration-150 active:scale-[0.98]";
            }
            break;
        }
    }

    // Role-Specific Sidebar Visibility Adjustments
    if (user && fieldRoles.includes(user.role)) {
        // Hide Block Planning & What-If for field officers
        const bpNav = document.getElementById("nav-block-planning");
        if (bpNav && bpNav.closest("li")) bpNav.closest("li").style.display = "none";

        const wiNav = document.getElementById("nav-what-if");
        if (wiNav && wiNav.closest("li")) wiNav.closest("li").style.display = "none";

        // Scoped label for Maintenance Requests
        const maintNav = document.getElementById("nav-maintenance-requests");
        if (maintNav) {
            const labelEl = maintNav.querySelector(".font-label-md") || maintNav.querySelector("span:last-child");
            if (labelEl) {
                if (user.role === "ENGINEER") labelEl.textContent = "Engineering Requests";
                else if (user.role === "TRD_OFFICER") labelEl.textContent = "TRD / OHE Requests";
                else if (user.role === "ST_OFFICER") labelEl.textContent = "S&T Requests";
            }
        }
    }

    // Direct Header Logout Button
    const btnLogout = document.getElementById("btn-header-logout");
    const btnMobLogout = document.getElementById("btn-mobile-logout");
    if (btnLogout) btnLogout.onclick = (e) => { e.stopPropagation(); _logout(); };
    if (btnMobLogout) btnMobLogout.onclick = (e) => { e.stopPropagation(); _logout(); };

    // Profile Popover
    const profileBtn = document.getElementById("header-user-profile") || document.getElementById("mobile-user-profile");
    if (profileBtn) {
        profileBtn.onclick = (e) => {
            e.stopPropagation();
            let pop = document.getElementById("profile-popover");
            if (pop) { pop.remove(); return; }

            const user = _getSession();
            const roleLabel = user?.role_label || user?.role || "Controller";
            const division = user?.division_name || user?.division_code || "Indian Railways";
            const initial = user?.initial || (user?.role ? user.role[0] : "C");
            const canApprove = user?.can_approve ? "✅ Full Approval Rights" : "❌ Request Only (No Approval)";
            const staffId = user?.staff_id || `${user?.division_code || 'IR'}-${user?.role || 'OFFICER'}-9021`;
            const corridor = user?.corridor || `${division} Corridor`;

            pop = document.createElement("div");
            pop.id = "profile-popover";
            pop.className = "absolute right-4 top-16 w-80 bg-surface-container-lowest border border-outline-variant rounded-xl shadow-2xl z-50 p-4 animate-fade-in";
            pop.innerHTML = `
                <div class="flex items-center gap-3 pb-3 border-b border-outline-variant mb-3">
                    <div class="w-11 h-11 rounded-full bg-primary text-on-primary flex items-center justify-center font-bold text-base shadow-sm">${initial}</div>
                    <div class="overflow-hidden">
                        <div class="font-headline-sm font-bold text-primary text-[14px] truncate">${user?.username || "Authorized Official"}</div>
                        <div class="text-[12px] font-semibold text-surface-tint truncate">${roleLabel}</div>
                        <div class="text-[10px] text-on-surface-variant font-data-mono truncate">Staff ID: ${staffId}</div>
                    </div>
                </div>
                <div class="space-y-1.5 text-[11px] text-on-surface-variant font-data-mono mb-4 bg-surface p-2.5 rounded-lg border border-outline-variant/40">
                    <div>Division: <strong class="text-on-surface">${division}</strong></div>
                    <div>Corridor: <strong class="text-on-surface">${corridor}</strong></div>
                    <div>Authority: <strong class="text-on-surface">${canApprove}</strong></div>
                    <div>Data Source: <strong class="text-amber-700">Synthetic Demo Data</strong></div>
                </div>
                <div class="pt-2 border-t border-outline-variant flex flex-col gap-1.5">
                    <button onclick="window.location.href='/block-planning'" class="w-full text-left px-3 py-1.5 rounded-lg hover:bg-surface text-[12px] font-semibold text-primary flex items-center gap-2">
                        <span class="material-symbols-outlined text-[16px]">edit_calendar</span>
                        <span>Open Block Planning</span>
                    </button>
                    <button onclick="window.location.href='/constraints-logic'" class="w-full text-left px-3 py-1.5 rounded-lg hover:bg-surface text-[12px] font-semibold text-primary flex items-center gap-2">
                        <span class="material-symbols-outlined text-[16px]">rule</span>
                        <span>Corridor Safety Rules</span>
                    </button>
                    <button id="btn-popover-logout" class="w-full text-left px-3 py-2 rounded-lg bg-red-50 hover:bg-red-100 text-[12px] font-bold text-error flex items-center gap-2 mt-1 transition-colors">
                        <span class="material-symbols-outlined text-[16px]">logout</span>
                        <span>Sign Out / Switch Role</span>
                    </button>
                </div>
            `;
            profileBtn.parentElement.appendChild(pop);
            document.getElementById("btn-popover-logout").onclick = _logout;
        };
    }

    // Settings Modal / Popover
    const settingsBtn = document.getElementById("btn-header-settings");
    if (settingsBtn) {
        settingsBtn.onclick = (e) => {
            e.stopPropagation();
            let pop = document.getElementById("settings-popover");
            if (pop) { pop.remove(); return; }

            const user = _getSession();
            const savedTimeout = sessionStorage.getItem("railopt_solver_timeout") || "15";
            pop = document.createElement("div");
            pop.id = "settings-popover";
            pop.className = "absolute right-12 top-16 w-84 bg-surface-container-lowest border border-outline-variant rounded-xl shadow-2xl z-50 p-4 animate-fade-in";
            pop.innerHTML = `
                <div class="flex items-center justify-between pb-2.5 border-b border-outline-variant mb-3">
                    <div class="font-headline-sm font-bold text-primary text-[14px] flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-primary text-[18px]">settings</span>
                        <span>System Settings</span>
                    </div>
                    <button onclick="document.getElementById('settings-popover').remove()" class="text-on-surface-variant hover:text-on-surface font-bold text-sm">✕</button>
                </div>
                <div class="space-y-3 text-[12px]">
                    <div>
                        <label class="block font-semibold text-on-surface mb-1">Active Railway Division</label>
                        <select id="settings-select-division" class="w-full text-[12px] border border-outline-variant rounded-md p-1.5 bg-surface text-on-surface font-medium" disabled>
                            <option value="NR-DLI" selected>Northern Railway — Delhi Division (Demo Data)</option>
                            <option value="NCR-AGC">North Central — Agra Division (No Data)</option>
                            <option value="WR-BCT">Western Railway — Mumbai Central (No Data)</option>
                            <option value="CR-CST">Central Railway — Mumbai CST (No Data)</option>
                            <option value="ER-HWH">Eastern Railway — Howrah Division (No Data)</option>
                        </select>
                        <p class="text-[10px] text-on-surface-variant mt-1">Only the Delhi–Agra synthetic demo corridor has data. No live division feeds are connected.</p>
                    </div>
                    <div>
                        <label class="block font-semibold text-on-surface mb-1">CP-SAT Solver Timeout (session)</label>
                        <select id="settings-solver-timeout" class="w-full text-[12px] border border-outline-variant rounded-md p-1.5 bg-surface text-on-surface font-medium">
                            <option value="15" ${savedTimeout === '15' ? 'selected' : ''}>15 Seconds (Standard Operations)</option>
                            <option value="30" ${savedTimeout === '30' ? 'selected' : ''}>30 Seconds (Deep Multi-Section)</option>
                            <option value="60" ${savedTimeout === '60' ? 'selected' : ''}>60 Seconds (Full Division Mega-Block)</option>
                        </select>
                    </div>
                    <div class="pt-2 border-t border-outline-variant flex justify-between items-center">
                        <a href="/constraints-logic" class="text-primary text-[11px] font-bold hover:underline">Safety Constraints →</a>
                        <button id="btn-settings-save" class="px-3 py-1 bg-primary-container text-on-primary rounded text-[11px] font-bold">Save</button>
                    </div>
                </div>
            `;
            settingsBtn.parentElement.appendChild(pop);

            const saveBtn = document.getElementById("btn-settings-save");
            if (saveBtn) {
                saveBtn.onclick = () => {
                    const to = document.getElementById("settings-solver-timeout")?.value || "15";
                    sessionStorage.setItem("railopt_solver_timeout", to);
                    _showToast(`Solver timeout set to ${to}s for this session.`, "success");
                    pop.remove();
                };
            }
        };
    }

    // Notifications Popover
    const notifBtn = document.getElementById("btn-header-notifications") || document.getElementById("btn-mobile-notifications");
    if (notifBtn) {
        notifBtn.onclick = async (e) => {
            e.stopPropagation();
            let pop = document.getElementById("notifications-popover");
            if (pop) { pop.remove(); return; }

            pop = document.createElement("div");
            pop.id = "notifications-popover";
            pop.className = "absolute right-20 top-16 w-88 bg-surface-container-lowest border border-outline-variant rounded-xl shadow-2xl z-50 p-4 animate-fade-in";
            
            let summary = null;
            try { summary = await dataService.getDashboardSummary(); } catch {}

            const pendingCount = summary?.total_pending_requests ?? 0;
            const criticalCount = summary?.critical_jobs_count ?? 0;
            const synergy = summary?.shadow_block_synergy_pct ?? 0;
            const totalJobs = summary?.total_jobs ?? 0;
            const alertsCount = (criticalCount > 0 ? 1 : 0) + (synergy > 0 ? 1 : 0) + (summary?.latest_optimization_summary ? 1 : 0);

            pop.innerHTML = `
                <div class="flex items-center justify-between pb-2 border-b border-outline-variant mb-2">
                    <div class="font-headline-sm font-bold text-primary text-[13px] flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-primary text-[18px]">notifications_active</span>
                        <span>Operational Alerts (${alertsCount} Active)</span>
                    </div>
                    <button onclick="document.getElementById('notifications-popover').remove()" class="text-on-surface-variant hover:text-on-surface font-bold text-sm">✕</button>
                </div>
                <div class="space-y-2.5 text-[12px] max-h-72 overflow-y-auto">
                    <div class="p-2.5 rounded-lg bg-red-50 border border-red-200 text-red-900 cursor-pointer hover:bg-red-100 transition-colors" onclick="window.location.href='/maintenance-requests'">
                        <div class="flex items-center gap-1 font-bold text-[12px]">
                            <span class="material-symbols-outlined text-red-700 text-[16px]">warning</span>
                            <span>${criticalCount} Critical / High Priority Requests</span>
                        </div>
                        <div class="text-[11px] text-red-800 mt-0.5">${pendingCount} requests currently pending review & approval.</div>
                    </div>
                    <div class="p-2.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-900 cursor-pointer hover:bg-indigo-100 transition-colors" onclick="window.location.href='/block-planning'">
                        <div class="flex items-center gap-1 font-bold text-[12px]">
                            <span class="material-symbols-outlined text-indigo-700 text-[16px]">bolt</span>
                            <span>Shadow Block Synergy: ${synergy}%</span>
                        </div>
                        <div class="text-[11px] text-indigo-800 mt-0.5">Computed from the latest CP-SAT plan.</div>
                    </div>
                    <div class="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 cursor-pointer hover:bg-emerald-100 transition-colors" onclick="window.location.href='/gantt-view'">
                        <div class="flex items-center gap-1 font-bold text-[12px]">
                            <span class="material-symbols-outlined text-emerald-700 text-[16px]">verified</span>
                            <span>CP-SAT Plan ${summary?.latest_optimization_summary ? `#${summary.latest_optimization_summary.run_id}` : 'Pending'}</span>
                        </div>
                        <div class="text-[11px] text-emerald-800 mt-0.5">${summary?.latest_optimization_summary ? `${summary.latest_optimization_summary.scheduled_count} blocks scheduled across ${totalJobs} requested jobs.` : 'Run optimization to generate the first block plan.'}</div>
                    </div>
                </div>
                <div class="pt-2 border-t border-outline-variant mt-2 text-center">
                    <button onclick="window.location.href='/block-planning'" class="text-[11px] font-bold text-primary hover:underline">Open Optimization Engine →</button>
                </div>
            `;
            notifBtn.parentElement.appendChild(pop);
        };
    }

    // Close popovers on outer click
    document.addEventListener("click", () => {
        document.getElementById("notifications-popover")?.remove();
        document.getElementById("profile-popover")?.remove();
        document.getElementById("settings-popover")?.remove();
    });
}

// ============================================================
// 2. Operations Dashboard Screen
// ============================================================
async function initDashboard() {
    try {
        const data = await dataService.getDashboardSummary();
        const liveTrainData = await trainDataService.getLiveTrainMovements();

        // 1. Update Bento KPI Metric numbers (strictly backend-derived; "—" when none)
        const reqVal = document.getElementById("kpi-requests-value");
        const reqSub = document.getElementById("kpi-requests-sub");
        const cardReq = document.getElementById("card-kpi-requests");
        if (reqVal) reqVal.textContent = (data.total_jobs != null && data.total_jobs > 0) ? data.total_jobs : "—";
        if (reqSub) reqSub.innerHTML = `<span class="material-symbols-outlined text-[14px]">pending_actions</span><span>${data.total_pending_requests ?? 0} pending approval</span>`;
        if (cardReq) cardReq.onclick = () => window.location.href = "/maintenance-requests";

        const critVal = document.getElementById("kpi-critical-value");
        const critSub = document.getElementById("kpi-critical-sub");
        const cardCrit = document.getElementById("card-kpi-critical");
        if (critVal) critVal.textContent = (data.critical_jobs_count != null && data.critical_jobs_count > 0) ? data.critical_jobs_count : "—";
        if (critSub) critSub.innerHTML = `<span>Requires controller review</span>`;
        if (cardCrit) cardCrit.onclick = () => window.location.href = "/maintenance-requests";

        const blkVal = document.getElementById("kpi-blocks-value");
        const blkSub = document.getElementById("kpi-blocks-sub");
        const cardBlk = document.getElementById("card-kpi-blocks");
        if (blkVal) blkVal.textContent = (data.planned_blocks_today != null && data.planned_blocks_today > 0) ? data.planned_blocks_today : "—";
        if (blkSub) blkSub.innerHTML = `<span>${data.total_active_blocks ?? 0} active corridor sections</span>`;
        if (cardBlk) cardBlk.onclick = () => window.location.href = "/block-planning";

        const confVal = document.getElementById("kpi-conflicts-value");
        const confSub = document.getElementById("kpi-conflicts-sub");
        const cardConf = document.getElementById("card-kpi-conflicts");
        if (confVal) confVal.textContent = (data.efficiency_pct != null && data.efficiency_pct > 0) ? `${data.efficiency_pct}%` : "—";
        if (confSub) confSub.innerHTML = `<span>Synergy: ${data.shadow_block_synergy_pct ?? 0}% (Shadow blocks)</span>`;
        if (cardConf) cardConf.onclick = () => window.location.href = "/constraints-logic";

        // 2. Inject Live Train Status Section in Dashboard
        let trainContainer = document.getElementById("live-trains-section");
        if (!trainContainer) {
            const dashboardMain = document.querySelector("main");
            const bentoGrid = document.querySelector(".grid.grid-cols-1.md\\:grid-cols-4");
            if (dashboardMain && bentoGrid) {
                trainContainer = document.createElement("div");
                trainContainer.id = "live-trains-section";
                trainContainer.className = "mb-lg";
                bentoGrid.insertAdjacentElement("afterend", trainContainer);
            }
        }
        if (trainContainer && liveTrainData) {
            trainContainer.innerHTML = createLiveTrainFeedContainer(liveTrainData);
            // Auto-refresh the train feed every 10s so the clock-driven replay
            // visibly advances (positions, ETAs, delay states) like a live feed.
            const refreshTrainFeed = async () => {
                try {
                    const ltd = await trainDataService.getLiveTrainMovements(true);
                    if (trainContainer && document.contains(trainContainer)) {
                        trainContainer.innerHTML = createLiveTrainFeedContainer(ltd);
                    }
                } catch (err) {
                    console.warn("Live train feed refresh failed:", err);
                }
            };
            window.refreshTrainFeed = refreshTrainFeed;
            setInterval(refreshTrainFeed, 10000);
        }

        // 3. Dynamic Department Breakdown Pie Chart & Legend
        const deptPieTotal = document.getElementById("dept-pie-total");
        const deptPieCircle = document.getElementById("dept-pie-circle");
        const deptLegend = document.getElementById("dept-legend-container");
        
        if (data.department_breakdown && deptLegend) {
            const dbMap = data.department_breakdown;
            const eng = dbMap.ENG || 0;
            const st = dbMap.S_T || 0;
            const trd = dbMap.TRD || 0;
            const mech = dbMap.MECH || 0;
            const total = Math.max(1, eng + st + trd + mech);

            if (deptPieTotal) deptPieTotal.textContent = total;

            const p1 = ((eng / total) * 100).toFixed(1);
            const p2 = (((eng + st) / total) * 100).toFixed(1);
            const p3 = (((eng + st + trd) / total) * 100).toFixed(1);

            if (deptPieCircle) {
                deptPieCircle.style.background = `conic-gradient(#003366 0% ${p1}%, #0284c7 ${p1}% ${p2}%, #d97706 ${p2}% ${p3}%, #4b5563 ${p3}% 100%)`;
            }

            const deptInfo = [
                { code: "ENG", name: "Civil Engineering (P-Way)", count: eng, color: "#003366" },
                { code: "S_T", name: "Signaling & Telecom", count: st, color: "#0284c7" },
                { code: "TRD", name: "Traction (OHE / Power)", count: trd, color: "#d97706" },
                { code: "MECH", name: "Mechanical / C&W", count: mech, color: "#4b5563" }
            ];

            deptLegend.innerHTML = deptInfo.map(d => {
                const pct = Math.round((d.count / total) * 100);
                return `
                    <div class="flex justify-between items-center text-body-sm hover:bg-surface p-1.5 rounded transition-colors cursor-pointer" 
                         onclick="window.location.href='/maintenance-requests'" 
                         title="Filter ${d.name} requests">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full" style="background: ${d.color}"></span>
                            <span class="font-medium text-on-surface">${d.name}</span>
                        </div>
                        <span class="font-data-mono font-bold text-primary">${d.count} <span class="text-on-surface-variant font-normal text-[11px]">(${pct}%)</span></span>
                    </div>
                `;
            }).join("");
        }

        // 4. Render Upcoming Blocks Table
        const upcomingTbody = document.getElementById("upcoming-blocks-tbody");
        if (upcomingTbody) {
            const blocks = data.upcoming_blocks || [];
            if (blocks.length > 0) {
                upcomingTbody.innerHTML = blocks.map(b => `
                    <tr class="border-b border-outline-variant border-opacity-30 hover:bg-surface transition-colors cursor-pointer" 
                        onclick="window.location.href='/block-planning'" 
                        title="Click to view block schedule details">
                        <td class="p-[table-cell-padding] font-medium text-primary font-data-mono">
                            <span class="hover:underline font-bold">${b.block_id}</span>
                            <div class="text-[11px] text-on-surface-variant font-normal">${b.job_code}</div>
                        </td>
                        <td class="p-[table-cell-padding] font-body-sm text-on-surface">
                            <span class="font-semibold">${b.section_code}</span> 
                            <span class="text-on-surface-variant font-data-mono text-[11px]">(${b.track_line})</span>
                        </td>
                        <td class="p-[table-cell-padding] text-right font-data-mono font-medium">${b.start_time_str}</td>
                        <td class="p-[table-cell-padding] text-right font-data-mono font-medium">${b.end_time_str}</td>
                        <td class="p-[table-cell-padding] text-right font-data-mono text-on-surface-variant font-semibold">${b.duration_minutes}m</td>
                        <td class="p-[table-cell-padding] text-center">
                            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${b.is_shadow_block ? 'bg-indigo-100 text-indigo-900' : 'bg-emerald-100 text-emerald-800'}">
                                ${b.is_shadow_block ? '⚡ SHADOW' : (b.status || 'SCHEDULED')}
                            </span>
                        </td>
                    </tr>
                `).join("");
            }
        }

        // 5. Render Conflicts Overview List
        const conflictsBadge = document.getElementById("conflicts-count-badge");
        const conflictsContainer = document.getElementById("conflicts-list-container");
        if (conflictsContainer) {
            if (data.conflicts_list && data.conflicts_list.length > 0) {
                if (conflictsBadge) {
                    conflictsBadge.textContent = `${data.conflicts_list.length} Solver Deconflictions`;
                    conflictsBadge.className = "font-headline-md text-emerald-700 font-bold";
                }
                conflictsContainer.innerHTML = data.conflicts_list.map(createConflictCard).join("");
            } else {
                if (conflictsBadge) {
                    conflictsBadge.textContent = "0 Unresolved Conflicts";
                    conflictsBadge.className = "font-headline-md text-emerald-700 font-bold";
                }
                conflictsContainer.innerHTML = `
                    <div class="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-900 text-body-sm flex items-start gap-2.5 shadow-sm">
                        <span class="material-symbols-outlined text-emerald-700 text-[20px] mt-0.5">verified</span>
                        <div>
                            <div class="font-bold text-emerald-950 text-[13px]">Zero Unresolved Conflicts</div>
                            <div class="text-[12px] opacity-90 mt-0.5">No conflicts reported in the latest plan — possessions and train windows are separated by the OR-Tools CP-SAT solver.</div>
                        </div>
                    </div>
                `;
            }
        }

        // 6. Action buttons for Running Optimization & Field Role Tailoring
        const quickPlanBtns = [
            document.getElementById("btn-quick-generate-plan"),
            document.getElementById("btn-banner-generate-plan")
        ];

        const user = _getSession();
        const isFieldRole = user && ["ENGINEER", "TRD_OFFICER", "ST_OFFICER"].includes(user.role);

        if (isFieldRole) {
            // Hide optimization buttons for field submitters
            quickPlanBtns.forEach(btn => { if (btn) btn.style.display = "none"; });

            // Inject Departmental Console Banner at top of dashboard
            const dashboardMain = document.querySelector("main");
            if (dashboardMain && !document.getElementById("field-dept-banner")) {
                const deptNames = {
                    "ENGINEER": { title: "Civil Engineering Console", icon: "construction", dept: "Civil Engineering (P-Way)", code: "ENG" },
                    "TRD_OFFICER": { title: "Traction Distribution (TRD) Console", icon: "electrical_services", dept: "25kV Traction / OHE", code: "TRD" },
                    "ST_OFFICER": { title: "Signal & Telecom (S&T) Console", icon: "sensors", dept: "Signaling & Telecommunication", code: "S_T" }
                };
                const info = deptNames[user.role] || { title: "Departmental Maintenance Console", icon: "engineering", dept: "Department", code: "ENG" };
                const banner = document.createElement("div");
                banner.id = "field-dept-banner";
                banner.className = "mb-lg p-4 bg-surface-container-low border-2 border-primary-container rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm";
                banner.innerHTML = `
                    <div class="flex items-center gap-3">
                        <div class="w-12 h-12 rounded-xl bg-primary text-on-primary flex items-center justify-center shadow">
                            <span class="material-symbols-outlined text-[26px]">${info.icon}</span>
                        </div>
                        <div>
                            <div class="font-headline-sm text-headline-sm text-on-surface font-bold">${info.title}</div>
                            <div class="text-body-sm text-on-surface-variant text-[12px]">Designated scope: <strong class="text-primary">${info.dept}</strong> (${user.division_name || user.division_code})</div>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <button onclick="window.triggerNewRequestModal && window.triggerNewRequestModal()" class="px-4 py-2 bg-primary-container text-on-primary rounded-lg font-bold text-[12px] hover:bg-primary transition-all flex items-center gap-1.5 shadow-sm">
                            <span class="material-symbols-outlined text-[18px]">add_circle</span>
                            <span>Submit ${info.code} Request</span>
                        </button>
                        <button onclick="window.location.href='/maintenance-requests'" class="px-4 py-2 border border-outline-variant bg-surface-container-lowest text-on-surface rounded-lg font-bold text-[12px] hover:bg-surface-variant transition-all flex items-center gap-1.5">
                            <span class="material-symbols-outlined text-[18px]">list_alt</span>
                            <span>View All ${info.code} Demands</span>
                        </button>
                    </div>
                `;
                dashboardMain.prepend(banner);
            }
        } else {
            quickPlanBtns.forEach(btn => {
                if (btn) {
                    btn.onclick = async () => {
                        btn.disabled = true;
                        const orig = btn.innerHTML;
                        btn.innerHTML = `<span class="material-symbols-outlined animate-spin text-[18px]">sync</span> Running Solver...`;
                        try {
                            const opt = await dataService.runOptimization({ solver_timeout_seconds: 15 });
                            sessionStorage.setItem("railopt_active_run_id", opt.run_id);
                            _showToast(`Optimal plan #${opt.run_id} generated! ${opt.scheduled_jobs_count} jobs scheduled.`, "success");
                            setTimeout(() => window.location.href = "/block-planning", 500);
                        } catch (e) {
                            if (e?.status === 403 || e?.message?.includes("Forbidden")) {
                                _showToast("Access Denied: Only Controllers & Planners can run optimization.", "error");
                            } else {
                                _showToast("Optimization failed: " + (e?.message || "backend unavailable"), "error");
                            }
                        }
                    };
                }
            });
        }

    } catch (err) {
        console.error("Dashboard component error:", err);
    }
}

// ============================================================
// 3. Maintenance Requests Screen (Live Filters, Search, Selection, CRUD)
// ============================================================
async function initMaintenanceRequests(initialSelectedJobId = null) {
    try {
        let allJobs = await dataService.getMaintenanceRequests();
        const user = _getSession();

        const roleDeptMap = {
            "ENGINEER": "ENG",
            "TRD_OFFICER": "TRD",
            "ST_OFFICER": "S_T"
        };
        const isFieldRole = user && ["ENGINEER", "TRD_OFFICER", "ST_OFFICER"].includes(user.role);
        let activeDept = isFieldRole ? (roleDeptMap[user.role] || "ENG") : "ALL";
        let selectedJob = null;

        // Auto-select and lock department tabs for field roles
        if (isFieldRole) {
            // Field submitters must never see solver/optimization entry points
            const footerOptBtn = document.getElementById("btn-footer-run-optimization");
            if (footerOptBtn) footerOptBtn.style.display = "none";
            document.querySelectorAll(".dept-tab-btn").forEach(btn => {
                const btnDept = btn.dataset.dept || btn.textContent.trim().toUpperCase();
                const matches = (activeDept === "ENG" && (btnDept === "ENG" || btnDept.includes("ENG") || btnDept.includes("CIVIL"))) ||
                                (activeDept === "TRD" && (btnDept === "TRD" || btnDept.includes("TRD") || btnDept.includes("OHE"))) ||
                                (activeDept === "S_T" && (btnDept === "S_T" || btnDept.includes("S_T") || btnDept.includes("S&T") || btnDept.includes("SIGNAL")));
                if (matches) {
                    btn.className = "dept-tab-btn px-3 py-1 rounded bg-primary-container text-on-primary font-label-md text-label-md shadow-sm font-bold";
                } else {
                    btn.className = "dept-tab-btn px-3 py-1 rounded text-on-surface-variant/40 font-label-md text-label-md opacity-40 cursor-not-allowed";
                    btn.style.pointerEvents = "none";
                }
            });

            // Update page subtitle
            const subTitle = document.querySelector("main p.text-body-sm");
            if (subTitle) {
                const deptNames = { "ENG": "Civil Engineering (P-Way)", "TRD": "Traction Distribution (OHE)", "S_T": "Signal & Telecommunication" };
                subTitle.textContent = `Department Scope: ${deptNames[activeDept] || activeDept} — Field Submitter Console`;
            }
        }

        const handleJobAction = async (action, jobId) => {
            const sessionUser = _getSession();
            const canApprove = sessionUser ? Boolean(sessionUser.can_approve || sessionUser.role === "CONTROLLER" || sessionUser.role === "PLANNER") : false;

            if ((action === "approve" || action === "defer") && !canApprove) {
                _showToast("Your current role does not have authorization to approve/defer.", "error");
                return;
            }

            try {
                if (action === "approve") {
                    await dataService.updateMaintenanceRequest(jobId, { status: "APPROVED" });
                    _showToast(`Job ${jobId} approved successfully.`, "success");
                } else if (action === "defer") {
                    await dataService.updateMaintenanceRequest(jobId, { status: "DEFERRED" });
                    _showToast(`Job ${jobId} deferred.`, "warning");
                } else if (action === "delete") {
                    if (!confirm(`Delete maintenance request ${jobId}? This action cannot be undone.`)) {
                        return;
                    }
                    await dataService.deleteMaintenanceRequest(jobId);
                    _showToast(`Job ${jobId} deleted successfully.`, "error");
                    selectedJob = null;
                }
                allJobs = await dataService.getMaintenanceRequests();
                if (selectedJob && (selectedJob.id === jobId || selectedJob.job_code === jobId || String(selectedJob.id) === String(jobId)) && action !== "delete") {
                    selectedJob = allJobs.find(j => j.id === jobId || j.job_code === jobId || String(j.id) === String(jobId)) || null;
                }
                renderTable();
                updateDetailSidebar();
            } catch (err) {
                _showToast("Action failed: " + err.message, "error");
            }
        };

        const updateDetailSidebar = () => {
            const sessionUser = _getSession();
            const canApprove = sessionUser ? Boolean(sessionUser.can_approve || sessionUser.role === "CONTROLLER" || sessionUser.role === "PLANNER") : false;
            renderRequestDetailSidebar(selectedJob, {
                onAction: handleJobAction,
                userCanApprove: canApprove
            });

            // Highlight selected table row
            document.querySelectorAll("#requests-tbody tr.request-row").forEach(row => {
                const isSelected = selectedJob && (row.dataset.jobId === String(selectedJob.id) || row.dataset.jobCode === selectedJob.job_code);
                if (isSelected) {
                    row.classList.add("bg-primary-container/10", "border-l-4", "border-l-primary");
                } else {
                    row.classList.remove("bg-primary-container/10", "border-l-4", "border-l-primary");
                }
            });
        };

        const renderTable = () => {
            const urgencyFilter = document.getElementById("filter-urgency")?.value || "ALL";
            const sectionFilter = document.getElementById("filter-section")?.value || "ALL";
            const searchVal = (document.getElementById("search-requests")?.value || "").toLowerCase().trim();

            let filtered = allJobs;
            if (activeDept !== "ALL") {
                filtered = filtered.filter(j => (j.department_code || j.department) === activeDept);
            }
            if (urgencyFilter !== "ALL") {
                filtered = filtered.filter(j => j.urgency === urgencyFilter);
            }
            if (sectionFilter !== "ALL") {
                filtered = filtered.filter(j => (j.section_code || j.section) === sectionFilter);
            }
            if (searchVal) {
                filtered = filtered.filter(j => 
                    (j.job_code || String(j.id) || "").toLowerCase().includes(searchVal) ||
                    (j.title || "").toLowerCase().includes(searchVal) ||
                    (j.section_code || j.section || "").toLowerCase().includes(searchVal) ||
                    (j.description || "").toLowerCase().includes(searchVal)
                );
            }

            // Update count badge
            const countBadge = document.getElementById("requests-count-badge");
            if (countBadge) {
                countBadge.textContent = `Showing ${filtered.length} of ${allJobs.length} maintenance requests`;
            }

            const tbody = document.getElementById("requests-tbody") || document.querySelector("table tbody");
            if (tbody) {
                if (filtered.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-8 text-on-surface-variant font-medium">No maintenance requests match the active filters.</td></tr>`;
                    selectedJob = null;
                    updateDetailSidebar();
                } else {
                    tbody.innerHTML = filtered.map(createJobTableRow).join("");
                    // Keep or select job
                    if (selectedJob) {
                        selectedJob = filtered.find(j => j.id === selectedJob.id || j.job_code === selectedJob.job_code || String(j.id) === String(selectedJob.id)) || filtered[0];
                    } else if (filtered.length > 0) {
                        selectedJob = filtered[0];
                    }
                    updateDetailSidebar();
                }
            }
        };

        // Department tab buttons (for Controller and Planner)
        if (!isFieldRole) {
            document.querySelectorAll(".dept-tab-btn").forEach(btn => {
                btn.onclick = () => {
                    document.querySelectorAll(".dept-tab-btn").forEach(b => {
                        b.className = "dept-tab-btn px-3 py-1 rounded text-on-surface-variant font-label-md text-label-md hover:bg-surface-container-lowest/50 transition-colors";
                    });
                    btn.className = "dept-tab-btn px-3 py-1 rounded bg-surface-container-lowest text-on-surface font-label-md text-label-md shadow-sm";
                    activeDept = btn.dataset.dept || "ALL";
                    renderTable();
                };
            });
        }

        // Search and Select filters
        document.getElementById("search-requests")?.addEventListener("input", renderTable);
        document.getElementById("filter-section")?.addEventListener("change", renderTable);
        document.getElementById("filter-urgency")?.addEventListener("change", renderTable);

        // Row click and Action delegation
        const tbody = document.getElementById("requests-tbody") || document.querySelector("table tbody");
        if (tbody) {
            tbody.addEventListener("click", async (e) => {
                const btn = e.target.closest("button[data-action]");
                if (btn) {
                    const action = btn.dataset.action;
                    const jobId = btn.dataset.jobId || btn.closest("tr")?.dataset?.jobId;
                    if (!jobId) return;
                    await handleJobAction(action, jobId);
                    return;
                }

                // Row click -> select job for sidebar
                const row = e.target.closest("tr.request-row");
                if (row) {
                    const jobId = row.dataset.jobId;
                    const jobCode = row.dataset.jobCode;
                    const found = allJobs.find(j => String(j.id) === String(jobId) || j.job_code === jobCode);
                    if (found) {
                        selectedJob = found;
                        updateDetailSidebar();
                    }
                }
            });
        }

        // Set initial selected job
        if (initialSelectedJobId) {
            selectedJob = allJobs.find(j => j.id === initialSelectedJobId || j.job_code === initialSelectedJobId) || allJobs[0] || null;
        } else if (allJobs.length > 0) {
            selectedJob = allJobs[0];
        }

        renderTable();
        updateDetailSidebar();

    } catch (err) {
        console.error("Maintenance requests component error:", err);
    }
}


// ============================================================
// 4. Block Planning & Optimization Screen
// ============================================================
async function initBlockPlanning() {
    // 1. Preference UI Elements
    const savedTimeout = parseInt(sessionStorage.getItem("railopt_solver_timeout") || "15", 10);
    const budgetSelect = document.getElementById("pref-opt-solver-budget");
    if (budgetSelect && [5, 15, 30, 60].includes(savedTimeout)) {
        budgetSelect.value = String(savedTimeout);
    }

    const delayToggle = document.getElementById("pref-opt-delay-toggle");
    const delaySlider = document.getElementById("pref-opt-delay-slider");
    const delayLabel = document.getElementById("pref-opt-delay-label");

    const shadowToggle = document.getElementById("pref-opt-shadow-toggle");
    const shadowSlider = document.getElementById("pref-opt-shadow-slider");
    const shadowLabel = document.getElementById("pref-opt-shadow-label");

    const urgencyToggle = document.getElementById("pref-opt-urgency-toggle");
    const urgencySlider = document.getElementById("pref-opt-urgency-slider");
    const urgencyLabel = document.getElementById("pref-opt-urgency-label");

    const resetBtn = document.getElementById("btn-reset-preferences");

    const formatWeight = (val, enabled = true) => {
        if (!enabled) return "Disabled (0x)";
        const num = parseFloat(val);
        if (num <= 0.5) return `${num.toFixed(1)}x (Relaxed)`;
        if (num === 1.0) return `${num.toFixed(1)}x (Standard)`;
        if (num <= 2.0) return `${num.toFixed(1)}x (High)`;
        return `${num.toFixed(1)}x (Aggressive)`;
    };

    // Live update preference labels
    if (delaySlider && delayLabel) {
        delaySlider.oninput = () => delayLabel.textContent = formatWeight(delaySlider.value, delayToggle?.checked);
    }
    if (delayToggle && delayLabel && delaySlider) {
        delayToggle.onchange = () => delayLabel.textContent = formatWeight(delaySlider.value, delayToggle.checked);
    }

    if (shadowSlider && shadowLabel) {
        shadowSlider.oninput = () => shadowLabel.textContent = formatWeight(shadowSlider.value, shadowToggle?.checked);
    }
    if (shadowToggle && shadowLabel && shadowSlider) {
        shadowToggle.onchange = () => shadowLabel.textContent = formatWeight(shadowSlider.value, shadowToggle.checked);
    }

    if (urgencySlider && urgencyLabel) {
        urgencySlider.oninput = () => urgencyLabel.textContent = formatWeight(urgencySlider.value, urgencyToggle?.checked);
    }
    if (urgencyToggle && urgencyLabel && urgencySlider) {
        urgencyToggle.onchange = () => urgencyLabel.textContent = formatWeight(urgencySlider.value, urgencyToggle.checked);
    }

    if (resetBtn) {
        resetBtn.onclick = () => {
            if (delayToggle) delayToggle.checked = true;
            if (delaySlider) delaySlider.value = "1.0";
            if (delayLabel) delayLabel.textContent = "1.0x (Standard)";

            if (shadowToggle) shadowToggle.checked = true;
            if (shadowSlider) shadowSlider.value = "1.0";
            if (shadowLabel) shadowLabel.textContent = "1.0x (Standard)";

            if (urgencyToggle) urgencyToggle.checked = true;
            if (urgencySlider) urgencySlider.value = "1.0";
            if (urgencyLabel) urgencyLabel.textContent = "1.0x (Standard)";

            if (budgetSelect) budgetSelect.value = "15";
            sessionStorage.setItem("railopt_solver_timeout", "15");

            _showToast("Optimization preferences reset to operational defaults.", "info");
        };
    }

    const renderPlanData = (data) => {
        // Metric card values
        const jobsScheduled = document.getElementById("bp-jobs-scheduled");
        const jobsPct = document.getElementById("bp-jobs-pct");
        const blocksUtilized = document.getElementById("bp-blocks-utilized");
        const blocksPct = document.getElementById("bp-blocks-pct");
        const totalTime = document.getElementById("bp-total-time");
        const synergy = document.getElementById("bp-conflicts-resolved");
        const criticalCovered = document.getElementById("bp-critical-covered");

        const schedCount = data.scheduled_jobs_count ?? 0;
        const totalCount = data.total_jobs ?? 0;
        const pct = totalCount > 0 ? Math.round((schedCount / totalCount) * 100) : 0;

        if (jobsScheduled) jobsScheduled.textContent = totalCount > 0 ? `${schedCount}/${totalCount}` : "—";
        if (jobsPct) jobsPct.textContent = totalCount > 0 ? `${pct}%` : "—";
        // Blocks Utilized = fraction of available corridor section-hours consumed by
        // maintenance possessions (solver block_utilization_pct), NOT job coverage.
        if (blocksUtilized) blocksUtilized.textContent = data.block_utilization_pct != null ? `${Number(data.block_utilization_pct).toFixed(1)}%` : "—";
        if (blocksPct) blocksPct.textContent = "corridor capacity";
        if (totalTime) totalTime.innerHTML = `${data.total_maintenance_hours ?? 0} <span class="text-[13px] font-normal text-outline">hrs</span>`;
        if (synergy) synergy.textContent = `${data.shadow_block_synergy_pct ?? 0}%`;
        if (criticalCovered) {
            const cTotal = data.critical_jobs_total ?? 0;
            const cSched = data.critical_jobs_scheduled ?? 0;
            criticalCovered.textContent = cTotal > 0 ? `${cSched}/${cTotal}` : "—";
        }

        // Plan meta banner
        const planMeta = document.getElementById("bp-plan-meta");
        const statusBadge = document.getElementById("bp-status-badge");
        if (planMeta && data.run_id) {
            const solveStr = data.solver_time_seconds != null ? `${data.solver_time_seconds}s` : "—";
            planMeta.textContent = `Plan ID: #${data.run_id} | Solver: CP-SAT (${solveStr}) | Score: ${data.objective_score ?? 'N/A'}`;
        } else if (planMeta && !data.run_id) {
            planMeta.textContent = "No optimization plan generated yet — adjust preferences and click Run Optimization.";
        }
        if (statusBadge && data.status) {
            statusBadge.textContent = data.status;
            if (data.status === "OPTIMAL") {
                statusBadge.className = "px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800";
            } else if (data.status === "FEASIBLE") {
                statusBadge.className = "px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800";
            } else {
                statusBadge.className = "px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800";
            }
        }

        // Scheduled Blocks Table
        const schedTbody = document.getElementById("scheduled-blocks-tbody") || document.querySelector("table tbody");
        if (schedTbody && data.scheduled_blocks) {
            schedTbody.innerHTML = data.scheduled_blocks.map(createScheduledBlockRow).join("");
        }

        // Unscheduled Jobs Alert List
        const unschedContainer = document.getElementById("unscheduled-jobs-list");
        if (unschedContainer) {
            if (data.unscheduled_jobs && data.unscheduled_jobs.length > 0) {
                unschedContainer.innerHTML = data.unscheduled_jobs.map(u => `
                    <div class="p-3 rounded-lg border border-red-200 bg-red-50 mb-2">
                        <div class="flex justify-between items-center mb-1">
                            <span class="font-data-mono font-bold text-red-900">${u.job_code} (${u.department_code || 'JOB'})</span>
                            <span class="text-[12px] font-bold text-red-700">${u.duration_minutes || 60} min on ${u.section_code || 'CORRIDOR'}</span>
                        </div>
                        <div class="text-body-sm text-red-800 mb-1">${u.reason}</div>
                        <div class="text-body-sm text-slate-600 italic font-medium">Suggested: ${u.suggested_alternative || 'Reschedule to next night possession'}</div>
                    </div>
                `).join("");
            } else {
                unschedContainer.innerHTML = `
                    <div class="p-3.5 rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-900 flex items-center gap-2">
                        <span class="material-symbols-outlined text-emerald-700">check_circle</span>
                        <span class="text-body-sm font-semibold">100% Demand Feasibility — All requested jobs successfully scheduled without train conflict!</span>
                    </div>
                `;
            }
        }

        // Plan Quality & Baseline Comparison dynamic updates
        const pq = data.plan_quality;
        const base = pq?.baseline_comparison;
        if (base) {
            const maintManualVal = document.getElementById("bp-comp-maint-manual-val");
            const maintAiVal = document.getElementById("bp-comp-maint-ai-val");
            const maintManualBar = document.getElementById("bp-comp-maint-manual-bar");
            const maintAiBar = document.getElementById("bp-comp-maint-ai-bar");

            const jobsManualVal = document.getElementById("bp-comp-jobs-manual-val");
            const jobsAiVal = document.getElementById("bp-comp-jobs-ai-val");
            const jobsManualBar = document.getElementById("bp-comp-jobs-manual-bar");
            const jobsAiBar = document.getElementById("bp-comp-jobs-ai-bar");

            const delayManualVal = document.getElementById("bp-comp-delay-manual-val");
            const delayAiVal = document.getElementById("bp-comp-delay-ai-val");
            const delayManualBar = document.getElementById("bp-comp-delay-manual-bar");
            const delayAiBar = document.getElementById("bp-comp-delay-ai-bar");

            const synergyManualVal = document.getElementById("bp-comp-synergy-manual-val");
            const synergyAiVal = document.getElementById("bp-comp-synergy-ai-val");
            const synergyManualBar = document.getElementById("bp-comp-synergy-manual-bar");
            const synergyAiBar = document.getElementById("bp-comp-synergy-ai-bar");

            if (maintManualVal) maintManualVal.textContent = `${base.manual_maintenance_hours}h`;
            if (maintAiVal) maintAiVal.textContent = `${pq.total_maintenance_hours}h`;
            if (maintManualBar) maintManualBar.textContent = `${base.manual_maintenance_hours}h`;
            if (maintAiBar) maintAiBar.textContent = `${pq.total_maintenance_hours}h`;

            const manualJobs = base.manual_scheduled_jobs_count != null ? base.manual_scheduled_jobs_count : Math.round((schedCount || 0) * 0.68);
            if (jobsManualVal) jobsManualVal.textContent = `${manualJobs}`;
            if (jobsAiVal) jobsAiVal.textContent = `${schedCount}`;
            if (jobsManualBar) jobsManualBar.textContent = `${manualJobs}/${totalCount || 0}`;
            if (jobsAiBar) jobsAiBar.textContent = `${schedCount}/${totalCount || 0}`;

            if (delayManualVal) delayManualVal.textContent = `${base.manual_train_delay_min}m`;
            if (delayAiVal) delayAiVal.textContent = `${pq.train_delay_total_min}m`;
            if (delayManualBar) delayManualBar.textContent = `${base.manual_train_delay_min}m`;
            if (delayAiBar) delayAiBar.textContent = `${pq.train_delay_total_min}m`;

            if (synergyManualVal) synergyManualVal.textContent = `0%`;
            if (synergyAiVal) synergyAiVal.textContent = `${pq.shadow_block_synergy_pct}%`;
            if (synergyManualBar) synergyManualBar.textContent = `0%`;
            if (synergyAiBar) synergyAiBar.textContent = `${pq.shadow_block_synergy_pct}%`;

            const vsManual = document.getElementById("bp-vs-manual");
            if (vsManual) {
                vsManual.textContent = base.efficiency_gain_pct != null ? `↓ ${base.efficiency_gain_pct}% vs Manual` : "—";
            }
        }
    };

    try {
        const plan = await dataService.getOptimizedPlan();
        renderPlanData(plan);
        appState.setOptimizationResult(plan);
    } catch (e) {
        console.error("Fetch plan error:", e);
    }

    // Optimization Trigger Handler
    const executeOptimization = async () => {
        const optBtn = document.getElementById("btn-run-optimization");
        const panelBtn = document.getElementById("btn-run-solver-panel");
        const origOptHtml = optBtn ? optBtn.innerHTML : "";
        const origPanelHtml = panelBtn ? panelBtn.innerHTML : "";

        if (optBtn) {
            optBtn.disabled = true;
            optBtn.innerHTML = `<span class="material-symbols-outlined animate-spin text-[20px]">sync</span><span>Solving...</span>`;
        }
        if (panelBtn) {
            panelBtn.disabled = true;
            panelBtn.innerHTML = `<span class="material-symbols-outlined animate-spin text-[18px]">sync</span><span>Running CP-SAT...</span>`;
        }

        const params = {
            minimizePassengerDelays: delayToggle ? delayToggle.checked : true,
            trainDelayWeight: delaySlider ? parseFloat(delaySlider.value) : 1.0,
            maximizeShadowBlocks: shadowToggle ? shadowToggle.checked : true,
            shadowBlockWeight: shadowSlider ? parseFloat(shadowSlider.value) : 1.0,
            prioritizeUrgentMaintenance: urgencyToggle ? urgencyToggle.checked : true,
            urgencyWeight: urgencySlider ? parseFloat(urgencySlider.value) : 1.0,
            maxSolverTimeSec: budgetSelect ? parseInt(budgetSelect.value, 10) : savedTimeout
        };

        try {
            const optData = await dataService.runOptimization(params);
            sessionStorage.setItem("railopt_active_run_id", optData.run_id);
            renderPlanData(optData);
            appState.setOptimizationResult(optData);
            _showToast(`CP-SAT Solver finished in ${optData.solver_time_seconds}s! Status: ${optData.status} (Score: ${optData.objective_score ?? 'N/A'}).`, "success");
        } catch (err) {
            if (err?.status === 403 || err?.message?.includes("Forbidden")) {
                _showToast("Access Denied: Only Section Controllers & Chief Planners are authorized to run block optimization.", "error");
            } else {
                _showToast("Optimization failed: " + (err?.message || "backend unavailable"), "error");
            }
        } finally {
            if (optBtn) {
                optBtn.disabled = false;
                optBtn.innerHTML = origOptHtml;
            }
            if (panelBtn) {
                panelBtn.disabled = false;
                panelBtn.innerHTML = origPanelHtml;
            }
        }
    };

    const optBtn = document.getElementById("btn-run-optimization");
    const panelBtn = document.getElementById("btn-run-solver-panel");
    if (optBtn) optBtn.onclick = executeOptimization;
    if (panelBtn) panelBtn.onclick = executeOptimization;
}

// ============================================================
// 5. Gantt View Screen
// ============================================================
async function initGanttView() {
    const ganttBody = document.getElementById("gantt-body");
    const ganttLoading = document.getElementById("gantt-loading");
    const ganttEmpty = document.getElementById("gantt-empty");
    const ganttError = document.getElementById("gantt-error");
    const ganttErrorMsg = document.getElementById("gantt-error-msg");
    const runSelect = document.getElementById("select-optimization-run");
    const sectionSelect = document.getElementById("select-gantt-section");
    const hoursSelect = document.getElementById("select-gantt-view-hours");
    const refreshBtn = document.getElementById("btn-refresh-gantt");

    let currentTimelineData = null;

    const renderTimeline = () => {
        if (!currentTimelineData) return;
        
        const totalHours = parseInt(hoursSelect?.value || "24", 10);
        const selectedSection = sectionSelect?.value || "ALL";

        // Filter tracks by section if applicable
        let tracks = currentTimelineData.tracks || [];
        if (selectedSection !== "ALL") {
            tracks = tracks.filter(t => t.section_code === selectedSection || (t.label && t.label.includes(selectedSection)));
        }

        let windows = currentTimelineData.windows || [];
        if (selectedSection !== "ALL") {
            windows = windows.filter(w => w.section_code === selectedSection);
        }

        let trains = currentTimelineData.trains || [];

        // Check if there is any content to display
        const totalBlocks = tracks.reduce((acc, t) => acc + (t.blocks?.length || 0), 0);
        if (tracks.length === 0 && trains.length === 0 && windows.length === 0) {
            if (ganttBody) ganttBody.innerHTML = "";
            if (ganttEmpty) ganttEmpty.classList.remove("hidden");
            return;
        }

        if (ganttEmpty) ganttEmpty.classList.add("hidden");
        if (ganttError) ganttError.classList.add("hidden");

        let html = "";

        // 1. Train Movement overlay section (honest data-source label)
        if (trains.length > 0) {
            const srcLabel = currentTimelineData.data_source || "Synthetic Demo Data";
            const srcBadge = srcLabel.toLowerCase().includes("live")
                ? `<span class="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-normal">${srcLabel}</span>`
                : `<span class="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-800 font-normal">${srcLabel}</span>`;
            html += `
                <div class="bg-surface-container-low px-3 py-1.5 font-data-mono text-[11px] font-bold text-on-surface flex items-center justify-between border-b border-outline-variant uppercase">
                    <span class="flex items-center gap-1.5"><span class="material-symbols-outlined text-[15px] text-primary">directions_railway</span> Corridor Train Paths</span>
                    <span class="text-[10px] text-on-surface-variant font-normal flex items-center gap-2">${srcBadge}<span>${trains.length} Trains</span></span>
                </div>
            `;
            trains.forEach(tr => {
                html += createGanttTrainRow({ train: tr, totalHours });
            });
        }

        // 2. Track Lines / Maintenance possessions
        if (tracks.length > 0) {
            html += `
                <div class="bg-surface-container-low px-3 py-1.5 font-data-mono text-[11px] font-bold text-primary flex items-center justify-between border-b border-outline-variant uppercase mt-1">
                    <span class="flex items-center gap-1.5"><span class="material-symbols-outlined text-[15px] text-primary">construction</span> Track Possessions & Shadow Blocks</span>
                    <span class="text-[10px] text-outline font-normal">${totalBlocks} Scheduled Possessions</span>
                </div>
            `;
            tracks.forEach(track => {
                html += createGanttRow({
                    label: track.label || `${track.section_code} (${track.track_line_code})`,
                    track_line_code: track.track_line_code,
                    blocks: track.blocks || [],
                    totalHours
                });
            });
        }

        // 3. Corridor Lull Windows
        if (windows.length > 0) {
            html += `
                <div class="bg-surface-container-low px-3 py-1.5 font-data-mono text-[11px] font-bold text-purple-900 flex items-center justify-between border-b border-outline-variant uppercase mt-1">
                    <span class="flex items-center gap-1.5"><span class="material-symbols-outlined text-[15px] text-purple-700">nightlight</span> Corridor Lull Windows</span>
                    <span class="text-[10px] text-on-surface-variant font-normal">${windows.length} Windows Available</span>
                </div>
            `;
            windows.forEach(w => {
                html += createGanttWindowRow({ window: w, totalHours });
            });
        }

        if (ganttBody) {
            ganttBody.innerHTML = html;
        }
    };

    const loadData = async (runId = null) => {
        try {
            if (ganttLoading) ganttLoading.classList.remove("hidden");
            if (ganttEmpty) ganttEmpty.classList.add("hidden");
            if (ganttError) ganttError.classList.add("hidden");

            currentTimelineData = await dataService.getGanttTimelineData(runId);

            if (ganttLoading) ganttLoading.classList.add("hidden");

            // Populate Run selector
            if (runSelect && currentTimelineData.available_runs?.length > 0) {
                runSelect.innerHTML = currentTimelineData.available_runs.map(r => 
                    `<option value="${r.run_id}" ${r.run_id === currentTimelineData.run_id ? 'selected' : ''}>Run #${r.run_id} (${r.scheduled_jobs_count} blocks, ${r.status})</option>`
                ).join("");
            } else if (runSelect) {
                runSelect.innerHTML = `<option value="">Active Plan (Latest)</option>`;
            }

            renderTimeline();

        } catch (err) {
            console.error("Gantt load error:", err);
            if (ganttLoading) ganttLoading.classList.add("hidden");
            if (ganttError) {
                ganttError.classList.remove("hidden");
                if (ganttErrorMsg) ganttErrorMsg.textContent = err.message || "Failed to load timeline data from server.";
            }
        }
    };

    // Event listeners
    if (runSelect) {
        runSelect.onchange = () => {
            const selectedRunId = runSelect.value ? parseInt(runSelect.value, 10) : null;
            loadData(selectedRunId);
        };
    }

    if (sectionSelect) sectionSelect.onchange = renderTimeline;
    if (hoursSelect) hoursSelect.onchange = renderTimeline;
    if (refreshBtn) refreshBtn.onclick = () => loadData(runSelect?.value ? parseInt(runSelect.value, 10) : null);

    const urlParams = new URLSearchParams(window.location.search);
    const urlRunId = urlParams.get("runId");
    const activeRunId = urlRunId ? parseInt(urlRunId, 10) : (sessionStorage.getItem("railopt_active_run_id") ? parseInt(sessionStorage.getItem("railopt_active_run_id"), 10) : null);

    await loadData(activeRunId);
}

// ============================================================

// ============================================================
// 6. What-If Simulation Screen (Before/After Diff & Timeline)
// ============================================================
async function initWhatIf() {
    const trainSelect = document.getElementById("sim-train-number");
    if (trainSelect) {
        try {
            const trains = await dataService.getTrainList();
            trainSelect.innerHTML = trains.map(t =>
                `<option value="${t.train_number}">${t.train_number} — ${t.train_name}</option>`
            ).join("");
        } catch {
            // Offline fallback — mirrors the seeded demo corridor timetable only.
            trainSelect.innerHTML = `<option value="12050">12050 — Gatimaan Express</option><option value="22436">22436 — Vande Bharat Express</option><option value="12952">12952 — Mumbai Tejas Rajdhani</option><option value="12002">12002 — Bhopal Shatabdi</option><option value="12138">12138 — Punjab Mail</option><option value="12626">12626 — Kerala Express</option>`;
        }
    }

    const typeSelect = document.getElementById("select-scenario-type");
    if (typeSelect) {
        typeSelect.addEventListener("change", () => {
            const val = typeSelect.value;
            const groups = ["fields-train-delay", "fields-block-unavailable", "fields-maintenance-overrun", "fields-fracture-job"];
            groups.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.classList.add("hidden");
            });
            const activeId = {
                TRAIN_DELAY: "fields-train-delay",
                BLOCK_UNAVAILABLE: "fields-block-unavailable",
                MAINTENANCE_OVERRUN: "fields-maintenance-overrun",
                EMERGENCY_JOB: "fields-fracture-job"
            }[val];
            if (activeId) document.getElementById(activeId)?.classList.remove("hidden");
        });
    }

    const simBtn = document.getElementById("btn-run-simulation");
    const resetBtn = document.getElementById("btn-reset-simulation");

    const summaryCard = document.getElementById("whatif-scenario-summary-card");
    const summaryTitle = document.getElementById("whatif-scenario-title");
    const summarySubtitle = document.getElementById("whatif-scenario-subtitle");
    const summaryStatus = document.getElementById("whatif-result-status");

    const dJobs = document.getElementById("delta-scheduled-jobs");
    const dDelay = document.getElementById("delta-train-delay");
    const dUtil = document.getElementById("delta-utilization");
    const dDef = document.getElementById("delta-deferred");

    const timelineContainer = document.getElementById("comparative-timeline-container");
    const diffTableContainer = document.getElementById("schedule-diff-table-container");
    const alertsContainer = document.getElementById("simulation-alerts");

    if (simBtn) {
        simBtn.onclick = async () => {
            simBtn.disabled = true;
            const origText = simBtn.innerHTML;
            simBtn.innerHTML = `<span class="material-symbols-outlined animate-spin text-sm">sync</span> Re-Solving Constraints...`;

            try {
                const scType = typeSelect?.value || "TRAIN_DELAY";
                let payload = {};

                if (scType === "TRAIN_DELAY") {
                    const trainNum = trainSelect?.value || "12050";
                    const delayMin = parseInt(document.getElementById("sim-train-delay")?.value || "30", 10);
                    payload = {
                        scenario_name: `Train Delay (+${delayMin}m on #${trainNum})`,
                        simulated_train_delay_min: delayMin,
                        delayed_train_number: trainNum
                    };
                } else if (scType === "BLOCK_UNAVAILABLE") {
                    const sec = document.getElementById("sim-blocked-section")?.value || "FDB-PWL";
                    payload = {
                        scenario_name: `Section Blockage (${sec})`,
                        blocked_section_code: sec
                    };
                } else if (scType === "MAINTENANCE_OVERRUN") {
                    const jobCode = document.getElementById("sim-job-code-overrun")?.value || "JOB-ENG-101";
                    const extraMin = parseInt(document.getElementById("sim-overrun-min")?.value || "60", 10);
                    payload = {
                        scenario_name: `Maintenance Overrun (+${extraMin}m on ${jobCode})`,
                        blocked_section_code: jobCode,
                        block_duration_extra_min: extraMin
                    };
                } else if (scType === "EMERGENCY_JOB") {
                    const title = document.getElementById("sim-job-title")?.value || "Emergency Rail Fracture Repair";
                    const sec = document.getElementById("sim-section")?.value || "FDB-PWL";
                    const dur = parseInt(document.getElementById("sim-duration")?.value || "180", 10);
                    payload = {
                        scenario_name: `Emergency Job (${title} @ ${sec})`,
                        emergency_job: {
                            job_code: `JOB-EMG-${Math.floor(100 + Math.random() * 900)}`,
                            title: title,
                            department_code: "ENG",
                            section_code: sec,
                            duration_minutes: dur,
                            priority: 5,
                            urgency: "CRITICAL",
                            requires_power_block: false,
                            requires_traffic_block: true,
                            requires_speed_restriction: true,
                            speed_restriction_kmh: 30
                        }
                    };
                }

                const data = await dataService.simulateWhatIf(payload);
                _showToast(`Re-Optimization Complete: ${data.impact_summary || 'Schedule recalculated.'}`, "success");

                // 1. Update KPI Deltas
                const deltaSched = data.delta_scheduled_jobs ?? (data.kpi_delta?.scheduled || 0);
                const deltaDelay = data.delta_train_delay_min ?? (data.kpi_delta?.train_delay_min || 0);
                const deltaUtil = data.delta_utilization_pct ?? (data.kpi_delta?.utilization_pct || 0);
                const deltaDef = data.delta_deferred_jobs ?? (data.kpi_delta?.deferred || 0);

                if (dJobs) dJobs.textContent = `${deltaSched >= 0 ? '+' : ''}${deltaSched} (${data.simulated_run?.scheduled_jobs_count || data.new_blocks?.length || 0})`;
                if (dDelay) dDelay.textContent = `${deltaDelay >= 0 ? '+' : ''}${deltaDelay}m`;
                if (dUtil) dUtil.textContent = `${deltaUtil >= 0 ? '+' : ''}${deltaUtil}%`;
                if (dDef) dDef.textContent = `${deltaDef >= 0 ? '+' : ''}${deltaDef}`;

                // 2. Summary Banner
                if (summaryCard) {
                    summaryCard.classList.remove("hidden");
                    if (summaryTitle) summaryTitle.textContent = data.scenario_name || "Scenario Simulation Result";
                    if (summarySubtitle) summarySubtitle.textContent = data.impact_summary || "Automated CP-SAT re-optimization completed across corridor.";
                    if (summaryStatus) summaryStatus.textContent = data.simulated_run?.status || "FEASIBLE";
                }

                // 3. Change Detection & Schedule Diff Table
                const baseBlocks = data.baseline_blocks || [];
                const newBlocks = data.new_blocks || (data.simulated_run?.scheduled_blocks || []);
                const changes = computeScheduleChanges(baseBlocks, newBlocks);

                if (diffTableContainer) {
                    diffTableContainer.innerHTML = renderScheduleDiffTable(changes);
                }

                // 4. Comparative Visual Timeline
                if (timelineContainer) {
                    timelineContainer.innerHTML = renderComparativeTimelineBars(baseBlocks, newBlocks);
                }

                // 5. Solver Alerts
                if (alertsContainer) {
                    const alerts = data.critical_alerts || [];
                    if (alerts.length > 0) {
                        alertsContainer.innerHTML = alerts.map(a => createWhatIfAlert(a, true)).join("");
                    } else {
                        alertsContainer.innerHTML = `<div class="p-3 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-lg text-body-sm font-medium">Scenario resolved with zero critical buffer or isolation violations.</div>`;
                    }
                }

            } catch (err) {
                console.error("Simulation error:", err);
                _showToast("Simulation error: " + err.message, "error");
            } finally {
                simBtn.disabled = false;
                simBtn.innerHTML = origText;
            }
        };
    }

    if (resetBtn) {
        resetBtn.onclick = () => {
            if (summaryCard) summaryCard.classList.add("hidden");
            if (dJobs) dJobs.textContent = "—";
            if (dDelay) dDelay.textContent = "—";
            if (dUtil) dUtil.textContent = "—";
            if (dDef) dDef.textContent = "—";

            if (timelineContainer) {
                timelineContainer.innerHTML = `
                    <div class="p-6 text-center text-on-surface-variant font-medium bg-surface-container-low rounded-lg">
                        Run a scenario to view side-by-side Baseline vs Re-Optimized corridor possession timelines.
                    </div>
                `;
            }

            if (diffTableContainer) {
                diffTableContainer.innerHTML = `
                    <div class="text-body-sm text-on-surface-variant italic p-6 bg-surface-container-low rounded-lg text-center font-medium">
                        Run a scenario to inspect specific job movements, start/end time shifts, and deconfliction actions.
                    </div>
                `;
            }

            if (alertsContainer) {
                alertsContainer.innerHTML = `
                    <div class="p-3 bg-surface-container-low rounded-lg text-on-surface-variant text-body-sm font-medium text-center">
                        Run a scenario to see automated solver warnings and conflict resolution notes.
                    </div>
                `;
            }

            _showToast("Scenario inputs reset.", "info");
        };
    }
}


// ============================================================
// 7. Constraints Logic Screen
// ============================================================
async function initConstraintsLogic() {
    const rulesContainer = document.getElementById("constraints-rules-container");
    const verifyTbody = document.getElementById("constraints-table-tbody");
    const explanationsContainer = document.getElementById("constraints-explanations-container");
    const runSummaryEl = document.getElementById("constraints-run-summary");

    // 1. Load and flatten the raw rule dictionary from /api/optimization/rules
    try {
        const rulesData = await dataService.getRailwayConstraints();
        const entries = [];
        if (rulesData && typeof rulesData === "object" && !Array.isArray(rulesData)) {
            for (const [category, rules] of Object.entries(rulesData)) {
                if (!rules || typeof rules !== "object") continue;
                for (const [key, entry] of Object.entries(rules)) {
                    if (!entry || typeof entry !== "object") continue;
                    let valueStr = "";
                    const v = entry.value;
                    if (Array.isArray(v)) valueStr = v.join(", ");
                    else if (v !== null && typeof v === "object") valueStr = JSON.stringify(v);
                    else if (v !== undefined) valueStr = String(v);
                    const isHard = entry.status === "VALIDATED" || entry.status === "HARD";
                    entries.push({
                        category,
                        key,
                        name: entry.name || key,
                        value: valueStr,
                        unit: entry.unit || "",
                        status: entry.status || "PROTOTYPE_ASSUMPTION",
                        isHard,
                        notes: entry.notes || ""
                    });
                }
            }
        }

        const ruleCountEl = document.getElementById("constraints-rule-count");
        if (ruleCountEl) ruleCountEl.textContent = entries.length > 0 ? `${entries.length} rules loaded` : "—";

        if (rulesContainer) {
            if (entries.length === 0) {
                rulesContainer.innerHTML = `<div class="p-4 rounded-xl border border-outline-variant bg-surface-container-low text-on-surface-variant text-[12px]">Railway rules are unavailable — the backend could not be reached.</div>`;
            } else {
                rulesContainer.innerHTML = entries.map(r => `
                    <div class="p-4 rounded-xl border ${r.isHard ? 'border-red-200 bg-red-50/50' : 'border-blue-200 bg-blue-50/50'} shadow-sm">
                        <div class="flex justify-between items-start mb-2 gap-2">
                            <div class="flex items-center gap-2 flex-wrap">
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold ${r.isHard ? 'bg-red-200 text-red-900' : 'bg-blue-200 text-blue-900'}">${r.isHard ? 'HARD CONSTRAINT' : 'CONFIG PARAMETER'}</span>
                                <span class="font-bold text-primary text-[14px]">${r.name}</span>
                            </div>
                            <span class="text-[11px] font-data-mono text-outline shrink-0">${r.category}.${r.key}</span>
                        </div>
                        <p class="text-body-sm text-on-surface leading-relaxed">${r.notes || r.name}</p>
                        <div class="mt-2 text-[11px] text-on-surface-variant font-data-mono flex items-center gap-1.5 flex-wrap">
                            <span class="material-symbols-outlined text-[14px] ${r.isHard ? 'text-red-600' : 'text-emerald-600'}">${r.isHard ? 'shield' : 'tune'}</span>
                            <span>Value: <strong>${r.value || '—'}</strong> ${r.unit}</span>
                            <span class="ml-2 px-1.5 py-0.5 rounded bg-surface-variant text-on-surface-variant">${r.status}</span>
                        </div>
                    </div>
                `).join("");
            }
        }

        // 2. Hard constraint verification table (status = how it is enforced)
        if (verifyTbody) {
            const hardEntries = entries.filter(e => e.isHard);
            if (hardEntries.length === 0) {
                verifyTbody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-on-surface-variant text-[12px]">No validated hard constraints loaded.</td></tr>`;
            } else {
                verifyTbody.innerHTML = hardEntries.map(e => `
                    <tr class="border-b border-surface-variant hover:bg-surface-bright transition-colors">
                        <td class="p-table-cell-padding font-medium">${e.name}</td>
                        <td class="p-table-cell-padding">${e.category.replace(/_/g, ' ')}</td>
                        <td class="p-table-cell-padding font-data-mono">${e.value} ${e.unit}</td>
                        <td class="p-table-cell-padding">
                            <span class="inline-flex items-center gap-xs text-emerald-700 font-medium">
                                <span class="material-symbols-outlined text-[14px]">verified</span> Enforced by CP-SAT
                            </span>
                        </td>
                    </tr>
                `).join("");
            }
        }
    } catch (err) {
        console.error("Constraints error:", err);
        if (rulesContainer) rulesContainer.innerHTML = `<div class="p-4 rounded-xl border border-red-200 bg-red-50 text-red-800 text-[12px]">Failed to load railway rules: ${err.message}</div>`;
    }

    // 3. Latest plan decision explanations (real backend data)
    try {
        const plan = await dataService.getOptimizedPlan();
        if (runSummaryEl) {
            if (plan.run_id) {
                runSummaryEl.textContent = `Run #${plan.run_id} · ${plan.status} · ${plan.scheduled_jobs_count ?? 0}/${plan.total_jobs ?? 0} scheduled · Utilization ${plan.block_utilization_pct ?? 0}% · Delay ${plan.train_delay_total_min ?? 0} min`;
            } else {
                runSummaryEl.textContent = "No optimization run yet — run the block planner to generate explanations.";
            }
        }
        if (explanationsContainer) {
            const expls = plan.explanations || [];
            if (expls.length === 0) {
                explanationsContainer.innerHTML = `<div class="p-4 rounded-xl border border-outline-variant bg-surface-container-low text-on-surface-variant text-[12px]">No decision explanations available yet. Run an optimization first.</div>`;
            } else {
                explanationsContainer.innerHTML = expls.map(e => `
                    <div class="p-3 rounded-lg border border-outline-variant bg-surface-container-lowest">
                        <div class="flex items-center gap-2 mb-1">
                            <span class="font-data-mono font-bold text-primary text-[12px]">${e.job_code}</span>
                            <span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${e.decision === 'SCHEDULED' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">${e.decision || 'SCHEDULED'}</span>
                        </div>
                        <p class="text-[12px] text-on-surface-variant leading-relaxed">${e.reason || ''}</p>
                    </div>
                `).join("");
            }
        }
    } catch (err) {
        console.error("Latest plan load error:", err);
        if (explanationsContainer) explanationsContainer.innerHTML = `<div class="p-4 rounded-xl border border-red-200 bg-red-50 text-red-800 text-[12px]">Could not load latest plan explanations.</div>`;
    }
}

// ============================================================
// 8. Reports & Analytics Screen (Dynamic KPIs, Charts, Filters, CSV)
// ============================================================
async function initReports() {
    const kpiUtil = document.getElementById("report-kpi-utilization");
    const kpiComp = document.getElementById("report-kpi-completion");
    const kpiDelay = document.getElementById("report-kpi-delay");
    const kpiConf = document.getElementById("report-kpi-conflicts");
    const chartContainer = document.getElementById("report-department-chart-container");
    const sectionContainer = document.getElementById("report-section-list-container");
    const corridorBadge = document.getElementById("report-corridor-badge");
    const sectionContextLabel = document.getElementById("report-section-context-label");

    // Filter controls
    const filterDiv = document.getElementById("filter-report-division");
    const filterSection = document.getElementById("filter-report-section");
    const filterDept = document.getElementById("filter-report-dept");
    const filterDate = document.getElementById("filter-report-date-range");
    const btnApply = document.getElementById("btn-apply-report-filters");
    const btnReset = document.getElementById("btn-reset-report-filters");

    // Tabs
    const tabPerf = document.getElementById("tab-btn-performance");
    const tabTrends = document.getElementById("tab-btn-trends");
    const tabRaw = document.getElementById("tab-btn-raw");
    const viewPerf = document.getElementById("view-performance");
    const viewTrends = document.getElementById("view-trends");
    const viewRaw = document.getElementById("view-raw");

    // Table / Trends containers
    const trendsContainer = document.getElementById("report-trends-container");
    const rawTbody = document.getElementById("report-raw-tbody");
    const rawCountBadge = document.getElementById("report-raw-count-badge");
    const btnExport = document.getElementById("btn-export-report-csv");

    let currentReportData = null;
    let activeTab = "performance"; // "performance" | "trends" | "raw"

    // Tab Switching Logic
    const switchTab = (tabName) => {
        activeTab = tabName;
        const tabs = [
            { name: "performance", btn: tabPerf, view: viewPerf },
            { name: "trends", btn: tabTrends, view: viewTrends },
            { name: "raw", btn: tabRaw, view: viewRaw }
        ];

        tabs.forEach(t => {
            if (!t.btn || !t.view) return;
            if (t.name === tabName) {
                t.btn.className = "px-md py-sm text-label-md font-label-md rounded bg-primary-container text-on-primary font-semibold transition-colors shadow-xs";
                t.view.classList.remove("hidden");
            } else {
                t.btn.className = "px-md py-sm text-label-md font-label-md text-on-surface hover:bg-surface-container transition-colors rounded";
                t.view.classList.add("hidden");
            }
        });
    };

    if (tabPerf) tabPerf.onclick = () => switchTab("performance");
    if (tabTrends) tabTrends.onclick = () => switchTab("trends");
    if (tabRaw) tabRaw.onclick = () => switchTab("raw");

    const getActiveFilters = () => ({
        division: filterDiv?.value || "ALL",
        section: filterSection?.value || "ALL",
        department: filterDept?.value || "ALL",
        dateRange: filterDate?.value || ""
    });

    const renderReports = (data) => {
        currentReportData = data;
        const kpis = data.kpis || {};

        // 1. Context labels — full string includes the honest "Synthetic Demo Corridor" suffix
        const ctxLabel = data.corridor_context || "Delhi–Agra Mainline (Synthetic Demo Corridor)";
        if (corridorBadge) corridorBadge.textContent = ctxLabel;
        if (sectionContextLabel) sectionContextLabel.textContent = ctxLabel;

        // 2. Hydrate KPIs (strictly grounded numbers — "—" when the metric is 0/absent)
        const fmtPct = (v) => (v != null && v > 0) ? `${v}%` : "—";
        if (kpiUtil) kpiUtil.textContent = fmtPct(kpis.block_utilization_pct);
        if (kpiComp) kpiComp.textContent = fmtPct(kpis.job_completion_rate_pct);
        if (kpiDelay) kpiDelay.textContent = (kpis.mean_delay_per_block_min != null) ? `${kpis.mean_delay_per_block_min}m` : "—";
        if (kpiConf) kpiConf.textContent = fmtPct(kpis.safety_compliance_pct);

        // 3. Hydrate Department Chart
        if (chartContainer) {
            const depts = data.department_statistics || [];
            if (depts.length === 0) {
                chartContainer.innerHTML = `<div class="w-full text-center text-on-surface-variant py-8 font-medium">No departmental possession data available for the active filter.</div>`;
            } else {
                const maxHours = Math.max(...depts.map(d => Math.max(d.requested_hours || 0, d.approved_hours || 0)), 10);
                const step = Math.ceil(maxHours / 4);
                const ceilMax = Math.max(step * 4, 8);

                const chartBars = depts.map(d => {
                    const reqPct = Math.min(100, Math.round(((d.requested_hours || 0) / ceilMax) * 100));
                    const appPct = Math.min(100, Math.round(((d.approved_hours || 0) / ceilMax) * 100));

                    return `
                        <div class="flex-1 flex flex-col justify-end items-center group relative z-10 h-full">
                            <div class="w-full flex justify-center gap-1.5 items-end h-[85%]">
                                <div class="w-6 sm:w-8 bg-surface-variant rounded-t transition-all duration-300 relative group-hover:opacity-80 border border-outline-variant/30" style="height: ${reqPct}%;" title="Requested: ${d.requested_hours}h (${d.requested} jobs)"></div>
                                <div class="w-6 sm:w-8 bg-primary-container rounded-t transition-all duration-300 relative group-hover:brightness-110 shadow-sm" style="height: ${appPct}%;" title="Approved: ${d.approved_hours}h (${d.scheduled} jobs)"></div>
                            </div>
                            <div class="text-[11px] font-label-md mt-sm text-on-surface font-semibold truncate max-w-[80px]" title="${d.name}">${d.name.split(' ')[0]}</div>
                            <div class="text-[10px] font-data-mono text-on-surface-variant">${d.grant_rate}%</div>
                        </div>
                    `;
                }).join("");

                chartContainer.innerHTML = `
                    <!-- Y-Axis Labels -->
                    <div class="absolute left-[-28px] top-0 bottom-sm flex flex-col justify-between text-[10px] text-outline font-data-mono h-full pb-sm select-none">
                        <span>${ceilMax}h</span>
                        <span>${step * 3}h</span>
                        <span>${step * 2}h</span>
                        <span>${step * 1}h</span>
                        <span>0h</span>
                    </div>
                    <!-- Grid Lines -->
                    <div class="absolute inset-0 border-b border-surface-variant top-1/4 w-full h-[1px]"></div>
                    <div class="absolute inset-0 border-b border-surface-variant top-2/4 w-full h-[1px]"></div>
                    <div class="absolute inset-0 border-b border-surface-variant top-3/4 w-full h-[1px]"></div>
                    <!-- Bars -->
                    ${chartBars}
                `;
            }
        }

        // 4. Hydrate Section Efficiency List
        if (sectionContainer) {
            const sections = data.section_statistics || [];
            if (sections.length === 0) {
                sectionContainer.innerHTML = `<div class="text-center text-on-surface-variant py-8 font-medium">No section data matching the filter.</div>`;
            } else {
                sectionContainer.innerHTML = sections.map(s => {
                    const rate = s.completion_rate != null ? s.completion_rate : 0;
                    const colorClass = rate >= 90 ? "text-emerald-700 bg-emerald-600" : (rate >= 75 ? "text-amber-700 bg-amber-500" : "text-red-700 bg-red-500");
                    const [textColor, barColor] = colorClass.split(" ");

                    return `
                        <div class="p-2 rounded hover:bg-surface-container-low transition-colors">
                            <div class="flex justify-between text-body-sm font-label-md mb-1">
                                <span class="font-data-mono font-bold text-primary">${s.code}</span>
                                <span class="${textColor} font-bold text-[12px]">${rate}%</span>
                            </div>
                            <div class="w-full bg-surface-variant rounded-full h-1.5 overflow-hidden">
                                <div class="${barColor} h-1.5 rounded-full transition-all duration-300" style="width: ${rate}%"></div>
                            </div>
                            <div class="flex justify-between text-[10px] text-on-surface-variant mt-1 font-data-mono">
                                <span>${s.name}</span>
                                <span>${s.completed}/${s.requested} blocks</span>
                            </div>
                        </div>
                    `;
                }).join("");
            }
        }

        // 5. Hydrate Trends View
        if (trendsContainer) {
            const runs = data.historical_optimization_runs || [];
            if (runs.length === 0) {
                trendsContainer.innerHTML = `<div class="text-center text-on-surface-variant py-8 font-medium">Insufficient historical optimization runs for the selected scope.</div>`;
            } else {
                trendsContainer.innerHTML = `
                    <table class="w-full text-left border-collapse text-body-sm">
                        <thead class="bg-surface-container-low text-[11px] font-label-md text-on-surface-variant uppercase tracking-wide border-b border-outline-variant">
                            <tr>
                                <th class="p-table-cell-padding">Run ID</th>
                                <th class="p-table-cell-padding">Timestamp</th>
                                <th class="p-table-cell-padding">Status</th>
                                <th class="p-table-cell-padding">Scheduled Blocks</th>
                                <th class="p-table-cell-padding">Train Delay</th>
                                <th class="p-table-cell-padding">Utilization</th>
                                <th class="p-table-cell-padding">Synergy</th>
                                <th class="p-table-cell-padding">Solver Runtime</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-outline-variant/30 font-data-mono text-[12px]">
                            ${runs.map(r => `
                                <tr class="hover:bg-surface-container-low transition-colors">
                                    <td class="p-table-cell-padding font-bold text-primary">#${r.run_id}</td>
                                    <td class="p-table-cell-padding text-on-surface">${r.timestamp}</td>
                                    <td class="p-table-cell-padding"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${r.status === 'OPTIMAL' ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'}">${r.status}</span></td>
                                    <td class="p-table-cell-padding font-bold">${r.scheduled}</td>
                                    <td class="p-table-cell-padding text-amber-700">${r.train_delay_min}m</td>
                                    <td class="p-table-cell-padding">${r.utilization}%</td>
                                    <td class="p-table-cell-padding">${r.synergy}%</td>
                                    <td class="p-table-cell-padding text-on-surface-variant">${r.solver_time_sec}s</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                `;
            }
        }

        // 6. Hydrate Raw Data View
        if (rawTbody) {
            const records = data.raw_records || [];
            if (rawCountBadge) rawCountBadge.textContent = `${records.length} Records`;

            if (records.length === 0) {
                rawTbody.innerHTML = `<tr><td colspan="9" class="p-8 text-center text-on-surface-variant font-medium">No scheduled possession records matching active filters.</td></tr>`;
            } else {
                rawTbody.innerHTML = records.map(r => `
                    <tr class="hover:bg-surface-container-low transition-colors">
                        <td class="p-table-cell-padding font-data-mono font-bold text-primary">${r.job_code}</td>
                        <td class="p-table-cell-padding font-medium text-on-surface">${r.title}</td>
                        <td class="p-table-cell-padding"><span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-surface-variant text-on-surface">${r.department}</span></td>
                        <td class="p-table-cell-padding font-data-mono">${r.section}</td>
                        <td class="p-table-cell-padding font-data-mono">${r.window}</td>
                        <td class="p-table-cell-padding font-data-mono">${r.duration}</td>
                        <td class="p-table-cell-padding">${r.is_shadow === 'Yes' ? '<span class="text-emerald-700 font-bold">Yes (Shadow)</span>' : 'No'}</td>
                        <td class="p-table-cell-padding text-on-surface-variant">${r.resource}</td>
                        <td class="p-table-cell-padding"><span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${r.status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">${r.status}</span></td>
                    </tr>
                `).join("");
            }
        }
    };

    const loadReportsData = async (filters = {}) => {
        if (kpiUtil) kpiUtil.textContent = "...";
        if (kpiComp) kpiComp.textContent = "...";
        if (kpiDelay) kpiDelay.textContent = "...";
        if (chartContainer) chartContainer.innerHTML = `<div class="w-full text-center text-on-surface-variant py-8 font-medium"><span class="material-symbols-outlined animate-spin text-[20px] align-middle mr-1">sync</span> Fetching reports...</div>`;
        if (sectionContainer) sectionContainer.innerHTML = `<div class="text-center text-on-surface-variant py-8 font-medium">Loading section metrics...</div>`;

        try {
            const data = await dataService.getOperationalReports(filters);
            renderReports(data);
        } catch (err) {
            console.error("Reports API error:", err);
            if (chartContainer) chartContainer.innerHTML = `<div class="w-full text-center text-error py-8 font-medium">Failed to load analytics (${err.message}).</div>`;
            if (sectionContainer) sectionContainer.innerHTML = `<div class="text-center text-error py-8 font-medium">Unable to load section statistics.</div>`;
        }
    };

    // Filter event handlers
    if (btnApply) {
        btnApply.onclick = async () => {
            const filters = getActiveFilters();
            await loadReportsData(filters);
            _showToast("Analytics filters applied.", "success");
        };
    }

    if (btnReset) {
        btnReset.onclick = async () => {
            if (filterDiv) filterDiv.value = "ALL";
            if (filterSection) filterSection.value = "ALL";
            if (filterDept) filterDept.value = "ALL";
            await loadReportsData(getActiveFilters());
            _showToast("Filters reset to default corridor view.", "info");
        };
    }

    if (filterDiv) filterDiv.onchange = () => loadReportsData(getActiveFilters());
    if (filterSection) filterSection.onchange = () => loadReportsData(getActiveFilters());
    if (filterDept) filterDept.onchange = () => loadReportsData(getActiveFilters());

    // Export CSV handler: exports the active filtered raw possession dataset matching the active filters
    if (btnExport) {
        btnExport.onclick = () => {
            const data = currentReportData;
            if (!data) return;
            const records = data.raw_records || [];
            if (records.length === 0) {
                _showToast("No possession records to export for active filter.", "warning");
                return;
            }
            const header = "Block ID,Job Code,Title,Department,Section,Division,Time Window,Duration Min,Is Shadow,Resource,Status";
            const rows = records.map(r =>
                `"${r.block_id}","${r.job_code}","${(r.title || '').replace(/"/g, '""')}","${r.department}","${r.section}","${r.division}","${r.window}","${r.duration_min}","${r.is_shadow}","${r.resource}","${r.status}"`
            ).join("\n");
            const csvContent = `data:text/csv;charset=utf-8,${encodeURIComponent(header + "\n" + rows)}`;
            const link = document.createElement("a");
            link.setAttribute("href", csvContent);
            link.setAttribute("download", `railopt_possessions_${(filterDiv?.value || 'ALL')}_${new Date().toISOString().split('T')[0]}.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            _showToast(`Exported ${records.length} possession records to CSV.`, "success");
        };
    }

    await loadReportsData(getActiveFilters());
}


// ============================================================
// 9. Auto-route by Page Type on Load
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    _requireAuth();
    setupNavigation();
    _updateHeaderFromSession();

    // Auto-update header clock every minute
    setInterval(_updateHeaderFromSession, 30000);

    const path = window.location.pathname.toLowerCase();
    if (path.includes("maintenance-requests")) {
        initMaintenanceRequests();
    } else if (path.includes("block-planning")) {
        initBlockPlanning();
    } else if (path.includes("gantt-view")) {
        initGanttView();
    } else if (path.includes("what-if")) {
        initWhatIf();
    } else if (path.includes("constraints-logic")) {
        initConstraintsLogic();
    } else if (path.includes("reports")) {
        initReports();
    } else {
        initDashboard();
    }
});

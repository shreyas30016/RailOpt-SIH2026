/**
 * Reusable Maintenance Job Row & Card Component
 * Updated: CRUD action buttons with data-action/data-job-id for event delegation in app.js
 */

export function createJobTableRow(job) {
    const deptBg = job.department_code === 'ENG'
        ? 'bg-blue-100 text-blue-800'
        : (job.department_code === 'TRD'
            ? 'bg-amber-100 text-amber-800'
            : (job.department_code === 'S_T' ? 'bg-cyan-100 text-cyan-800' : 'bg-slate-100 text-slate-800'));

    const urgencyBadge = job.urgency === 'CRITICAL'
        ? 'bg-red-100 text-red-800'
        : (job.urgency === 'HIGH' ? 'bg-orange-100 text-orange-800' : 'bg-slate-100 text-slate-700');

    const statusBadge = job.status === 'SCHEDULED'
        ? 'bg-green-100 text-green-800'
        : (job.status === 'APPROVED' ? 'bg-blue-100 text-blue-800'
        : (job.status === 'DEFERRED' ? 'bg-red-50 text-red-700'
        : 'bg-amber-50 text-amber-800'));

    const jobId = job.id !== undefined && job.id !== null ? job.id : (job.job_code || "0");
    // Only show approve/defer for actionable statuses and authorized roles
    const isActionable = !['SCHEDULED', 'CANCELLED'].includes(job.status);

    let user = null;
    try {
        const raw = localStorage.getItem("railopt_user");
        user = raw ? JSON.parse(raw) : null;
    } catch {}

    const canApprove = Boolean(user?.can_approve || user?.role === "CONTROLLER" || user?.role === "PLANNER");
    const userRole = user?.role || "CONTROLLER";
    const jobDept = job.department_code || job.department || "ENG";
    const isOwnDept = (userRole === "ENGINEER" && jobDept === "ENG") ||
                      (userRole === "TRD_OFFICER" && jobDept === "TRD") ||
                      (userRole === "ST_OFFICER" && (jobDept === "S_T" || jobDept === "ST" || jobDept === "S&T")) ||
                      canApprove;

    return `
        <tr class="border-b border-outline-variant border-opacity-30 hover:bg-surface-container-low transition-colors cursor-pointer request-row"
            data-job-id="${jobId}" data-job-code="${job.job_code || jobId}">
            <td class="p-table-cell-padding font-data-mono text-primary font-bold">
                <span class="hover:underline cursor-pointer" title="Click to view decision audit" onclick="event.stopPropagation(); window.showJobExplanation && window.showJobExplanation('${job.job_code || job.id}')">${job.job_code || job.id}</span>
            </td>
            <td class="p-table-cell-padding">
                <div class="font-body-md text-on-surface font-semibold">${job.title}</div>
                <div class="text-body-sm text-on-surface-variant line-clamp-1">${job.description || ''}</div>
            </td>

            <td class="p-table-cell-padding">
                <span class="px-2.5 py-1 rounded text-body-sm font-bold ${deptBg}">
                    ${job.department_code || job.department}
                </span>
            </td>
            <td class="p-table-cell-padding font-data-mono text-body-sm text-on-surface-variant">
                ${job.section_code || job.section} (${job.track_line || 'UP'})
            </td>
            <td class="p-table-cell-padding font-data-mono text-body-sm font-semibold text-primary">
                ${job.duration_minutes} min
            </td>
            <td class="p-table-cell-padding">
                <div class="flex items-center gap-1.5">
                    ${job.requires_power_block ? '<span class="material-symbols-outlined text-amber-600 text-[18px]" title="Traction Power Block Required">bolt</span>' : ''}
                    ${job.requires_traffic_block ? '<span class="material-symbols-outlined text-red-600 text-[18px]" title="Traffic Halt Required">block</span>' : ''}
                    ${job.requires_speed_restriction ? '<span class="material-symbols-outlined text-orange-600 text-[18px]" title="Speed Restriction">speed</span>' : ''}
                </div>
            </td>
            <td class="p-table-cell-padding">
                <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold ${urgencyBadge}">
                    ${job.urgency}
                </span>
            </td>
            <td class="p-table-cell-padding">
                <span class="px-2 py-0.5 rounded text-[11px] font-semibold ${statusBadge}">
                    ${job.status}
                </span>
            </td>
            <td class="p-table-cell-padding" onclick="if(!event.target.closest('button')) event.stopPropagation()">
                <div class="flex items-center gap-1">
                    ${canApprove && isActionable && job.status !== 'APPROVED' ? `
                    <button
                        data-action="approve"
                        data-job-id="${jobId}"
                        class="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-600 text-white hover:bg-emerald-700 transition-colors whitespace-nowrap"
                        title="Approve this maintenance request">
                        ✓ Approve
                    </button>` : ''}
                    ${canApprove && isActionable && job.status !== 'DEFERRED' ? `
                    <button
                        data-action="defer"
                        data-job-id="${jobId}"
                        class="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500 text-white hover:bg-amber-600 transition-colors whitespace-nowrap"
                        title="Defer this request">
                        ⏸ Defer
                    </button>` : ''}
                    ${!canApprove ? `
                    <button
                        onclick="window.showJobExplanation && window.showJobExplanation('${job.job_code || job.id}')"
                        class="text-[10px] font-bold px-2 py-0.5 rounded bg-primary-container text-on-primary hover:bg-primary transition-colors whitespace-nowrap"
                        title="View Solver & Safety Audit">
                        Audit
                    </button>` : ''}
                    ${isOwnDept ? `
                    <button
                        data-action="delete"
                        data-job-id="${jobId}"
                        class="text-[10px] font-bold px-2 py-0.5 rounded bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
                        title="Delete this request permanently">
                        ✕
                    </button>` : ''}
                </div>
            </td>
        </tr>
    `;
}

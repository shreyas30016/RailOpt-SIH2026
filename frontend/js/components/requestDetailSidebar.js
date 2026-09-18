/**
 * Dynamic Maintenance Request Detail Sidebar Component for RailOpt
 * Replaces static J-03 mockup with dynamic, API-backed selection details.
 */

export function renderRequestDetailSidebar(job, { onAction, userCanApprove = true } = {}) {
    const sidebar = document.getElementById("request-detail-sidebar");
    if (!sidebar) return;

    if (!job) {
        sidebar.innerHTML = renderEmptyRequestDetailSidebar();
        return;
    }

    const urgencyBadge = job.urgency === 'CRITICAL'
        ? 'bg-red-100 text-red-800 border-red-200'
        : (job.urgency === 'HIGH' ? 'bg-orange-100 text-orange-800 border-orange-200' : 'bg-slate-100 text-slate-700 border-slate-200');

    const statusConfig = {
        'APPROVED': { label: 'Approved (Ready for Solver)', bg: 'bg-blue-600', text: 'text-blue-800', width: '75%', pill: 'bg-blue-100 text-blue-800' },
        'SCHEDULED': { label: 'Scheduled in Block Plan', bg: 'bg-emerald-600', text: 'text-emerald-800', width: '100%', pill: 'bg-emerald-100 text-emerald-800' },
        'DEFERRED': { label: 'Deferred / Re-planning Required', bg: 'bg-amber-600', text: 'text-amber-800', width: '35%', pill: 'bg-amber-100 text-amber-800' },
        'PENDING': { label: 'Pending Review & Approval', bg: 'bg-indigo-600', text: 'text-indigo-800', width: '25%', pill: 'bg-indigo-100 text-indigo-800' }
    }[job.status] || { label: job.status, bg: 'bg-slate-600', text: 'text-slate-800', width: '50%', pill: 'bg-slate-100 text-slate-800' };

    const formatMin = (m) => {
        if (m === undefined || m === null) return "--:--";
        const h = Math.floor(m / 60) % 24;
        const min = m % 60;
        return `${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}`;
    };

    const requestedBy = `SSE/${job.department_code || job.department}/${(job.section_code || 'NDLS').split('-')[0]}`;

    sidebar.innerHTML = `
        <!-- Sidebar Header -->
        <div class="px-md py-md border-b border-outline-variant flex items-start justify-between bg-surface-container-low shrink-0">
            <div>
                <div class="flex items-center gap-2 mb-1">
                    <h3 class="font-headline-sm text-headline-sm text-on-surface font-bold font-data-mono">${job.job_code || job.id}</h3>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${urgencyBadge}">${job.urgency}</span>
                </div>
                <p class="font-body-sm text-body-sm text-on-surface-variant font-medium line-clamp-2">${job.title}</p>
            </div>
            <button id="btn-close-detail-sidebar" class="text-outline hover:text-on-surface rounded p-1 hover:bg-surface-variant transition-colors" title="Deselect Request">
                <span class="material-symbols-outlined text-[20px]">close</span>
            </button>
        </div>

        <!-- Details Content -->
        <div class="flex-1 overflow-y-auto p-md flex flex-col gap-4">
            <!-- Status Bar -->
            <div class="bg-surface-container-low rounded-lg p-3 border border-outline-variant">
                <div class="flex justify-between items-center mb-1">
                    <span class="text-[10px] uppercase font-label-md text-on-surface-variant font-bold">Current Status</span>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${statusConfig.pill}">${job.status}</span>
                </div>
                <div class="text-[11px] text-on-surface-variant mt-1 font-medium">${statusConfig.label}</div>
                <div class="w-full bg-outline-variant/30 rounded-full h-1.5 mt-2 overflow-hidden">
                    <div class="${statusConfig.bg} h-1.5 rounded-full" style="width: ${statusConfig.width};"></div>
                </div>
            </div>

            <!-- Info Grid -->
            <div class="grid grid-cols-2 gap-y-3 gap-x-2 bg-surface-container-lowest p-3 rounded-lg border border-outline-variant/60">
                <div>
                    <div class="text-[10px] uppercase font-label-md text-on-surface-variant mb-0.5 font-bold">Department</div>
                    <div class="font-body-sm text-on-surface font-semibold text-[12px] flex items-center gap-1">
                        <span class="material-symbols-outlined text-[15px] text-primary">engineering</span>
                        ${job.department_code || job.department}
                    </div>
                </div>
                <div>
                    <div class="text-[10px] uppercase font-label-md text-on-surface-variant mb-0.5 font-bold">Requested By</div>
                    <div class="font-body-sm text-on-surface font-data-mono text-[11px] truncate">${requestedBy}</div>
                </div>
                <div>
                    <div class="text-[10px] uppercase font-label-md text-on-surface-variant mb-0.5 font-bold">Section</div>
                    <div class="font-body-sm text-on-surface font-data-mono text-[12px] font-bold text-primary">${job.section_code || job.section}</div>
                </div>
                <div>
                    <div class="text-[10px] uppercase font-label-md text-on-surface-variant mb-0.5 font-bold">Track Line</div>
                    <div class="font-body-sm text-on-surface font-data-mono text-[11px] font-semibold">${job.track_line || 'UP_MAIN'}</div>
                </div>
                <div>
                    <div class="text-[10px] uppercase font-label-md text-on-surface-variant mb-0.5 font-bold">Duration</div>
                    <div class="font-body-sm text-on-surface font-data-mono font-bold text-[12px] text-primary">${job.duration_minutes} min</div>
                </div>
                <div>
                    <div class="text-[10px] uppercase font-label-md text-on-surface-variant mb-0.5 font-bold">Preferred Slot</div>
                    <div class="font-body-sm text-on-surface font-data-mono text-[11px]">${formatMin(job.earliest_start_minute)}–${formatMin(job.latest_end_minute)}</div>
                </div>
            </div>

            <!-- Safety Clearances -->
            <div class="p-3 bg-surface-container-low rounded-lg border border-outline-variant">
                <span class="text-[10px] uppercase font-label-md text-on-surface-variant mb-2 block font-bold">Required Safety Clearances</span>
                <div class="flex flex-col gap-1.5 text-[11px]">
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-[16px] ${job.requires_traffic_block ? 'text-red-600' : 'text-slate-400'}">
                            ${job.requires_traffic_block ? 'check_box' : 'check_box_outline_blank'}
                        </span>
                        <span class="${job.requires_traffic_block ? 'font-bold text-on-surface' : 'text-on-surface-variant'}">Traffic Halt Block (Track Possession)</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-[16px] ${job.requires_power_block ? 'text-amber-600' : 'text-slate-400'}">
                            ${job.requires_power_block ? 'check_box' : 'check_box_outline_blank'}
                        </span>
                        <span class="${job.requires_power_block ? 'font-bold text-on-surface' : 'text-on-surface-variant'}">25kV Traction Power Block (OHE)</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-[16px] ${job.requires_speed_restriction ? 'text-orange-600' : 'text-slate-400'}">
                            ${job.requires_speed_restriction ? 'check_box' : 'check_box_outline_blank'}
                        </span>
                        <span class="${job.requires_speed_restriction ? 'font-bold text-on-surface' : 'text-on-surface-variant'}">
                            Temporary Speed Restriction ${job.requires_speed_restriction ? `(${job.speed_restriction_kmh || 30} km/h)` : ''}
                        </span>
                    </div>
                </div>
            </div>

            <!-- Description -->
            <div>
                <div class="text-[10px] uppercase font-label-md text-on-surface-variant mb-1 font-bold">Description & Scope</div>
                <p class="font-body-sm text-on-surface text-[12px] leading-relaxed p-3 bg-surface-container-lowest rounded-lg border border-outline-variant/60">
                    ${job.description || 'No detailed remarks provided for this possession request.'}
                </p>
            </div>
        </div>

        <!-- Action Footer -->
        <div class="p-md border-t border-outline-variant bg-surface-container-low shrink-0 flex gap-2">
            <button id="btn-sidebar-delete" data-job-id="${job.id || job.job_code}" class="p-2 border border-red-200 text-red-600 rounded bg-white hover:bg-red-50 transition-colors" title="Delete Request">
                <span class="material-symbols-outlined text-[18px]">delete</span>
            </button>
            <button id="btn-sidebar-defer" data-job-id="${job.id || job.job_code}" ${!userCanApprove ? 'disabled' : ''} class="flex-1 px-3 py-2 border border-outline-variant rounded bg-white text-on-surface font-label-md hover:bg-surface-variant transition-colors text-[12px] font-bold ${!userCanApprove ? 'opacity-50 cursor-not-allowed' : ''}">
                ⏸ Defer
            </button>
            <button id="btn-sidebar-approve" data-job-id="${job.id || job.job_code}" ${!userCanApprove ? 'disabled' : ''} class="flex-1 px-3 py-2 rounded bg-primary-container text-on-primary font-label-md hover:bg-primary transition-colors shadow-sm text-[12px] font-bold ${!userCanApprove ? 'opacity-50 cursor-not-allowed' : ''}">
                ✓ Approve
            </button>
        </div>
    `;

    const targetJobId = job.id !== undefined && job.id !== null ? job.id : (job.job_code || "0");

    // Bind action events
    document.getElementById("btn-close-detail-sidebar")?.addEventListener("click", () => {
        sidebar.innerHTML = renderEmptyRequestDetailSidebar();
    });

    if (typeof onAction === "function") {
        document.getElementById("btn-sidebar-delete")?.addEventListener("click", () => onAction("delete", targetJobId));
        document.getElementById("btn-sidebar-defer")?.addEventListener("click", () => onAction("defer", targetJobId));
        document.getElementById("btn-sidebar-approve")?.addEventListener("click", () => onAction("approve", targetJobId));
    }
}

export function renderEmptyRequestDetailSidebar() {
    return `
        <div class="px-md py-md border-b border-outline-variant bg-surface-container-low shrink-0">
            <h3 class="font-headline-sm text-headline-sm text-on-surface font-bold">Request Details</h3>
            <p class="font-body-sm text-body-sm text-on-surface-variant text-[12px]">Possession & Safety Clearance Inspector</p>
        </div>
        <div class="flex-1 flex flex-col items-center justify-center p-md text-center text-on-surface-variant gap-3">
            <div class="w-12 h-12 rounded-full bg-surface-variant/40 flex items-center justify-center text-outline">
                <span class="material-symbols-outlined text-[28px]">touch_app</span>
            </div>
            <h4 class="font-headline-sm text-on-surface font-bold text-[14px]">No Request Selected</h4>
            <p class="text-body-sm text-[12px] max-w-xs text-on-surface-variant">
                Click any maintenance request row in the table to view complete possession details, safety clearances, and operational actions.
            </p>
        </div>
    `;
}

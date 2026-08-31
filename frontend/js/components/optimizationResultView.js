/**
 * Reusable Optimization Result & Decision Explanation Component
 */

export function createScheduledBlockRow(block) {
    const deptBg = block.department_code === 'ENG' 
        ? 'bg-blue-100 text-blue-800' 
        : (block.department_code === 'TRD' ? 'bg-amber-100 text-amber-800' : 'bg-cyan-100 text-cyan-800');

    return `
        <tr class="border-b border-outline-variant border-opacity-30 hover:bg-surface transition-colors">
            <td class="p-table-cell-padding font-data-mono text-primary font-bold">
                <button onclick="window.showJobExplanation('${block.job_code || block.job_id}')" class="text-primary hover:underline font-bold text-left flex items-center gap-1">
                    <span>${block.job_code || block.job_id}</span>
                    <span class="material-symbols-outlined text-[14px] opacity-70">open_in_new</span>
                </button>
            </td>
            <td class="p-table-cell-padding">
                <div class="font-body-md text-on-surface font-semibold">${block.title}</div>
                <div class="text-body-sm text-on-surface-variant line-clamp-1">${block.explanation || ''}</div>
            </td>
            <td class="p-table-cell-padding">
                <span class="px-2 py-0.5 rounded text-[11px] font-bold ${deptBg}">
                    ${block.department_code}
                </span>
            </td>
            <td class="p-table-cell-padding font-data-mono text-body-sm text-on-surface-variant">
                ${block.section_code} (${block.track_line})
            </td>
            <td class="p-table-cell-padding font-data-mono text-primary font-bold text-body-sm">
                ${block.start_time_str} - ${block.end_time_str} (${block.duration_minutes}m)
            </td>
            <td class="p-table-cell-padding">
                ${block.is_shadow_block ? 
                    `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-green-100 text-green-800 flex items-center gap-1 w-fit"><span class="material-symbols-outlined text-[14px]">link</span> Shadow Block</span>` : 
                    `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700">Dedicated</span>`
                }
            </td>
            <td class="p-table-cell-padding font-body-sm text-on-surface-variant font-data-mono text-[12px]">
                ${block.resource_assigned || 'Standard Gang'}
            </td>
        </tr>
    `;
}

export function renderDecisionAuditModal(auditData) {
    let modal = document.getElementById("explainer-modal");
    if (!modal) {
        modal = document.createElement("div");
        modal.id = "explainer-modal";
        modal.className = "fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4 animate-fade-in";
        document.body.appendChild(modal);
    }

    const isSched = auditData.status === "SCHEDULED" || auditData.status === "SHADOW_PAIRED";
    const statusPill = isSched 
        ? `<span class="px-2.5 py-0.5 rounded text-[11px] font-bold bg-green-100 text-green-800">SCHEDULED</span>`
        : `<span class="px-2.5 py-0.5 rounded text-[11px] font-bold bg-red-100 text-red-800">DEFERRED</span>`;

    // Reason code badge for deferred jobs
    const reasonCodeBadge = (!isSched && auditData.reason_code) ?
        `<span class="ml-2 px-2 py-0.5 rounded text-[10px] font-bold bg-orange-100 text-orange-800 border border-orange-200">${auditData.reason_code}</span>` : "";

    // Scheduled window info
    const windowInfo = auditData.scheduled_window ?
        `<div class="text-[12px] font-data-mono text-on-surface-variant mt-0.5">
            ${auditData.scheduled_window.start_str}–${auditData.scheduled_window.end_str}
            (${auditData.scheduled_window.duration_min} min) on ${auditData.section || ""}
         </div>` : "";

    // Shadow block info
    const shadowInfo = (isSched && auditData.shadow_block && auditData.paired_jobs?.length > 0) ?
        `<div class="mt-2 p-2 rounded bg-emerald-50 border border-emerald-200 text-[12px] text-emerald-800 flex items-center gap-1">
            <span class="material-symbols-outlined text-[14px]">link</span>
            <strong>Shadow Block:</strong> Co-located with ${auditData.paired_jobs.join(", ")} — shared track possession
         </div>` : "";

    // Failed candidate windows (deferred only)
    const failedWindowsHtml = (!isSched && auditData.failed_candidate_windows?.length > 0) ?
        `<div class="mt-3">
            <div class="font-label-md font-bold text-on-surface text-[12px] mb-1 flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px] text-red-600">block</span>
                Failed Candidate Windows (${auditData.failed_candidate_windows.length} evaluated)
            </div>
            ${auditData.failed_candidate_windows.map(w => `
                <div class="p-2 rounded border border-red-100 bg-red-50 mb-1 text-[12px]">
                    <span class="font-data-mono font-bold text-red-900">${w.start_str}–${w.end_str}</span>
                    <span class="text-red-700 ml-2">${w.failure_reason}</span>
                </div>
            `).join("")}
        </div>` : "";

    // Next feasible window (deferred only)
    const nextWindowHtml = (!isSched && auditData.next_feasible_window) ?
        `<div class="mt-2 p-2 rounded bg-blue-50 border border-blue-200 text-[12px] text-blue-800 flex items-center gap-1">
            <span class="material-symbols-outlined text-[14px]">schedule</span>
            <strong>Next Feasible Slot:</strong> ${auditData.next_feasible_window.start_str}–${auditData.next_feasible_window.end_str}
            (${auditData.next_feasible_window.duration_min} min, no train conflicts detected)
         </div>` : "";

    // Reasoning tree nodes
    const treeHtml = (auditData.reasoning_tree || []).map(node => {
        const isOk = node.status === "PASSED" || node.status === "OPTIMIZED" || node.status === "PRIORITISED" || node.status === "SHADOW_PAIRED" || node.status === "STANDALONE" || node.status === "SCHEDULED" || node.status === "REGULATED";
        const borderClass = isOk ? "border-green-200 bg-green-50" : (node.status === "INFO" ? "border-blue-100 bg-blue-50" : "border-amber-200 bg-amber-50");
        const iconName = isOk ? "check_circle" : (node.status === "CONFLICT" || node.status === "SUPPRESSED" || node.status === "EXHAUSTED" ? "cancel" : "info");
        const iconClass = isOk ? "text-green-700" : (node.status === "CONFLICT" || node.status === "SUPPRESSED" || node.status === "EXHAUSTED" ? "text-red-600" : "text-amber-700");
        return `
            <div class="flex items-start gap-3 p-3 rounded-lg border ${borderClass}">
                <span class="material-symbols-outlined text-sm font-bold mt-0.5 ${iconClass}">${iconName}</span>
                <div>
                    <div class="font-label-md font-bold text-on-surface text-[13px]">
                        <span class="text-[11px] font-data-mono text-on-surface-variant mr-2">#${node.step}</span>
                        ${node.title}
                        <span class="ml-1 px-1.5 py-0.5 rounded text-[10px] font-bold ${isOk ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">${node.status}</span>
                    </div>
                    <div class="text-body-sm text-on-surface-variant mt-0.5">${node.detail}</div>
                </div>
            </div>
        `;
    }).join("");

    modal.innerHTML = `
        <div class="bg-surface-container-lowest border border-outline rounded-xl max-w-2xl w-full p-lg shadow-2xl overflow-hidden animate-scale-up" style="max-height:90vh;overflow-y:auto;">
            <div class="flex justify-between items-center border-b border-outline-variant pb-md mb-md">
                <div>
                    <h3 class="font-headline-md text-primary font-bold">Optimization Decision Audit: ${auditData.job_code}</h3>
                    <div class="mt-1 flex items-center gap-1">${statusPill}${reasonCodeBadge}</div>
                    ${windowInfo}
                </div>
                <button onclick="document.getElementById('explainer-modal').remove()" class="p-1 rounded-full hover:bg-surface text-on-surface">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
            <div class="mb-md p-3.5 rounded-lg bg-surface border border-outline-variant text-body-md text-on-surface leading-relaxed">
                <strong>Mathematical Solver Rationale:</strong> ${auditData.summary}
            </div>
            ${shadowInfo}
            <div class="space-y-3 mb-md">
                ${treeHtml}
            </div>
            ${failedWindowsHtml}
            ${nextWindowHtml}
            ${auditData.suggested_alternative && !isSched ? `
                <div class="mt-3 p-2.5 rounded bg-slate-50 border border-outline-variant text-body-sm text-on-surface-variant italic">
                    <strong class="text-on-surface not-italic">Suggested Action:</strong> ${auditData.suggested_alternative}
                </div>` : ""}
            <div class="flex justify-end gap-2 pt-sm border-t border-outline-variant mt-md">
                <button onclick="document.getElementById('explainer-modal').remove()" class="px-4 py-2 bg-primary text-on-primary rounded font-label-md hover:bg-opacity-90">Close Audit</button>
            </div>
        </div>
    `;
}


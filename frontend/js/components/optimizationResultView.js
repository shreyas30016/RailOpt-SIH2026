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

    const isSched = auditData.status === "SCHEDULED";
    const statusPill = isSched 
        ? `<span class="px-2.5 py-0.5 rounded text-[11px] font-bold bg-green-100 text-green-800">SCHEDULED</span>`
        : `<span class="px-2.5 py-0.5 rounded text-[11px] font-bold bg-red-100 text-red-800">DEFERRED</span>`;

    modal.innerHTML = `
        <div class="bg-surface-container-lowest border border-outline rounded-xl max-w-2xl w-full p-lg shadow-2xl overflow-hidden animate-scale-up">
            <div class="flex justify-between items-center border-b border-outline-variant pb-md mb-md">
                <div>
                    <h3 class="font-headline-md text-primary font-bold">Optimization Decision Audit: ${auditData.job_code}</h3>
                    <div class="mt-1">${statusPill}</div>
                </div>
                <button onclick="document.getElementById('explainer-modal').remove()" class="p-1 rounded-full hover:bg-surface text-on-surface">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
            <div class="mb-md p-3.5 rounded-lg bg-surface border border-outline-variant text-body-md text-on-surface leading-relaxed">
                <strong>Mathematical Solver Rationale:</strong> ${auditData.summary}
            </div>
            <div class="space-y-3 mb-md max-h-72 overflow-y-auto pr-1">
                ${auditData.reasoning_tree.map(node => `
                    <div class="flex items-start gap-3 p-3 rounded-lg border ${node.status === 'PASSED' || node.status === 'OPTIMIZED' ? 'border-green-200 bg-green-50' : 'border-amber-200 bg-amber-50'}">
                        <span class="material-symbols-outlined text-sm font-bold mt-0.5 ${node.status === 'PASSED' || node.status === 'OPTIMIZED' ? 'text-green-700' : 'text-amber-700'}">
                            ${node.status === 'PASSED' || node.status === 'OPTIMIZED' ? 'check_circle' : 'info'}
                        </span>
                        <div>
                            <div class="font-label-md font-bold text-on-surface text-[13px]">${node.title}</div>
                            <div class="text-body-sm text-on-surface-variant mt-0.5">${node.detail}</div>
                        </div>
                    </div>
                `).join("")}
            </div>
            <div class="flex justify-end gap-2 pt-sm border-t border-outline-variant">
                <button onclick="document.getElementById('explainer-modal').remove()" class="px-4 py-2 bg-primary text-on-primary rounded font-label-md hover:bg-opacity-90">Close Audit</button>
            </div>
        </div>
    `;
}

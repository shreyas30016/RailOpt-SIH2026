/**
 * Reusable Maintenance Job Row & Card Component
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
        : (job.status === 'APPROVED' ? 'bg-blue-100 text-blue-800' : 'bg-amber-50 text-amber-800');

    return `
        <tr class="border-b border-outline-variant border-opacity-30 hover:bg-surface transition-colors cursor-pointer" onclick="window.showJobExplanation && window.showJobExplanation('${job.job_code || job.id}')">
            <td class="p-table-cell-padding font-data-mono text-primary font-bold">
                <span class="hover:underline">${job.job_code || job.id}</span>
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
        </tr>
    `;
}

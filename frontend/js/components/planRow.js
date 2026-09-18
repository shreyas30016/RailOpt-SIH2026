/**
 * Reusable Scheduled Block Row & Conflict Card Components
 */

export function createScheduledBlockRow(b) {
    const isShadow = b.is_shadow_block || (b.synergy_label && b.synergy_label.includes("SHADOW"));
    return `
        <tr class="border-b border-outline-variant/30 hover:bg-surface transition-colors cursor-pointer" onclick="window.location.href='/gantt-view'">
            <td class="p-[table-cell-padding] font-data-mono font-bold text-primary">${b.block_id || b.id || 'BLK-01'}</td>
            <td class="p-[table-cell-padding] font-body-sm font-medium">
                <div class="font-bold text-on-surface">${b.title || b.job_title || b.job_code || 'Corridor Track Block'}</div>
                <div class="text-[11px] text-on-surface-variant font-data-mono">${b.department_code || b.department || 'ENG'}</div>
            </td>
            <td class="p-[table-cell-padding] font-data-mono text-[12px]">${b.section_code || b.section || 'NDLS-TKD'} <span class="text-outline">(${b.track_line || 'UP'})</span></td>
            <td class="p-[table-cell-padding] font-data-mono font-semibold text-right">${b.start_time_str || b.start_time || '01:00'}</td>
            <td class="p-[table-cell-padding] font-data-mono font-semibold text-right">${b.end_time_str || b.end_time || '03:30'}</td>
            <td class="p-[table-cell-padding] font-data-mono text-on-surface-variant text-right font-bold">${b.duration_minutes || 150}m</td>
            <td class="p-[table-cell-padding] text-center">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${isShadow ? 'bg-indigo-100 text-indigo-900' : 'bg-slate-100 text-slate-700'}">
                    ${isShadow ? '⚡ SHADOW' : 'STANDALONE'}
                </span>
            </td>
            <td class="p-[table-cell-padding] text-center">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                    ${b.status || 'SCHEDULED'}
                </span>
            </td>
        </tr>
    `;
}

export { createConflictCard } from "./conflictCard.js";

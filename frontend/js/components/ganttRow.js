/**
 * Reusable Gantt Track Timeline & Train Movement Row Component
 */

export function createGanttRow({ label, track_line_code, blocks = [], totalHours = 24 }) {
    const blockElements = blocks.map(b => {
        const leftPct = (b.start_minute / (totalHours * 60)) * 100;
        const widthPct = Math.max(1.8, ((b.end_minute - b.start_minute) / (totalHours * 60)) * 100);
        
        let bgColor = b.color || '#003366';
        if (b.is_shadow) bgColor = '#059669'; // High-contrast green for shadow blocks

        return `
            <div class="absolute top-1 bottom-1 rounded px-2 py-1 text-white text-[11px] font-bold shadow-md overflow-hidden flex items-center justify-between cursor-pointer transition-transform hover:scale-[1.02] hover:z-20 hover:ring-2 hover:ring-offset-1 hover:ring-white"
                 style="left: ${leftPct}%; width: ${widthPct}%; background-color: ${bgColor};"
                 onclick="window.showJobExplanation && window.showJobExplanation('${b.job_code}')"
                 title="${b.job_code}: ${b.title || ''} (${b.start_time_str} - ${b.end_time_str})">
                <span class="truncate tracking-tight">${b.job_code} (${b.department})</span>
                ${b.is_shadow ? '<span class="material-symbols-outlined text-[14px] flex-shrink-0" title="Co-located Shadow Block">link</span>' : ''}
            </div>
        `;
    }).join("");

    // Hourly vertical grid lines
    const gridLines = Array.from({ length: totalHours }).map((_, i) => `
        <div class="absolute top-0 bottom-0 border-r border-outline-variant border-opacity-20 pointer-events-none" style="left: ${(i / totalHours) * 100}%;"></div>
    `).join("");

    return `
        <div class="flex border-b border-outline-variant border-opacity-40 min-h-[52px] hover:bg-surface transition-colors">
            <div class="w-64 p-2.5 font-data-mono text-body-sm font-bold text-primary border-r border-outline-variant flex items-center bg-surface-container-low select-none">
                <span class="truncate">${label || track_line_code}</span>
            </div>
            <div class="flex-1 relative bg-surface-container-lowest overflow-hidden">
                ${gridLines}
                ${blockElements}
            </div>
        </div>
    `;
}

export function createGanttTrainRow({ train, totalHours = 24 }) {
    const leftPct = (train.departure_minute / (totalHours * 60)) * 100;
    const durMin = Math.max(25, train.arrival_minute - train.departure_minute);
    const widthPct = Math.max(2.5, (durMin / (totalHours * 60)) * 100);

    const isDelayed = train.delay_minutes > 0;
    const isPremium = train.train_type === "VANDE_BHARAT" || train.train_type === "RAJDHANI";
    const bgClass = isPremium ? 'bg-indigo-600' : (train.train_type === 'FREIGHT' ? 'bg-slate-700' : 'bg-blue-600');
    const delayIndicator = isDelayed ? `<span class="bg-rose-500 text-white px-1 rounded text-[9px] ml-1">+${train.delay_minutes}m</span>` : '';

    const gridLines = Array.from({ length: totalHours }).map((_, i) => `
        <div class="absolute top-0 bottom-0 border-r border-outline-variant border-opacity-20 pointer-events-none" style="left: ${(i / totalHours) * 100}%;"></div>
    `).join("");

    return `
        <div class="flex border-b border-outline-variant border-opacity-30 min-h-[42px] bg-slate-50/50 hover:bg-slate-100/60 transition-colors">
            <div class="w-64 p-2 font-data-mono text-[12px] font-semibold text-on-surface border-r border-outline-variant flex items-center gap-1.5 bg-surface-container-low select-none">
                <span class="material-symbols-outlined text-[16px] text-primary">train</span>
                <span class="truncate font-bold">${train.train_number}</span>
                <span class="text-[11px] text-on-surface-variant truncate">(${train.train_name})</span>
            </div>
            <div class="flex-1 relative overflow-hidden">
                ${gridLines}
                <div class="absolute top-1.5 bottom-1.5 rounded px-2 py-0.5 text-white text-[11px] font-bold shadow-sm overflow-hidden flex items-center justify-between cursor-pointer ${bgClass} hover:brightness-110"
                     style="left: ${leftPct}%; width: ${widthPct}%;"
                     title="Train #${train.train_number} (${train.train_name}): ${train.departure_time_str} - ${train.arrival_time_str} (${train.status})">
                    <span class="truncate">${train.train_number} ${train.direction === 'UP' ? '↑' : '↓'}</span>
                    ${delayIndicator}
                </div>
            </div>
        </div>
    `;
}

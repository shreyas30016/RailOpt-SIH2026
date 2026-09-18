/**
 * Reusable What-If Scenario Comparison Component for RailOpt
 * Handles Before vs After Schedule Diffs, Change Detection Badges,
 * and Visual Comparative Timeline Bars.
 */

export function createWhatIfDeltaBadge(value, unit = "", isHigherBetter = true) {
    const isZero = value === 0;
    const isPositive = value > 0;
    const isGood = isHigherBetter ? isPositive : !isPositive;
    
    const colorClass = isZero 
        ? "text-slate-600 bg-slate-100 border-slate-200" 
        : (isGood ? "text-emerald-800 bg-emerald-100 border-emerald-200" : "text-rose-800 bg-rose-100 border-rose-200");

    const prefix = isPositive ? "+" : "";

    return `
        <span class="px-2.5 py-0.5 rounded-full text-[12px] font-bold border ${colorClass}">
            ${prefix}${value}${unit ? ' ' + unit : ''}
        </span>
    `;
}

export function createWhatIfAlert(alertText, isWarning = true) {
    const bgClass = isWarning ? "bg-amber-50 border-amber-200 text-amber-900" : "bg-emerald-50 border-emerald-200 text-emerald-900";
    const icon = isWarning ? "warning" : "check_circle";
    const iconColor = isWarning ? "text-amber-700" : "text-emerald-700";

    return `
        <div class="p-3 rounded-lg border ${bgClass} font-medium flex items-start gap-2.5 shadow-sm">
            <span class="material-symbols-outlined ${iconColor} text-[18px] flex-shrink-0 mt-0.5">${icon}</span>
            <span class="text-body-sm leading-relaxed text-[12px]">${alertText}</span>
        </div>
    `;
}

/**
 * Compare baseline and simulated blocks to produce detailed change records.
 */
export function computeScheduleChanges(baselineBlocks = [], newBlocks = []) {
    const baseMap = new Map();
    baselineBlocks.forEach(b => baseMap.set(b.job_code || b.jobId, b));

    const newMap = new Map();
    newBlocks.forEach(b => newMap.set(b.job_code || b.jobId, b));

    const allJobCodes = Array.from(new Set([...baseMap.keys(), ...newMap.keys()]));
    const changes = [];

    allJobCodes.forEach(jobCode => {
        const base = baseMap.get(jobCode);
        const sim = newMap.get(jobCode);

        if (!base && sim) {
            changes.push({
                job_code: jobCode,
                title: sim.title || jobCode,
                department_code: sim.department_code || sim.department || "ENG",
                section_code: sim.section_code || sim.section || "FDB-PWL",
                change_type: "NEW",
                badge_class: "bg-emerald-100 text-emerald-800 border-emerald-200",
                badge_label: "NEW INJECTED",
                before_window: "—",
                after_window: `${sim.start_time_str || formatMin(sim.start_minute)}–${sim.end_time_str || formatMin(sim.end_minute)}`,
                duration_minutes: sim.duration_minutes,
                impact_detail: "Newly scheduled emergency block",
                job: sim
            });
        } else if (base && !sim) {
            changes.push({
                job_code: jobCode,
                title: base.title || jobCode,
                department_code: base.department_code || base.department || "ENG",
                section_code: base.section_code || base.section || "FDB-PWL",
                change_type: "DEFERRED",
                badge_class: "bg-red-100 text-red-800 border-red-200",
                badge_label: "DEFERRED",
                before_window: `${base.start_time_str || formatMin(base.start_minute)}–${base.end_time_str || formatMin(base.end_minute)}`,
                after_window: "Deferred to next lull",
                duration_minutes: base.duration_minutes,
                impact_detail: "Preempted by disruption / lack of feasible window",
                job: base
            });
        } else if (base && sim) {
            const startDiff = (sim.start_minute || 0) - (base.start_minute || 0);
            const isMoved = Math.abs(startDiff) >= 5;

            if (isMoved) {
                const shiftSign = startDiff > 0 ? `+${startDiff}m` : `${startDiff}m`;
                changes.push({
                    job_code: jobCode,
                    title: sim.title || base.title || jobCode,
                    department_code: sim.department_code || base.department_code || "ENG",
                    section_code: sim.section_code || base.section_code || "FDB-PWL",
                    change_type: "MOVED",
                    badge_class: "bg-amber-100 text-amber-800 border-amber-200",
                    badge_label: `MOVED (${shiftSign})`,
                    before_window: `${base.start_time_str || formatMin(base.start_minute)}–${base.end_time_str || formatMin(base.end_minute)}`,
                    after_window: `${sim.start_time_str || formatMin(sim.start_minute)}–${sim.end_time_str || formatMin(sim.end_minute)}`,
                    duration_minutes: sim.duration_minutes,
                    impact_detail: `Rescheduled start time shifted by ${Math.abs(startDiff)} minutes`,
                    job: sim
                });
            } else {
                changes.push({
                    job_code: jobCode,
                    title: sim.title || base.title || jobCode,
                    department_code: sim.department_code || base.department_code || "ENG",
                    section_code: sim.section_code || base.section_code || "FDB-PWL",
                    change_type: "UNCHANGED",
                    badge_class: "bg-slate-100 text-slate-700 border-slate-200",
                    badge_label: "UNCHANGED",
                    before_window: `${base.start_time_str || formatMin(base.start_minute)}–${base.end_time_str || formatMin(base.end_minute)}`,
                    after_window: `${sim.start_time_str || formatMin(sim.start_minute)}–${sim.end_time_str || formatMin(sim.end_minute)}`,
                    duration_minutes: sim.duration_minutes,
                    impact_detail: "Window unaffected by scenario disruption",
                    job: sim
                });
            }
        }
    });

    // Sort: NEW & MOVED & DEFERRED first, then UNCHANGED
    const sortPriority = { "NEW": 1, "DEFERRED": 2, "MOVED": 3, "UNCHANGED": 4 };
    changes.sort((a, b) => (sortPriority[a.change_type] || 5) - (sortPriority[b.change_type] || 5));

    return changes;
}

/**
 * Format integer minutes (0-1440) to HH:MM format
 */
function formatMin(m) {
    if (m === undefined || m === null) return "--:--";
    const h = Math.floor(m / 60) % 24;
    const min = m % 60;
    return `${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}`;
}

/**
 * Render the Before vs After Schedule Diff comparison table
 */
export function renderScheduleDiffTable(changes = []) {
    if (changes.length === 0) {
        return `<div class="p-6 text-center text-on-surface-variant font-medium">No schedule changes detected for this scenario.</div>`;
    }

    const deptBg = {
        ENG: "bg-blue-100 text-blue-800",
        TRD: "bg-amber-100 text-amber-800",
        S_T: "bg-cyan-100 text-cyan-800",
        MECH: "bg-slate-100 text-slate-800"
    };

    return `
        <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse dense-table text-body-sm">
                <thead class="bg-surface-container-low border-b border-outline-variant text-[11px] font-bold text-on-surface-variant uppercase font-label-md">
                    <tr>
                        <th class="p-2">Status</th>
                        <th class="p-2">Job Code</th>
                        <th class="p-2">Dept</th>
                        <th class="p-2">Section</th>
                        <th class="p-2">Baseline Window</th>
                        <th class="p-2 text-primary font-bold">Re-Optimized Window</th>
                        <th class="p-2">Duration</th>
                        <th class="p-2">Impact / Note</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-outline-variant/40 bg-surface-container-lowest font-data-mono text-[12px]">
                    ${changes.map(c => `
                        <tr class="hover:bg-surface-container-low/50 transition-colors ${c.change_type === 'DEFERRED' ? 'bg-red-50/30' : (c.change_type === 'NEW' ? 'bg-emerald-50/30' : '')}">
                            <td class="p-2">
                                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold border ${c.badge_class}">
                                    ${c.badge_label}
                                </span>
                            </td>
                            <td class="p-2 font-bold text-primary">
                                <span class="hover:underline cursor-pointer" onclick="window.showJobExplanation && window.showJobExplanation('${c.job_code}')" title="View Decision Explanation">
                                    ${c.job_code}
                                </span>
                            </td>
                            <td class="p-2">
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold ${deptBg[c.department_code] || 'bg-slate-100 text-slate-800'}">
                                    ${c.department_code}
                                </span>
                            </td>
                            <td class="p-2 font-semibold text-on-surface">${c.section_code}</td>
                            <td class="p-2 text-on-surface-variant line-through opacity-80 ${c.change_type === 'UNCHANGED' ? 'no-underline opacity-100' : ''}">${c.before_window}</td>
                            <td class="p-2 font-bold text-primary">${c.after_window}</td>
                            <td class="p-2">${c.duration_minutes}m</td>
                            <td class="p-2 font-body-sm text-[11px] text-on-surface-variant">${c.impact_detail}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        </div>
    `;
}

/**
 * Render visual comparative timeline blocks for Baseline vs Re-optimized schedule
 */
export function renderComparativeTimelineBars(baselineBlocks = [], newBlocks = []) {
    const renderTrackBlocks = (blocks, title, isReopt = false) => {
        const sections = ["NDLS-TKD", "TKD-FDB", "FDB-PWL", "PWL-KDS", "KDS-MTJ", "MTJ-AGC"];
        const deptColors = {
            ENG: "bg-blue-700 text-white",
            TRD: "bg-amber-600 text-white",
            S_T: "bg-cyan-700 text-white",
            MECH: "bg-slate-700 text-white"
        };

        return `
            <div class="flex-1 bg-surface-container-lowest p-3 rounded-lg border ${isReopt ? 'border-primary border-opacity-40 shadow-sm' : 'border-outline-variant/60'}">
                <div class="flex justify-between items-center mb-2 pb-1 border-b border-outline-variant">
                    <span class="font-label-md text-[11px] uppercase font-bold ${isReopt ? 'text-primary' : 'text-on-surface-variant'}">${title}</span>
                    <span class="text-[10px] font-data-mono text-outline">${blocks.length} blocks scheduled</span>
                </div>
                <div class="space-y-2">
                    ${sections.map(sec => {
                        const secBlocks = blocks.filter(b => (b.section_code || b.section) === sec);
                        return `
                            <div class="flex items-center gap-2 text-[11px]">
                                <span class="w-16 font-data-mono text-[10px] font-bold text-outline truncate">${sec}</span>
                                <div class="flex-1 bg-surface-container-low rounded h-6 relative overflow-hidden flex items-center px-1 gap-1">
                                    ${secBlocks.map(b => {
                                        const startMin = b.start_minute || 0;
                                        const dur = b.duration_minutes || 180;
                                        const leftPct = Math.min(90, Math.max(0, (startMin / 1440) * 100));
                                        const widthPct = Math.min(100 - leftPct, Math.max(8, (dur / 1440) * 100));
                                        const dept = b.department_code || b.department || "ENG";

                                        return `
                                            <div class="absolute h-5 rounded px-1.5 flex items-center text-[10px] font-bold font-data-mono shadow-xs truncate cursor-pointer hover:opacity-90 transition-opacity ${deptColors[dept] || 'bg-primary text-white'}"
                                                 style="left: ${leftPct}%; width: ${widthPct}%;"
                                                 title="${b.job_code} (${dept}): ${b.start_time_str || formatMin(startMin)}–${b.end_time_str || formatMin(startMin + dur)} (${dur}m)"
                                                 onclick="window.showJobExplanation && window.showJobExplanation('${b.job_code}')">
                                                ${b.job_code.replace('JOB-', '')}
                                            </div>
                                        `;
                                    }).join("")}
                                </div>
                            </div>
                        `;
                    }).join("")}
                </div>
            </div>
        `;
    };

    return `
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-md">
            ${renderTrackBlocks(baselineBlocks, "Baseline Schedule (Pre-Disruption)", false)}
            ${renderTrackBlocks(newBlocks, "Re-Optimized Schedule (Post-Disruption)", true)}
        </div>
    `;
}

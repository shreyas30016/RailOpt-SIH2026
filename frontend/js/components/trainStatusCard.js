/**
 * Reusable Live Train Status Component for Dashboard & Timeline
 * Strictly preserves Stitch design tokens and provides clear Data Honesty labels.
 */

export function createLiveTrainCard(train) {
    const isDelayed = train.delay_minutes > 0;
    const isFreight = train.train_type === "FREIGHT";
    
    let statusPill = "";
    if (train.delay_minutes === 0) {
        statusPill = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">ON TIME</span>`;
    } else if (isFreight) {
        statusPill = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">+${train.delay_minutes}m (REGULATED)</span>`;
    } else {
        statusPill = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">+${train.delay_minutes}m DELAY</span>`;
    }

    const typeBadge = train.train_type === "VANDE_BHARAT" || train.train_type === "RAJDHANI"
        ? `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-900">PREMIUM</span>`
        : (train.train_type === "FREIGHT" ? `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-800">FREIGHT</span>` : `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">EXP</span>`);

    return `
        <div class="p-3 rounded-lg border border-outline-variant bg-surface hover:bg-surface-container-low transition-colors shadow-sm">
            <div class="flex justify-between items-start mb-1.5">
                <div class="flex items-center gap-1.5">
                    <span class="font-data-mono font-bold text-primary text-[13px]">${train.train_id}</span>
                    <span class="font-headline-sm font-semibold text-on-surface text-[13px] truncate max-w-[130px]">${train.train_name}</span>
                    ${typeBadge}
                </div>
                <div>${statusPill}</div>
            </div>
            <div class="text-[12px] text-on-surface-variant flex items-center justify-between mt-1">
                <div class="flex items-center gap-1 truncate">
                    <span class="material-symbols-outlined text-[14px] text-outline">location_on</span>
                    <span class="truncate">${train.current_location}</span>
                </div>
                <div class="font-data-mono font-semibold text-primary text-[11px] flex-shrink-0 ml-2">
                    → ${train.next_location}
                </div>
            </div>
        </div>
    `;
}

export function createLiveTrainFeedContainer(feedData) {
    const isLive = !feedData.isFallback;
    const sourceBadge = isLive
        ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span> Live/Public Train Data</span>`
        : `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 flex items-center gap-1">Synthetic Demo Data (Fallback)</span>`;

    const cardsHtml = (feedData.movements || []).slice(0, 4).map(createLiveTrainCard).join("");

    return `
        <div class="bg-surface-container-lowest border border-outline-variant rounded-lg p-md shadow-[0_4px_6px_rgba(0,0,0,0.02)]">
            <div class="flex justify-between items-center mb-sm border-b border-outline-variant pb-2">
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary text-[20px]">train</span>
                    <span class="font-label-md text-label-md text-primary uppercase font-bold tracking-wider">Live Train Movements</span>
                </div>
                <div class="flex items-center gap-2">
                    ${sourceBadge}
                    <span class="text-[11px] text-on-surface-variant font-data-mono">Updated: ${feedData.lastUpdated}</span>
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                ${cardsHtml}
            </div>
        </div>
    `;
}

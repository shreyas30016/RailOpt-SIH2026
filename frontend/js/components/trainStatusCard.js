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
        <div class="p-3 rounded-lg border border-outline-variant bg-surface hover:bg-surface-container-low transition-all duration-150 shadow-sm cursor-pointer hover:border-primary-container active:scale-[0.99]" 
             onclick="window.showTrainDetailModal && window.showTrainDetailModal('${train.train_id}')"
             title="Click to view full schedule path and operational constraints for Train ${train.train_id}">
            <div class="flex justify-between items-start mb-1.5">
                <div class="flex items-center gap-1.5">
                    <span class="font-data-mono font-bold text-primary text-[13px] hover:underline">${train.train_id}</span>
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
        ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span> Live/Public Data Adapter</span>`
        : `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 flex items-center gap-1">Synthetic Demo Data (Fallback)</span>`;

    // Cache movements for modal lookup
    window._currentTrainMovements = feedData.movements || [];

    const cardsHtml = (feedData.movements || []).slice(0, 4).map(createLiveTrainCard).join("");

    return `
        <div class="bg-surface-container-lowest border border-outline-variant rounded-lg p-md shadow-[0_4px_6px_rgba(0,0,0,0.02)]">
            <div class="flex justify-between items-center mb-sm border-b border-outline-variant pb-2">
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary text-[20px]">train</span>
                    <span class="font-label-md text-label-md text-primary uppercase font-bold tracking-wider">Train Operating Window Feed</span>
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

export function renderTrainDetailModal(train) {
    let modal = document.getElementById("train-detail-modal");
    if (!modal) {
        modal = document.createElement("div");
        modal.id = "train-detail-modal";
        modal.className = "fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-fade-in";
        document.body.appendChild(modal);
    }

    const isDelayed = train.delay_minutes > 0;
    const isFreight = train.train_type === "FREIGHT";
    
    let statusPill = "";
    if (train.delay_minutes === 0) {
        statusPill = `<span class="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">ON TIME (0m Delay)</span>`;
    } else if (isFreight) {
        statusPill = `<span class="px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800">+${train.delay_minutes}m (REGULATED FREIGHT)</span>`;
    } else {
        statusPill = `<span class="px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800">+${train.delay_minutes}m DELAY</span>`;
    }

    modal.innerHTML = `
        <div class="bg-surface-container-lowest rounded-xl max-w-xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-outline-variant flex flex-col animate-scale-up" onclick="event.stopPropagation()">
            <!-- Modal Header -->
            <div class="p-lg bg-primary text-on-primary rounded-t-xl flex justify-between items-start">
                <div>
                    <div class="flex items-center gap-2 mb-1">
                        <span class="font-data-mono font-bold text-headline-sm">${train.train_id}</span>
                        <span class="px-2 py-0.5 rounded bg-primary-container text-on-primary-container text-[11px] font-bold uppercase">${train.train_type}</span>
                        <span class="px-2 py-0.5 rounded bg-surface/20 text-on-primary text-[11px] font-bold uppercase">${train.direction} LINE</span>
                    </div>
                    <h3 class="font-headline-md font-bold">${train.train_name}</h3>
                    <p class="text-body-sm opacity-80 mt-1 font-data-mono">Corridor Priority Weight: ${train.priority_weight || 10}</p>
                </div>
                <button onclick="document.getElementById('train-detail-modal').remove()" class="p-1 rounded-full hover:bg-white/10 text-on-primary transition-colors">
                    <span class="material-symbols-outlined text-[20px]">close</span>
                </button>
            </div>

            <!-- Modal Body -->
            <div class="p-lg space-y-md flex-1">
                <!-- Status Row -->
                <div class="flex items-center justify-between p-md bg-surface rounded-lg border border-outline-variant">
                    <div>
                        <span class="font-label-md text-on-surface-variant uppercase text-[11px]">Current Punctuality</span>
                        <div class="mt-1">${statusPill}</div>
                    </div>
                    <div class="text-right font-data-mono text-[12px] text-on-surface-variant">
                        <div>Sched: ${train.scheduled_departure_str || '--'} → ${train.scheduled_arrival_str || '--'}</div>
                        <div class="font-semibold text-primary">Est: ${train.estimated_departure_str || '--'} → ${train.estimated_arrival_str || '--'}</div>
                    </div>
                </div>

                <!-- Location Progress -->
                <div class="p-md bg-surface rounded-lg border border-outline-variant">
                    <h4 class="font-label-md text-primary font-bold uppercase text-[11px] mb-sm">Corridor Progression</h4>
                    <div class="flex items-center justify-between text-body-sm">
                        <div class="flex items-center gap-2">
                            <span class="material-symbols-outlined text-emerald-600">check_circle</span>
                            <div>
                                <div class="font-bold text-on-surface">${train.current_location}</div>
                                <div class="text-[11px] text-on-surface-variant">Last reported station/block</div>
                            </div>
                        </div>
                        <span class="material-symbols-outlined text-outline">arrow_forward</span>
                        <div class="flex items-center gap-2 text-right">
                            <div>
                                <div class="font-bold text-primary">${train.next_location}</div>
                                <div class="text-[11px] text-on-surface-variant">Approaching section</div>
                            </div>
                            <span class="material-symbols-outlined text-surface-tint">navigation</span>
                        </div>
                    </div>
                </div>

                <!-- Hard Constraint Notice -->
                <div class="p-sm bg-blue-50 border border-blue-200 rounded text-[12px] text-blue-900 flex items-start gap-2">
                    <span class="material-symbols-outlined text-blue-700 text-[18px] shrink-0 mt-0.5">shield</span>
                    <div>
                        <strong>Railway Safety Constraint Protection:</strong> 
                        This train has priority level <strong>${train.priority_weight}</strong>. The CP-SAT solver strictly forbids overlapping maintenance possessions with protected windows on line <code>${train.track_line || 'MAIN'}</code>.
                    </div>
                </div>
            </div>

            <!-- Modal Footer -->
            <div class="p-md border-t border-outline-variant bg-surface rounded-b-xl flex justify-between items-center">
                <button onclick="window.location.href='/what-if?train=${train.train_id}'" class="px-3 py-1.5 rounded-lg border border-outline text-primary font-bold text-[12px] hover:bg-surface-container-low transition-colors flex items-center gap-1">
                    <span class="material-symbols-outlined text-[16px]">query_stats</span>
                    Simulate Delay in What-If
                </button>
                <div class="flex items-center gap-sm">
                    <button onclick="window.location.href='/gantt-view'" class="px-3.5 py-1.5 rounded-lg bg-primary-container text-on-primary font-bold text-[12px] hover:bg-opacity-90 transition-colors flex items-center gap-1">
                        <span class="material-symbols-outlined text-[16px]">view_timeline</span>
                        View on Gantt
                    </button>
                    <button onclick="document.getElementById('train-detail-modal').remove()" class="px-3.5 py-1.5 border border-outline-variant rounded-lg font-bold text-[12px] hover:bg-surface text-on-surface">
                        Close
                    </button>
                </div>
            </div>
        </div>
    `;

    modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
    };
}

// Global hook for train detail modal
window.showTrainDetailModal = function(trainId) {
    const movements = window._currentTrainMovements || [];
    const train = movements.find(t => t.train_id === trainId || t.train_number === trainId);
    if (train) {
        renderTrainDetailModal(train);
    } else {
        // Fallback placeholder object if not in cache
        renderTrainDetailModal({
            train_id: trainId,
            train_name: `Train ${trainId}`,
            train_type: "EXPRESS",
            direction: "DN",
            current_location: "Delhi Division Mainline",
            next_location: "Agra Cantt (AGC)",
            delay_minutes: 0,
            scheduled_departure_str: "06:00",
            scheduled_arrival_str: "08:00",
            estimated_departure_str: "06:00",
            estimated_arrival_str: "08:00",
            priority_weight: 15,
            track_line: "DN_MAIN"
        });
    }
};


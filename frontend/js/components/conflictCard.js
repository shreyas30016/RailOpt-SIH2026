/**
 * Reusable Conflict & Resolution Card Component
 */

export function createConflictCard(conflict) {
    const isResolved = conflict.severity === "RESOLVED" || conflict.severity === "PREVENTED";
    const bgClass = isResolved ? "bg-emerald-50 border-emerald-200" : "bg-amber-50 border-amber-200";
    const textClass = isResolved ? "text-emerald-900" : "text-amber-900";
    const icon = isResolved ? "check_circle" : "warning";
    const iconColor = isResolved ? "text-emerald-700" : "text-amber-700";

    return `
        <div class="p-3.5 rounded-lg border ${bgClass} ${textClass} mb-2.5 shadow-sm">
            <div class="flex items-start gap-2.5">
                <span class="material-symbols-outlined ${iconColor} text-[20px] flex-shrink-0 mt-0.5">${icon}</span>
                <div class="flex-1">
                    <div class="flex justify-between items-center mb-1">
                        <span class="font-data-mono font-bold text-[12px] uppercase tracking-wider">${conflict.type || conflict.conflictType}</span>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold ${isResolved ? 'bg-emerald-200 text-emerald-900' : 'bg-amber-200 text-amber-900'}">${conflict.severity}</span>
                    </div>
                    <div class="text-body-sm font-medium mb-1">${conflict.description}</div>
                    ${conflict.resolution || conflict.resolutionApplied ? `
                        <div class="text-[12px] opacity-85 font-medium border-t border-current border-opacity-20 pt-1 mt-1">
                            <strong>Resolution:</strong> ${conflict.resolution || conflict.resolutionApplied}
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

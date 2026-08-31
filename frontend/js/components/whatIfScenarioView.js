/**
 * Reusable What-If Scenario Comparison Component
 */

export function createWhatIfDeltaBadge(value, unit = "", isHigherBetter = true) {
    const isZero = value === 0;
    const isPositive = value > 0;
    const isGood = isHigherBetter ? isPositive : !isPositive;
    
    const colorClass = isZero 
        ? "text-slate-600 bg-slate-100" 
        : (isGood ? "text-emerald-800 bg-emerald-100" : "text-rose-800 bg-rose-100");

    const prefix = isPositive ? "+" : "";

    return `
        <span class="px-2.5 py-1 rounded-full text-[12px] font-bold ${colorClass}">
            ${prefix}${value} ${unit}
        </span>
    `;
}

export function createWhatIfAlert(alertText, isWarning = true) {
    const bgClass = isWarning ? "bg-amber-50 border-amber-200 text-amber-900" : "bg-emerald-50 border-emerald-200 text-emerald-900";
    const icon = isWarning ? "warning" : "check_circle";
    const iconColor = isWarning ? "text-amber-700" : "text-emerald-700";

    return `
        <div class="p-3.5 rounded-lg border ${bgClass} font-medium mb-2.5 flex items-start gap-2.5 shadow-sm">
            <span class="material-symbols-outlined ${iconColor} text-[20px] flex-shrink-0 mt-0.5">${icon}</span>
            <span class="text-body-sm leading-relaxed">${alertText}</span>
        </div>
    `;
}

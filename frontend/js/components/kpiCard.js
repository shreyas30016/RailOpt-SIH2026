/**
 * Reusable KPI Metric Card Component
 * Conforms to Industrial Precision design system tokens
 */

export function createKPICard({
    title,
    value,
    subtitle = "",
    icon = "analytics",
    trend = null,
    colorVariant = "primary",
    borderColor = null
}) {
    const isError = colorVariant === "error";
    const textClass = isError ? "text-error" : "text-primary";
    const borderLeft = borderColor ? `<div class="absolute top-0 left-0 w-1 h-full" style="background-color: ${borderColor}"></div>` : "";
    
    let trendHtml = "";
    if (trend) {
        trendHtml = `
            <div class="mt-2 flex items-center gap-1 text-[12px] ${trend.isPositive ? 'text-surface-tint' : 'text-error'} font-medium">
                <span class="material-symbols-outlined text-[14px]">${trend.icon || (trend.isPositive ? 'arrow_upward' : 'arrow_downward')}</span>
                <span>${trend.text}</span>
            </div>
        `;
    } else if (subtitle) {
        trendHtml = `<div class="mt-2 text-[12px] text-on-surface-variant font-medium">${subtitle}</div>`;
    }

    return `
        <div class="bg-surface-container-lowest border border-outline-variant border-opacity-50 rounded-lg p-md shadow-[0_4px_6px_rgba(0,0,0,0.02)] relative overflow-hidden">
            ${borderLeft}
            <div class="flex justify-between items-start mb-sm ${borderColor ? 'pl-2' : ''}">
                <span class="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">${title}</span>
                <span class="material-symbols-outlined ${isError ? 'text-error opacity-70' : 'text-outline'} text-[20px]">${icon}</span>
            </div>
            <div class="flex items-end gap-sm ${borderColor ? 'pl-2' : ''}">
                <span class="font-headline-lg text-[32px] font-bold ${textClass}">${value}</span>
            </div>
            <div class="${borderColor ? 'pl-2' : ''}">
                ${trendHtml}
            </div>
        </div>
    `;
}

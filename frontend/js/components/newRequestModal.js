/**
 * New Maintenance Request Modal Component for RailOpt
 * Handles submission to POST /api/maintenance/requests with full field validation.
 */

import { dataService } from "../services/dataService.js";

export function renderNewRequestModal({ onSuccess } = {}) {
    let modal = document.getElementById("new-request-modal");
    if (!modal) {
        modal = document.createElement("div");
        modal.id = "new-request-modal";
        modal.className = "fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4 animate-fade-in";
        document.body.appendChild(modal);
    }

    let userRole = "CONTROLLER";
    try {
        const u = JSON.parse(localStorage.getItem("railopt_user") || "{}");
        if (u && u.role) userRole = u.role;
    } catch {}

    const roleDeptMap = {
        "ENGINEER": "ENG",
        "TRD_OFFICER": "TRD",
        "ST_OFFICER": "S_T"
    };
    const forcedDept = roleDeptMap[userRole] || null;
    // Job codes are assigned by the backend (unique, next-sequence per department).
    // The client never invents permanent codes like JOB-ENG-101.
    const defaultCode = "AUTO";

    modal.innerHTML = `
        <div class="bg-surface-container-lowest border border-outline rounded-xl max-w-2xl w-full p-lg shadow-2xl overflow-hidden animate-scale-up" style="max-height: 92vh; overflow-y: auto;">
            <!-- Modal Header -->
            <div class="flex justify-between items-center border-b border-outline-variant pb-md mb-md">
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary text-[24px]">add_circle</span>
                    <div>
                        <h3 class="font-headline-md text-headline-md text-on-surface font-bold">New Maintenance Possession Request</h3>
                        <p class="font-body-sm text-on-surface-variant text-[12px]">Submit track possession demand to the Railway Block Planning System</p>
                    </div>
                </div>
                <button id="btn-close-new-request-modal" class="p-1 rounded-full hover:bg-surface text-on-surface">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <!-- Error Banner -->
            <div id="modal-error-banner" class="hidden p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-body-sm mb-md flex items-center gap-2">
                <span class="material-symbols-outlined text-error text-[18px]">error</span>
                <span id="modal-error-msg">Please fill all required fields.</span>
            </div>

            <!-- Form -->
            <form id="form-new-request" class="flex flex-col gap-md">
                <!-- Row 1: Code & Department -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-md">
                    <div>
                        <label class="font-label-md text-on-surface-variant block mb-1 text-[11px] uppercase font-bold">Job Code</label>
                        <input id="req-job-code" class="w-full border border-outline-variant rounded-md px-3 py-1.5 font-data-mono text-body-sm text-on-surface focus:outline-none focus:border-primary bg-surface-container-lowest font-bold" type="text" value="${defaultCode}" readonly title="Auto-assigned by the backend to guarantee uniqueness">
                        <p class="text-[10px] text-on-surface-variant mt-1">Auto-assigned (e.g. JOB-ENG-107) — guaranteed unique.</p>
                    </div>
                    <div>
                        <label class="font-label-md text-on-surface-variant block mb-1 text-[11px] uppercase font-bold">Department *</label>
                        <select id="req-dept-code" class="w-full border border-outline-variant rounded-md px-3 py-1.5 font-body-sm text-on-surface focus:outline-none focus:border-primary bg-surface-container-lowest">
                            ${forcedDept === 'ENG' ? '<option value="ENG" selected>Civil Engineering (ENG / P-Way)</option>' :
                              forcedDept === 'TRD' ? '<option value="TRD" selected>Traction Distribution (TRD / OHE)</option>' :
                              forcedDept === 'S_T' ? '<option value="S_T" selected>Signal & Telecommunication (S&T)</option>' : `
                            <option value="ENG">Civil Engineering (ENG / P-Way)</option>
                            <option value="TRD">Traction Distribution (TRD / OHE)</option>
                            <option value="S_T">Signal & Telecommunication (S&T)</option>
                            <option value="MECH">Mechanical (MECH / C&W)</option>
                            `}
                        </select>
                    </div>
                    <div>
                        <label class="font-label-md text-on-surface-variant block mb-1 text-[11px] uppercase font-bold">Urgency *</label>
                        <select id="req-urgency" class="w-full border border-outline-variant rounded-md px-3 py-1.5 font-body-sm text-on-surface focus:outline-none focus:border-primary bg-surface-container-lowest font-semibold text-primary">
                            <option value="CRITICAL">🔴 Critical (Emergency/Urgent)</option>
                            <option value="HIGH">🟠 High Priority</option>
                            <option value="MEDIUM" selected>🟡 Medium Priority</option>
                            <option value="ROUTINE">🟢 Routine Maintenance</option>
                        </select>
                    </div>
                </div>

                <!-- Row 2: Title -->
                <div>
                    <label class="font-label-md text-on-surface-variant block mb-1 text-[11px] uppercase font-bold">Work Title / Activity *</label>
                    <input id="req-title" class="w-full border border-outline-variant rounded-md px-3 py-1.5 font-body-sm text-on-surface focus:outline-none focus:border-primary bg-surface-container-lowest font-medium" type="text" placeholder="e.g. Turnout Renewal & Deep Screening" required>
                </div>

                <!-- Row 3: Section, Track Line & Duration -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-md">
                    <div>
                        <label class="font-label-md text-on-surface-variant block mb-1 text-[11px] uppercase font-bold">Corridor Section *</label>
                        <select id="req-section-code" class="w-full border border-outline-variant rounded-md px-3 py-1.5 font-body-sm text-on-surface focus:outline-none focus:border-primary bg-surface-container-lowest">
                            <option value="NDLS-TKD">NDLS–TKD (New Delhi–Tuglakabad)</option>
                            <option value="TKD-FDB">TKD–FDB (Tuglakabad–Faridabad)</option>
                            <option value="FDB-PWL" selected>FDB–PWL (Faridabad–Palwal)</option>
                            <option value="PWL-KDS">PWL–KDS (Palwal–Kosi Kalan)</option>
                            <option value="KDS-MTJ">KDS–MTJ (Kosi Kalan–Mathura Jn)</option>
                            <option value="MTJ-AGC">MTJ–AGC (Mathura Jn–Agra Cantt)</option>
                        </select>
                    </div>
                    <div>
                        <label class="font-label-md text-on-surface-variant block mb-1 text-[11px] uppercase font-bold">Track Line *</label>
                        <select id="req-track-line" class="w-full border border-outline-variant rounded-md px-3 py-1.5 font-body-sm text-on-surface focus:outline-none focus:border-primary bg-surface-container-lowest font-data-mono">
                            <option value="UP_MAIN" selected>UP Main Line</option>
                            <option value="DN_MAIN">DN Main Line</option>
                            <option value="3RD_LINE">3rd Line (Freight Loop)</option>
                        </select>
                    </div>
                    <div>
                        <label class="font-label-md text-on-surface-variant block mb-1 text-[11px] uppercase font-bold">Duration (Minutes) *</label>
                        <input id="req-duration" class="w-full border border-outline-variant rounded-md px-3 py-1.5 font-data-mono text-body-sm text-on-surface focus:outline-none focus:border-primary bg-surface-container-lowest" type="number" min="15" max="720" value="180" required>
                    </div>
                </div>

                <!-- Row 4: Permitted Window -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-md p-3 bg-surface-container-low rounded-lg border border-outline-variant/50">
                    <div>
                        <label class="font-label-md text-on-surface-variant block mb-1 text-[11px] uppercase">Earliest Start Time</label>
                        <input id="req-start-time" class="w-full border border-outline-variant rounded-md px-3 py-1.5 font-data-mono text-body-sm text-on-surface focus:outline-none focus:border-primary bg-surface-container-lowest" type="time" value="01:00">
                    </div>
                    <div>
                        <label class="font-label-md text-on-surface-variant block mb-1 text-[11px] uppercase">Latest End Time</label>
                        <input id="req-end-time" class="w-full border border-outline-variant rounded-md px-3 py-1.5 font-data-mono text-body-sm text-on-surface focus:outline-none focus:border-primary bg-surface-container-lowest" type="time" value="06:00">
                    </div>
                </div>

                <!-- Row 5: Safety & Possession Requirements -->
                <div class="flex flex-col gap-2 p-3 bg-surface-container-low rounded-lg border border-outline-variant/50">
                    <span class="font-label-md text-on-surface-variant text-[11px] uppercase font-bold">Safety Isolation & Clearance Clearances</span>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-body-sm">
                        <label class="flex items-center gap-2 cursor-pointer select-none">
                            <input id="req-traffic-block" type="checkbox" class="rounded border-outline text-primary focus:ring-primary w-4 h-4" checked>
                            <span class="font-medium text-on-surface">Traffic Block (Halt)</span>
                        </label>
                        <label class="flex items-center gap-2 cursor-pointer select-none">
                            <input id="req-power-block" type="checkbox" class="rounded border-outline text-primary focus:ring-primary w-4 h-4">
                            <span class="font-medium text-on-surface">25kV Power Block (OHE)</span>
                        </label>
                        <label class="flex items-center gap-2 cursor-pointer select-none">
                            <input id="req-speed-restriction" type="checkbox" class="rounded border-outline text-primary focus:ring-primary w-4 h-4">
                            <span class="font-medium text-on-surface">TSR (Speed Restriction)</span>
                        </label>
                    </div>
                    <div id="wrapper-tsr-speed" class="hidden mt-1 flex items-center gap-2">
                        <span class="font-label-md text-[11px] text-on-surface-variant">TSR Speed (km/h):</span>
                        <input id="req-tsr-kmh" type="number" min="15" max="100" value="30" class="w-24 border border-outline-variant rounded px-2 py-1 text-xs font-data-mono bg-surface-container-lowest">
                    </div>
                </div>

                <!-- Row 6: Remarks -->
                <div>
                    <label class="font-label-md text-on-surface-variant block mb-1 text-[11px] uppercase font-bold">Description / Safety Justification</label>
                    <textarea id="req-description" rows="3" class="w-full border border-outline-variant rounded-md px-3 py-2 font-body-sm text-on-surface focus:outline-none focus:border-primary bg-surface-container-lowest" placeholder="Provide operational remarks, machine requirements, and track isolation notes..."></textarea>
                </div>

                <!-- Action Buttons -->
                <div class="flex justify-end items-center gap-3 pt-md border-t border-outline-variant mt-2">
                    <button type="button" id="btn-cancel-new-request" class="px-4 py-2 border border-outline-variant rounded-lg text-on-surface font-label-md hover:bg-surface-variant transition-colors">
                        Cancel
                    </button>
                    <button type="submit" id="btn-submit-new-request" class="px-5 py-2 bg-primary-container text-on-primary rounded-lg font-label-md font-bold hover:bg-primary transition-all shadow-sm flex items-center gap-2">
                        <span class="material-symbols-outlined text-[18px]">send</span>
                        Submit Request
                    </button>
                </div>
            </form>
        </div>
    `;

    // Toggle TSR speed field
    const tsrCheckbox = document.getElementById("req-speed-restriction");
    const tsrWrapper = document.getElementById("wrapper-tsr-speed");
    if (tsrCheckbox && tsrWrapper) {
        tsrCheckbox.onchange = () => {
            tsrWrapper.classList.toggle("hidden", !tsrCheckbox.checked);
        };
    }

    // Dynamic Track Line options based on Section
    const sectionSelect = document.getElementById("req-section-code");
    const trackLineSelect = document.getElementById("req-track-line");
    
    if (sectionSelect && trackLineSelect) {
        sectionSelect.addEventListener("change", () => {
            const section = sectionSelect.value;
            // NDLS-TKD, PWL-KDS, KDS-MTJ, MTJ-AGC have 2 tracks. TKD-FDB, FDB-PWL have 3 tracks.
            const has3rdLine = (section === "TKD-FDB" || section === "FDB-PWL");
            
            trackLineSelect.innerHTML = `
                <option value="UP_MAIN" selected>UP Main Line</option>
                <option value="DN_MAIN">DN Main Line</option>
                ${has3rdLine ? '<option value="3RD_LINE">3rd Line (Freight Loop)</option>' : ''}
            `;
        });
        
        // Trigger once on load
        sectionSelect.dispatchEvent(new Event("change"));
    }

    // Close modal handlers
    const closeModal = () => {
        if (modal) modal.remove();
    };

    document.getElementById("btn-close-new-request-modal")?.addEventListener("click", closeModal);
    document.getElementById("btn-cancel-new-request")?.addEventListener("click", closeModal);

    // Form submission
    const form = document.getElementById("form-new-request");
    form?.addEventListener("submit", async (e) => {
        e.preventDefault();

        const submitBtn = document.getElementById("btn-submit-new-request");
        const errorBanner = document.getElementById("modal-error-banner");
        const errorMsg = document.getElementById("modal-error-msg");

        const jobCodeRaw = (document.getElementById("req-job-code")?.value || "").trim();
        const jobCode = (jobCodeRaw === "" || jobCodeRaw.toUpperCase() === "AUTO") ? "" : jobCodeRaw;
        const title = document.getElementById("req-title")?.value.trim();
        const deptCode = document.getElementById("req-dept-code")?.value;
        const urgency = document.getElementById("req-urgency")?.value;
        const sectionCode = document.getElementById("req-section-code")?.value;
        const trackLine = document.getElementById("req-track-line")?.value;
        const durationMin = parseInt(document.getElementById("req-duration")?.value || "180", 10);
        const startTimeStr = document.getElementById("req-start-time")?.value || "01:00";
        const endTimeStr = document.getElementById("req-end-time")?.value || "06:00";
        const requiresTraffic = document.getElementById("req-traffic-block")?.checked ?? true;
        const requiresPower = document.getElementById("req-power-block")?.checked ?? false;
        const requiresTsr = document.getElementById("req-speed-restriction")?.checked ?? false;
        const tsrSpeed = parseInt(document.getElementById("req-tsr-kmh")?.value || "30", 10);
        const description = document.getElementById("req-description")?.value.trim();

        if (!title) {
            if (errorBanner && errorMsg) {
                errorBanner.classList.remove("hidden");
                errorMsg.textContent = "Please fill in the Activity Title.";
            }
            return;
        }

        // Convert start and end times to minutes
        const [sh, sm] = startTimeStr.split(":").map(Number);
        const [eh, em] = endTimeStr.split(":").map(Number);
        const startMin = (sh * 60) + sm;
        const endMin = (eh * 60) + em;

        const priorityMap = { CRITICAL: 5, HIGH: 4, MEDIUM: 3, ROUTINE: 2 };

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `<span class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span> Submitting...`;
        }

        if (errorBanner) errorBanner.classList.add("hidden");

        try {
            const created = await dataService.createMaintenanceRequest({
                job_code: jobCode, // empty string -> backend generates the real unique code
                title: title,
                department_code: deptCode,
                section_code: sectionCode,
                track_line: trackLine,
                duration_minutes: durationMin,
                priority: priorityMap[urgency] || 3,
                urgency: urgency,
                requires_power_block: requiresPower,
                requires_traffic_block: requiresTraffic,
                requires_speed_restriction: requiresTsr,
                speed_restriction_kmh: requiresTsr ? tsrSpeed : null,
                earliest_start_minute: startMin,
                latest_end_minute: endMin > startMin ? endMin : startMin + durationMin,
                description: description
            });

            closeModal();

            if (typeof onSuccess === "function") {
                onSuccess(created);
            }
        } catch (err) {
            console.error("Submission failed:", err);
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = `<span class="material-symbols-outlined text-[18px]">send</span> Submit Request`;
            }
            if (errorBanner && errorMsg) {
                errorBanner.classList.remove("hidden");
                errorMsg.textContent = err.message || "Failed to create maintenance request. Check inputs.";
            }
        }
    });
}

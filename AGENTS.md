# SIH26027 Railway Block Planning — Project Rules (AGENTS.md)

Treat this file as the project-level source of truth for all AI agents and developers working on this codebase. Follow all rules unless explicitly overridden by the user.

---

## 1. Project Goal
Build a professional prototype for SIH 2026 Problem Statement **SIH26027 — AI-Powered Automatic Block Planning to Maximize Asset Availability for Train Operations on Indian Railways**.

The product is a railway maintenance decision-support and optimization system. It coordinates maintenance demand from **Engineering (Permanent Way)**, **Traction Distribution (TRD / OHE)**, and **Signal & Telecommunication (S&T)** with railway operating windows and train movements.

**The goal is NOT to create a generic train tracker, generic AI chatbot, or generic dashboard.**

**Core Chain:**
$$\text{Maintenance Demand} + \text{Train / Operating Information} + \text{Validated Railway Constraints}$$
$$\downarrow$$
$$\text{Feasible Plans} \rightarrow \text{Optimized Block Plan} \rightarrow \text{Explainable Recommendation} \rightarrow \text{Human Review} \rightarrow \text{Dynamic Replanning}$$

---

## 2. Source of Truth
- The SIH problem statement is the source of truth for official scope.
- Refers to: Engineering, Traction Distribution, Signal & Telecommunication, BDMS, TMS/SMMS/TDMS, COA, train timetable, goods-train forecast, weekly/monthly planning.
- **Do not invent official railway processes, rules, system access, or terminology.**
- When a railway-specific detail is unknown, mark it as: **`PENDING DOMAIN VALIDATION`**.

---

## 3. Critical Domain Rule
The team has access to a railway-domain contact/expert.
Use this person to validate:
- Actual block-planning workflow
- Hard operational constraints vs soft preferences/objectives
- Maintenance-job compatibility and departmental dependencies
- Safety/permit/isolation dependencies
- Train/block interactions and handling of extensions/cancellations/emergency work
- What remains manually decided after a planned/mega/Sunday block exists
- What a real planner/controller would trust as system output

**Never turn an assumption into a railway rule without validation.**

---

## 4. Product Positioning
Position the product as: **Railway Maintenance Decision & Optimization System**
**NOT:**
- An AI train tracker
- A timetable generator only
- A generic calendar
- An LLM chatbot
- A static Gantt dashboard

---

## 5. Core Features & Priority

### P0 — Must Work (Rock Solid)
1. Maintenance request management
2. Train movement / operating-window representation
3. Railway constraint engine
4. Maintenance priority handling
5. Feasible block-plan generation
6. Optimization of the feasible plan (Google OR-Tools CP-SAT)
7. Gantt/timeline visualization
8. Before-vs-after KPIs
9. Plan explanation (*"Why this plan?"*)

### P1 — High-Value Differentiation
1. Multi-department job compatibility / bundling (Shadow Blocks)
2. Dynamic replanning
3. What-if simulation
4. Human-in-the-loop lock/edit/recalculate
5. Monthly $\rightarrow$ weekly $\rightarrow$ daily block-level planning hierarchy

### P2 — Optional
1. Live/public train-status adapter (with automatic mock fallback)
2. ML prediction for maintenance duration/risk/traffic where justified
3. Additional corridor scenarios

*Do not build P2 features at the expense of P0 reliability.*

---

## 6. Hard Constraints vs Soft Objectives

- **Hard Constraints (Must NEVER be violated)**:
  - Protected train movement conflict
  - Unavailable corridor/section
  - Incompatible maintenance activities
  - Required safety/isolation condition not satisfied (e.g. OHE power block)
  - Mandatory buffer/dependency not satisfied
  - *Action if violated*: **Reject candidate plan.**

- **Soft Objectives (Optimization preferences)**:
  - Minimize total blocked time
  - Minimize train disruption
  - Complete critical/overdue work earlier
  - Combine compatible work (Shadow block synergy)
  - Reduce maintenance backlog
  - Maximize useful block capacity & asset availability

*Do not mix safety constraints into a soft score.*

---

## 7. AI / ML Policy
- **Do NOT use an LLM as the railway scheduling brain.**
- Use deterministic rules and mathematical optimization for operational feasibility.
- Recommended architecture: $\text{Domain Rules} \rightarrow \text{Feasibility/Constraints} \rightarrow \text{Optimization} \rightarrow \text{Explainable Plan}$.
- Key explanation for judges:
  > *"AI predicts. Constraints protect. Optimization decides."*
- Any ML model must have a clear target, input data, evaluation metric, and fallback.
- **No fake AI.**

---

## 8. Optimization Policy
- Preferred solver: **Google OR-Tools CP-SAT**.
- Output requirements: scheduled jobs, block assignments, start/end times, unscheduled jobs, conflicts/rejections, KPI values, decision reasons.
- **Never hardcode "optimal" results directly in UI components.**

---

## 9. Dynamic Replanning
- Support live events: train delayed, maintenance extended, block unavailable, new urgent job, planned job cancelled.
- Flow: $\text{Existing plan} \rightarrow \text{Event occurs} \rightarrow \text{Identify affected items} \rightarrow \text{Re-check hard constraints} \rightarrow \text{Re-optimize} \rightarrow \text{Show what changed} \rightarrow \text{Update Gantt \& KPIs}$.
- The UI must show the Before $\rightarrow$ After comparison.

---

## 10. Explainability
Every major scheduling decision must have an understandable reason:
- **Why selected?** Critical job included, compatible jobs combined, no hard train conflict, required buffer satisfied, lower disruption than alternatives.
- **Why rejected/deferred?** Overlaps protected train, dependency unavailable, incompatible activity, no feasible window before deadline.
- Do not expose meaningless model jargon to judges.

---

## 11. Human-in-the-Loop
- Decision support, not autonomous railway control.
- Workflow: Optimizer recommends $\rightarrow$ Planner reviews $\rightarrow$ Planner accepts/edits/locks/rejects $\rightarrow$ Optimizer recalculates around locked decisions.

---

## 12. Data Policy & Labels
- **Synthetic Data**: Labeled as `"Synthetic Demo Data"`.
- **Live / Public Train Data**: Labeled as `"Live/Public Train Data"`.
- **Unvalidated Rules**: Labeled as `"Prototype Constraint — Pending Domain Validation"`.
- **Never claim direct integration** with TMS, SMMS, TDMS, COA, BDMS, NTES without authorized credentials.
- Never put API keys or secrets in frontend code or Git.

---

## 13. Scenario Design
- Manageable default corridor scenario:
  - 1 corridor (Delhi–Agra mainline)
  - 4–6 sections (NDLS-TKD, TKD-FDB, FDB-PWL, PWL-KDS, KDS-MTJ, MTJ-AGC)
  - 3 core departments: Engineering, S&T, TRD/OHE
  - 15–30 maintenance jobs, 10–30 train movements, 5–10 block windows

---

## 14. Frontend Rules (Stitch Baseline)
- Preserve existing Stitch UI visual design, spacing, typography, colors (`#003366`), and railway enterprise feel.
- **DO NOT redesign screens or use flashy/neon AI gimmicks.**
- Primary screens: Operations Dashboard, Maintenance Requests, Block Planning, Gantt View, Plan Logic, What-if / Replanning, Reports.

---

## 15. Frontend Architecture & Data Abstraction
- Reusable DOM components in `frontend/js/components/`.
- Data service layer (`dataService.js`, `trainDataService.js`) with typed schemas (`types.js`):
  - `MaintenanceJob`, `TrainMovement`, `BlockWindow`, `Constraint`, `OptimizedPlan`, `PlanChange`.
- Do not bypass the data-service layer.

---

## 16. Live Train Data Integration
- Pattern: $\text{Live / Mock Provider} \rightarrow \text{Train Data Adapter} \rightarrow \text{Normalized TrainMovement} \rightarrow \text{Constraint Engine} \rightarrow \text{Optimizer} \rightarrow \text{UI}$.
- Must work 100% offline with automatic mock fallback.
- Live data feeds maintenance planning, not a standalone tracking app.

---

## 17. Testing Rules
- Automated tests in `tests/` for all major components (no-conflict schedule, protected train conflict, incompatible jobs, unavailable window, train-delay replanning, API fallback).
- Run and pass all tests before completing tasks.

---

## 18. 3-Minute Wednesday Selection Demo Flow
1. Dashboard: Multi-department maintenance demand (ENG, TRD, S&T).
2. Corridor timetable and block window constraints.
3. Click **Generate Plan** $\rightarrow$ Show optimized Gantt with shadow blocks.
4. Click block $\rightarrow$ View *"Why this plan?"* explanation tree.
5. Trigger train delay event $\rightarrow$ Click **Auto Replan** $\rightarrow$ Show revised Gantt and Before vs After KPI delta.

---

## 19. Differentiation over Existing Baseline (e.g. RailAvail)
Target differentiation:
- Domain-validated railway constraints & compatibility logic
- Multi-department Shadow Block synergy (ENG + TRD + S&T co-location)
- Mathematical explainability tree
- Dynamic replanning on live events
- Human-in-the-loop decision locking

---

## 20. Agent Communication & Execution Guidelines
- Inspect existing codebase before modifying or creating files.
- Preserve existing UI and design tokens.
- Do not invent railway rules. Mark assumptions as `PENDING DOMAIN VALIDATION`.
- Keep business logic decoupled from presentation.
- Small, testable changes validated with pytest.
- Report precisely what was implemented.

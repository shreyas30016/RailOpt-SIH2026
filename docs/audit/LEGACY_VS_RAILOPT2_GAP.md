# Legacy Prototype vs. RailOpt 2.0 Specification Gap Analysis
**Project:** SIH26027 — AI-Powered Automatic Block Planning System for Indian Railways  
**Scope:** Comparative gap analysis between the existing legacy prototype in `A:\SHREYAS\RAILWAY BLOCK AI` and the desired **RailOpt 2.0** target architecture.

---

## 1. Feature-by-Feature Gap Matrix

| Domain Feature | Current Legacy State (`RAILWAY BLOCK AI`) | Desired RailOpt 2.0 Target State | Gap / Action Needed |
| :--- | :--- | :--- | :--- |
| **1. Authentication & Session** | Passwordless prototype login with Division dropdown & Role radio cards. Token in `localStorage`. | Multi-role session management with JWT / secure token, role-tailored landing views, and corridor switching. | Keep lightweight demo login flow; add server-side token validation on mutating endpoints. |
| **2. Operations Dashboard** | Bento grid with dynamic KPIs, Donut chart, live train feed, upcoming blocks table, and conflict cards. | Real-time multi-corridor overview with live bottleneck heatmaps, emergency alert triage, and quick-replan action triggers. | Add section congestion heatmap & emergency possession quick-action shortcut. |
| **3. Maintenance Requests Backlog** | Filterable table by department (ENG, S&T, TRD, MECH), urgency, section, text search. Approve/Defer/Delete working. Right detail sidebar is static mockup. "New Request" modal missing. | Full multi-department demand management with duration estimator modal, machine resource conflict check, and right-panel dynamic selection sync. | Connect "New Request" modal to `POST /api/maintenance/requests` and dynamically hydrate right detail sidebar on row click. |
| **4. Optimization Solver** | Google OR-Tools CP-SAT solver running in `backend/app/optimizer/solver.py`. Deconflicts against train paths, enforces buffers, pairs shadow blocks. | Full CP-SAT mathematical optimization with multi-track branching, train speed restriction impact modeling, and crew fatigue constraints. | Solver logic is already strong; expose tuning parameters (weights for delay vs shadow synergy) in UI. |
| **5. Gantt Timeline View** | DOM element mismatch causes static placeholder HTML to show. Dynamic timeline generator in `app.js` and `gantt.py` exists but is disconnected. | Interactive SVG/HTML5 24-hour multi-track timeline with zoom levels (24h, 12h, 8h), draggable block locks, and train trajectory overlay. | Fix element selector ID in `gantt-view.html` to allow `renderDynamicGanttRows()` to mount live solver blocks. |
| **6. Decision Explainer Tree** | Structured decision tree backend (`explainer.py`) and modal renderer (`optimizationResultView.js`) exist. Not triggered on click due to missing global assignment. | Mathematical *"Why this plan?"* explainability tree displaying hard constraint compliance, shadow block synergy pairing, and rejected alternatives. | Attach `window.showJobExplanation` to `window` in `app.js` to pop up the explainer modal on row click. |
| **7. What-If Replanning** | Simulates Train Delay, Block Unavailability, Maintenance Overrun, Emergency Job via differential CP-SAT runs. Updates delta badges. | Side-by-side Before $\rightarrow$ After comparison Gantt with affected train highlight, locked decision support, and one-click "Accept Revised Plan". | Populate the Before/After comparison tables in `what-if.html` with concrete rescheduled block lists. |
| **8. Plan Logic & Constraints** | Displays static Stitch HTML mockup text. Calling `getRailwayConstraints()` crashes due to missing client method. | Dynamic constraint viewer listing active Hard Safety Constraints vs Soft Optimization Objectives loaded from `railway_rules.yaml`. | Add `getRailwayConstraints()` to `dataService.js` and dynamically render rules from `/api/optimization/rules`. |
| **9. Reports & Analytics** | Static KPI cards and faux CSS bar charts in HTML. CSV export working from backend historical runs. | Comprehensive KPI report with YTD possession execution metrics, departmental grant ratios, and printable PDF/CSV operational summaries. | Bind `/api/reports/analytics` to the KPI cards and chart containers in `reports.html`. |
| **10. Live Train Feed** | `train_adapter.py` provides normalized movements with realistic GPS delays and mock fallback. Rendered on Dashboard. | Multi-source adapter (NTES/COA/Mock) feeding live delays directly into dynamic replanning triggers. | Fully working baseline; ready for presentation. |

---

## 2. Structural & Code Architecture Differences

| Architecture Aspect | Legacy Prototype Implementation | RailOpt 2.0 Target Standard |
| :--- | :--- | :--- |
| **State Management** | Centralized `appState.js` with observer listeners + DOM string template rendering. | Unified reactive state store coordinating UI filters, solver runs, and modal states without full-page reloads. |
| **Component Modularity** | Modular DOM components in `frontend/js/components/` (8 files) with ES6 imports. | Strict separation of DOM rendering components, data abstraction services, and business logic. |
| **Backend Router Layout** | Modular FastAPI routers mounted on both `/api` and `/api/v1`. Direct aliases on root. | Clean OpenAPI 3.1 REST API with standardized error schemas and lifespan data management. |
| **Solver Decoupling** | Solver runs independently of web requests; returns structured KPI JSON and explanation trees. | Mathematical optimization strictly decoupled from presentation layer; zero hardcoded solver results in UI. |

# SIH26027 Dashboard Interaction & Data Audit

**Date:** 2026-08-31  
**Scope:** Complete inventory of all interactive and data-bearing elements on the Operations Dashboard (`frontend/dashboard.html`).

---

## 1. Interaction & Data Inventory

| Element ID / Component | Visible Label / Type | Current Status | Current Behavior | Required Action / Fix |
|---|---|---|---|---|
| **Sidebar: Brand Link** | `RAILOPT` (Logo + Title) | **WORKING** | Navigates to `/dashboard` | Retain. |
| **Sidebar: Nav Links** | 7 page links (Dashboard, Requests, Planning, Gantt, What-if, Logic, Reports) | **WORKING** | Navigates to respective URLs with active indicator | Retain & ensure state sync. |
| **Sidebar: New Request** | `+ New Request` Button | **WORKING** | Calls `window.triggerNewRequestModal()` | Retain & ensure form submission updates dashboard. |
| **Sidebar: Domain Rules** | `Domain Rules` Link | **WORKING** | Navigates to `/constraints-logic` | Retain. |
| **Mobile Header** | Brand + Notification + Profile | **STATIC / INCOMPLETE** | Notifications and Planner pills are inert | Add dropdown / modal actions. |
| **Header: DateTime** | `#header-datetime` | **WORKING** | Dynamic ticking clock | Retain. |
| **Header: Notifications** | Bell Icon Button with red badge | **STATIC** | Dead click; no handler | Connect to notification popover with real system alerts. |
| **Header: Settings** | Gear Icon Button | **WORKING** | Links to `/constraints-logic` | Retain. |
| **Header: Planner Menu** | Planner Badge + Dropdown Icon | **STATIC** | Dead click; no menu | Add dropdown showing DOM role, division info, data mode. |
| **Header: Data Mode** | `⚠️ DEMO DATA` Badge | **WORKING** | Injected by `setupNavigation()` | Retain. |
| **KPI Card 1** | Maintenance Requests | **PARTIALLY STATIC** | Static fallback "12" in HTML; selector in `app.js` was fragile | Add explicit `id="kpi-requests"`, bind to `DashboardSummary.total_pending_requests`, make card click navigate to `/maintenance-requests`. |
| **KPI Card 2** | Critical Jobs | **PARTIALLY STATIC** | Static "3" in HTML | Add explicit `id="kpi-critical"`, bind to `urgent_queue.length`, click navigates to `/maintenance-requests?urgency=CRITICAL`. |
| **KPI Card 3** | Available Blocks | **PARTIALLY STATIC** | Static "5" in HTML | Add explicit `id="kpi-blocks"`, bind to `planned_blocks_today`, click navigates to `/block-planning`. |
| **KPI Card 4** | Conflicts | **PARTIALLY STATIC** | Static "2" in HTML | Add explicit `id="kpi-conflicts"`, bind to actual conflict metrics from latest optimization run, click navigates to `/constraints-logic`. |
| **Train Feed Header** | Train Operating Window Feed | **WORKING** | Dynamic container with data mode badge | Retain. |
| **Train Feed Cards** | 4 Live/Synthetic Train Cards | **STATIC (Non-interactive)** | Cards render from `trainDataService` but cannot be clicked | Make each train card clickable to open Train Detail Modal with timetable path and Gantt navigation. |
| **Dept Breakdown: Pie** | CSS Conic Pie Chart | **STATIC** | Hardcoded gradient and static "12 Total" in HTML | Dynamically calculate conic-gradient, total, and center text from `data.department_breakdown`. |
| **Dept Breakdown: Legend** | Dept Counts & Percentages | **STATIC** | Hardcoded "ENG: 6", "S&T: 4", "TRD: 2" | Dynamically generate legend rows with live counts, percentages, and filter links. |
| **Upcoming Blocks: Header** | Upcoming Blocks (Next 24 hrs) | **WORKING** | Header title | Retain. |
| **Upcoming Blocks: View All**| `View All` button in table header | **BROKEN / INERT** | No `onclick` or `href` attribute | Wire click to navigate to `/block-planning` or `/maintenance-requests`. |
| **Upcoming Blocks: Rows** | Job/Block Table Rows | **PARTIALLY STATIC** | HTML had hardcoded B-01..B-05 rows | Replace with dynamic `createJobTableRow` / `ScheduledBlock` rendering from DB/API, with click opening Decision Audit modal. |
| **Conflicts: Header** | Conflicts Overview | **WORKING** | Header title | Retain. |
| **Conflicts: View All** | `View All` button | **BROKEN / INERT** | No `onclick` or `href` attribute | Wire click to navigate to `/constraints-logic`. |
| **Conflicts: List** | Conflict Items | **STATIC** | Hardcoded B-01 vs 12302 and B-02 vs J-07 | Dynamically populate from `latest_run.conflicts_resolved` / `conflict_logs`. |
| **Conflicts: Resolve Btn** | `Resolve` Button | **BROKEN / INERT** | Dead click | Wire to open conflict resolution details or navigate to `/block-planning`. |
| **AI Optimization Banner** | AI Optimization Active Card | **STATIC** | Informational card | Add click handler to navigate to `/block-planning`. |

---

## 2. Hardcoded Values Identified

1. **HTML Static KPI Fallbacks:** `12` requests, `3 new`, `3` critical jobs, `5` available blocks, `2` conflicts.
2. **HTML Static Pie Chart:** `background: conic-gradient(...)`, `12 Total`, `6 (50%)`, `4 (33%)`, `2 (17%)`.
3. **HTML Static Table Rows:** `B-01` (NDLS - GZB 22:30-01:30), `B-02`, `B-03`, `B-04`, `B-05`.
4. **HTML Static Conflicts:** `2 Conflicts`, `B-01 vs Train 12302 (Overlaps)`, `B-02 vs Maintenance Job J-07 (Track Machine)`.
5. **Header Static Clock:** `31 Aug 2026 | 20:15:00` placeholder before JS clock ticks.

---

## 3. Data Flow Target

```
Backend API (GET /api/dashboard/summary, GET /api/trains/live, POST /api/optimization/run)
    ↓
DataService (fetchWithFallback & typed responses)
    ↓
AppState (central reactive store)
    ↓
Dashboard Render Functions (KPIs, Train Cards, Dept Breakdown Pie, Upcoming Blocks, Conflicts)
    ↓
User Actions (Click Train → Modal, Click Job → Decision Audit, Click View All → Route, Submit Request → Refresh)
```

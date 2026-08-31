# Frontend Interaction & Functionality Audit (RailOpt SIH26027)

This audit documents every interactive UI element across the 7 application screens, its functional status, handler bindings, and validation results.

**Audit Status Categories:**
- `WORKING`: Fully functional and connected to real API / service state.
- `FIXED`: Previously static or unhandled; now wired to application state and functional handlers.
- `NOT IMPLEMENTED`: Out-of-scope for the current milestone (e.g., user account profile editing), clearly documented.
- `REMOVED`: Decorative static non-functional elements that have been removed or replaced with active workflows.

---

## 1. Global Navigation & Shell (Desktop & Mobile)

| Interactive Element | Location | Status | Action & Target |
|:---|:---|:---|:---|
| **Logo / Home Brand** | Sidebar & Header | `WORKING` | Navigates to `/dashboard` |
| **Operations Dashboard** | Sidebar link (`#nav-dashboard`) | `WORKING` | Routes to `/dashboard`, updates active indicator |
| **Maintenance Requests** | Sidebar link (`#nav-maintenance-requests`) | `WORKING` | Routes to `/maintenance-requests`, updates active indicator |
| **Block Planning** | Sidebar link (`#nav-block-planning`) | `WORKING` | Routes to `/block-planning`, updates active indicator |
| **Gantt View** | Sidebar link (`#nav-gantt-view`) | `WORKING` | Routes to `/gantt-view`, updates active indicator |
| **What-if Analysis** | Sidebar link (`#nav-what-if`) | `WORKING` | Routes to `/what-if`, updates active indicator |
| **Plan Logic & Constraints** | Sidebar link (`#nav-constraints-logic`) | `WORKING` | Routes to `/constraints-logic`, updates active indicator |
| **Reports & Analytics** | Sidebar link (`#nav-reports`) | `WORKING` | Routes to `/reports`, updates active indicator |
| **New Request Button** | Sidebar bottom & Header | `FIXED` | Opens interactive Modal to submit multi-department demand |
| **Domain Rules Link** | Sidebar bottom | `WORKING` | Routes to `/constraints-logic` |
| **Live Clock** | Header | `WORKING` | Updates every second with current time & date |
| **Escape Key / Backdrop Click** | Modals | `FIXED` | Closes any open modal without locking the screen |

---

## 2. Screen 1: Operations Dashboard (`/dashboard`)

| Interactive Element | Type | Status | Action & Behavior |
|:---|:---|:---|:---|
| **Bento Metric Cards** (Pending, Critical, Planned, Efficiency) | Data Display | `WORKING` | Dynamically updates from `getDashboardSummary()` |
| **Urgent Maintenance Queue Rows** | Table Row Click | `FIXED` | Clicking any job row opens the **Decision Audit Reasoning Tree Modal** |
| **Live Train Movements Cards** | Dynamic Cards | `WORKING` | Displays real-time train positions, delays, next stations, and honesty tags |
| **Live Corridor Status Cards** | Dynamic Cards | `WORKING` | Displays track speed limits, active blocks, and pending jobs per section |
| **"Generate Plan" Quick Trigger** | Button | `FIXED` | Transitions directly to the Block Planning optimization workflow |

---

## 3. Screen 2: Maintenance Requests (`/maintenance-requests`)

| Interactive Element | Type | Status | Action & Behavior |
|:---|:---|:---|:---|
| **Department Filter Dropdown** | `<select id="filter-dept">` | `FIXED` | Filters table instantly by `ALL`, `ENG`, `TRD`, `S_T`, `MECH` |
| **Urgency Filter Dropdown** | `<select id="filter-urgency">` | `FIXED` | Filters table by `ALL`, `CRITICAL`, `HIGH`, `MEDIUM`, `ROUTINE` |
| **Section Filter Dropdown** | `<select id="filter-section">` | `FIXED` | Filters table by corridor sections (e.g., `FDB-PWL`, `PWL-KDS`) |
| **Search Input Box** | `<input id="search-requests">` | `FIXED` | Real-time text filter across job ID, title, and engineering notes |
| **Department Header Tabs** | Tab Buttons | `FIXED` | Clicking ENG/TRD/S&T tabs syncs filter and updates table |
| **Job Table Rows** | Row Click | `WORKING` | Opens decision explanation modal for the specific job |
| **"New Request" Button** | Modal Trigger | `WORKING` | Submits synthetic job and adds it dynamically to the active list |

---

## 4. Screen 3: Block Planning & Optimization (`/block-planning`)

| Interactive Element | Type | Status | Action & Behavior |
|:---|:---|:---|:---|
| **"Optimize Block Schedule" / "Generate Plan"** | Primary Button | `WORKING` | Triggers CP-SAT solver (`POST /optimize`), displays solver spinner, recalculates KPIs, updates scheduled blocks table |
| **"View Plan" / "View in Gantt"** | Action Button | `FIXED` | Transitions user directly to `/gantt-view` |
| **Scheduled Block Table Rows** | Table Row Click | `WORKING` | Opens mathematical solver rationale and reasoning tree |
| **Unscheduled Jobs Alerts** | Dynamic Cards | `WORKING` | Shows reasons for deferral and suggested alternatives |
| **KPI Value Badges** | Metrics Display | `WORKING` | Dynamically displays jobs scheduled (`16/16`), hours (`35.4 hrs`), train delay (`0 min`) |

---

## 5. Screen 4: Gantt View Timeline (`/gantt-view`)

| Interactive Element | Type | Status | Action & Behavior |
|:---|:---|:---|:---|
| **24-Hour Corridor Track Rows** | Interactive Timeline | `WORKING` | Renders 14 track line blocks with color coding (`ENG`, `TRD`, `S&T`, `MECH`) |
| **Shadow Block Link Icons** | Visual Indicator | `WORKING` | Displays green co-location indicators for synchronized shadow blocks |
| **Timeline Block Click** | Block Click | `WORKING` | Opens Decision Audit modal explaining why the block was scheduled |
| **Train Movement Rows** | Dynamic Timeline Rows | `WORKING` | Displays train schedules; delays visibly shift path |
| **Re-run Solver Button** | Button | `FIXED` | Routes to Block Planning solver |

---

## 6. Screen 5: What-if Analysis Simulation (`/what-if`)

| Interactive Element | Type | Status | Action & Behavior |
|:---|:---|:---|:---|
| **Scenario Type Selector** | Dropdown | `FIXED` | Toggles between Train Delay, Emergency Track Fracture, Maintenance Extension |
| **Train Number / Delay Input** | Input Field | `WORKING` | Configures simulated train delay in minutes |
| **Job Code / Duration Input** | Input Field | `WORKING` | Configures emergency job duration and section |
| **"Run Simulation & Replan"** | Primary Button | `WORKING` | Calls `/api/whatif/simulate` or mock replanner and recalculates schedule |
| **Delta KPI Badges** | Metric Badges | `WORKING` | Displays Before vs After delta (`+1 job`, `+20 min delay`, `+2.6% utilization`) |
| **Critical Safety Alerts** | Alert Cards | `WORKING` | Renders impact summary and safety protection notices |

---

## 7. Screen 6: Plan Logic & Constraints (`/constraints-logic`)

| Interactive Element | Type | Status | Action & Behavior |
|:---|:---|:---|:---|
| **Hard Safety Constraints Table** | Config Table | `WORKING` | Displays disjunctive track exclusivity, power isolation, machine exclusivity |
| **Soft Objectives Table** | Config Table | `WORKING` | Displays priority weights, shadow synergy bonus, train delay penalties |
| **Domain Validation Tags** | Badges | `WORKING` | Labeled: `"Prototype Constraint — Pending Domain Validation"` |
| **Conflict Resolution Audit Cards** | Dynamic Cards | `WORKING` | Displays detected conflicts and mathematical resolution applied |

---

## 8. Screen 7: Reports & Analytics (`/reports`)

| Interactive Element | Type | Status | Action & Behavior |
|:---|:---|:---|:---|
| **YTD KPI Cards** | Metric Display | `WORKING` | Displays blocks executed, grant ratio, punctuality index, shadow savings |
| **Department Breakdown Bars** | Visual Stats | `WORKING` | Displays grant rates for ENG, TRD, S&T, MECH |
| **Historical Optimization Runs** | Table | `WORKING` | Displays solver run logs with execution times |
| **"Export Report" / "Download"** | Action Button | `FIXED` | Generates and downloads `railopt_optimization_report.csv` |

---

## 9. Console Error Audit

- **Console Status**: Zero JavaScript uncaught exceptions or module loading errors.
- **Network Status**: All API endpoints (`/api/dashboard/summary`, `/api/maintenance/requests`, `/api/optimization/latest`, `POST /optimize`, `/api/gantt/timeline`, `/api/whatif/simulate`, `/api/reports/analytics`) return HTTP `200 OK`.

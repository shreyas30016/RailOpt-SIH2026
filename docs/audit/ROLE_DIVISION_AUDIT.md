# RailOpt Role & Division System Audit
**Repository:** `A:\SHREYAS\RAILWAY BLOCK AI`  
**Purpose:** Document how operational roles and administrative divisions are implemented, enforced, and visualized throughout the existing codebase.

---

## 1. Supported Divisions

The application recognizes **10 Indian Railways operational divisions** in `backend/app/api/auth.py` and `frontend/login.html`:

| Division Code | Official Operational Name | Zone | Corridor Context in Prototype |
| :--- | :--- | :--- | :--- |
| **`NDL`** | Northern Railway — Delhi Division | Northern Railway (NR) | Delhi–Agra Mainline Corridor (Primary demo corridor) |
| **`NW` / `NCR`** | North Central Railway — Prayagraj Division | North Central Railway (NCR) | High-density freight & express corridor |
| **`WR`** | Western Railway — Mumbai Central Division | Western Railway (WR) | Suburban & Mumbai–Ahmedabad trunk line |
| **`CR`** | Central Railway — Mumbai CST Division | Central Railway (CR) | Kalyan–Igatpuri / Pune ghat corridor |
| **`ER`** | Eastern Railway — Howrah Division | Eastern Railway (ER) | Howrah–Bardhaman chord corridor |
| **`SER`** | South Eastern Railway — Kharagpur Division | South Eastern Railway (SER) | Howrah–Kharagpur freight trunk line |
| **`SCR`** | South Central Railway — Secunderabad Division | South Central Railway (SCR) | Kazipet–Secunderabad–Wadi corridor |
| **`SR`** | Southern Railway — Chennai Division | Southern Railway (SR) | Chennai–Arakkonam–Jolarpettai corridor |
| **`NWR`** | North Western Railway — Jaipur Division | North Western Railway (NWR) | Jaipur–Phulera–Ajmer single/double line |
| **`NER`** | North Eastern Railway — Gorakhpur Division | North Eastern Railway (NER) | Lucknow–Gorakhpur–Chhapra mainline |

---

## 2. Operational Roles & Permissions Matrix

Implemented in `backend/app/api/auth.py:38-44` and client-side guards in `frontend/js/app.js`:

| Role Key | Operational Title & Designation | `can_approve` | `can_optimize` | `can_edit` | Initial | Operational Authority in RailOpt |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`CONTROLLER`** | Controller (DOM / TPC) | **YES** | **YES** | **YES** | `C` | Full authority: Can approve/defer requests, execute CP-SAT solver, run What-if simulations, and commit final blocks. |
| **`PLANNER`** | Planner (Sr. DOM / DEN) | **YES** | **YES** | **YES** | `P` | Planning authority: Can review demand, run optimizations, compare before-vs-after plans, and approve possession schedules. |
| **`ENGINEER`** | Engineer (JE / SSE P-Way) | **NO** | **NO** | **YES** | `E` | Departmental field submitter: Can view requests and submit new Civil Engineering maintenance demands. Cannot approve or trigger system-wide optimization. |
| **`TRD_OFFICER`** | TRD Officer (JE / SSE OHE) | **NO** | **NO** | **YES** | `T` | Departmental field submitter: Can submit and review Traction Distribution / 25kV OHE power block requests. |
| **`ST_OFFICER`** | S&T Officer (JE / SSE Signal) | **NO** | **NO** | **YES** | `S` | Departmental field submitter: Can submit and review Signal & Telecommunication block demands. |

---

## 3. Actual Implementation Behavior & Gaps

### A. Authentication & Session Handling
- **Login Mechanism:** Passwordless prototype login (`POST /api/auth/login`). Validates username, role, and division code against dictionaries. Returns a base64-encoded JSON profile token.
- **Session Storage:** Client persists `railopt_user` and `railopt_token` in browser `localStorage`.
- **Session Expiry:** Does not expire automatically during a browser session. Cleared upon clicking *"Sign Out / Switch Role"* in header or profile popover.
- **Auth Guard:** `_requireAuth()` in `app.js:24` automatically redirects unauthenticated users back to `/login`.

### B. Header & UI Customization by Role
- **Division Badge:** Top header displays active division name (e.g. *"Northern Railway — Delhi Division"*).
- **User Avatar & Label:** Top header displays user initial (`C`, `P`, `E`, `T`, `S`) and operational role label.
- **Profile Popover:** Displays Staff ID, Active Corridor, and Authority statement (e.g. *"✅ Full Approval Rights"* vs *"❌ Request Only"*).

### C. Actual Permission Enforcement
- **Client-Side Enforcement:** In `app.js:580`, when clicking *"✓ Approve"* or *"⏸ Defer"*, `app.js` checks `user.can_approve`. If false (for Engineer, TRD Officer, S&T Officer), it displays an error toast:  
  `"Your current role does not have authorization to approve/defer."`
- **Backend API Enforcement Gap:** The backend endpoint `PUT /api/maintenance/requests/{id}` currently does not inspect the `Authorization: Bearer <token>` header to reject unauthorized role updates server-side. It accepts any valid PUT request without rejecting non-approver roles.
- **Sidebar Difference Gap:** The sidebar currently displays identical navigation links (`Operations Dashboard`, `Maintenance Requests`, `Block Planning`, `Gantt View`, `What-if Analysis`, `Reports`) for all roles rather than filtering navigation options based on departmental or planning authority.

---

## 4. Key Recommendations for Future Sprints

1. **Server-Side Role Verification:** Add FastAPI dependency `verify_planner_or_controller` to `PUT /api/maintenance/requests/{id}` and `POST /api/optimization/run` to enforce role security at the API gateway layer.
2. **Dynamic Departmental Filtering for Field Officers:** When an `ENGINEER`, `TRD_OFFICER`, or `ST_OFFICER` logs in, automatically default the Maintenance Requests tab filter to their corresponding department.
3. **Division-Scoped Corridor Data:** Allow selecting different division corridors from the settings popover to load corridor-specific sections (e.g., Mumbai Central–Surat for WR vs Delhi–Agra for NR).

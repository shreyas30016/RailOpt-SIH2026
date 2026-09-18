# Sprint P1.3 — Role-Based Experience & Server-Side RBAC Hardening

## Overview
- **Sprint Target**: Real Role-Based Operational Experience + Server-Side RBAC
- **Repository**: `A:\SHREYAS\RAILWAY BLOCK AI`
- **Scope**: Authenticated RBAC enforcement on backend endpoints, department scoping for field roles, anti-spoofing protection, and role-differentiated frontend landing, navigation, action controls, and modal forms.

---

## Architecture & Security Enforcement

### 1. Server-Side Token Authorization (`backend/app/api/auth.py`)
- Standardized authentication token verification with HTTP Bearer scheme: `Authorization: Bearer <token>`.
- Token extraction and signature verification via `get_current_user` dependency.
- Return HTTP status codes according to standard contracts:
  - `401 Unauthorized`: Missing, expired, unparseable, or malformed Authorization header.
  - `403 Forbidden`: Authenticated user lacking the required role permission or exceeding authorized department scope.
- Anti-spoofing guarantee: Role and permission checks evaluate decoded token claims exclusively; request body/parameter role fields cannot escalate privileges.

### 2. Endpoint Protection
- `POST /api/optimization/run` & `POST /optimize`: Guarded by `Depends(require_permission("can_optimize"))`.
- `POST /api/whatif/simulate`: Guarded by `Depends(require_permission("can_optimize"))`.
- `POST /api/maintenance/requests`: Requires valid user session and strictly validates department scope via `validate_department_scope`.
- `PUT /api/maintenance/requests/{id}`:
  - Status transitions to `APPROVED` or `DEFERRED` strictly require `can_approve` (403 for field roles).
  - Field role updates are restricted to the user's authorized department.
- `DELETE /api/maintenance/requests/{id}`:
  - Controllers/Planners can delete any request.
  - Field roles can only delete requests within their assigned department.

---

## Frontend Role-Differentiated Experience

| Dimension | Controller (`CONTROLLER`) | Planner (`PLANNER`) | Engineer (`ENGINEER`) | TRD Officer (`TRD_OFFICER`) | S&T Officer (`ST_OFFICER`) |
|---|---|---|---|---|---|
| **Landing Page** | `/dashboard` | `/dashboard` | `/maintenance-requests` | `/maintenance-requests` | `/maintenance-requests` |
| **Sidebar Menu** | All 7 Sections | All 7 Sections | 4 Scoped Sections (`Block Planning` & `What-If` hidden) | 4 Scoped Sections (`Block Planning` & `What-If` hidden) | 4 Scoped Sections (`Block Planning` & `What-If` hidden) |
| **Maintenance Link Text** | Maintenance Requests | Maintenance Requests | Engineering Requests | TRD / OHE Requests | S&T Requests |
| **Department Scoping** | All Departments (Tabs active) | All Departments (Tabs active) | Scoped to Civil (`ENG`), other tabs locked | Scoped to Traction (`TRD`), other tabs locked | Scoped to S&T (`S_T`), other tabs locked |
| **Approval Actions** | `✓ Approve`, `⏸ Defer` visible | `✓ Approve`, `⏸ Defer` visible | Hidden (Shows `Audit` button) | Hidden (Shows `Audit` button) | Hidden (Shows `Audit` button) |
| **New Request Modal** | Full department selector | Full department selector | Department locked to `ENG`, Job ID `JOB-ENG-XXX` | Department locked to `TRD`, Job ID `JOB-TRD-XXX` | Department locked to `S_T`, Job ID `JOB-ST-XXX` |
| **Optimization CTA** | Available in Hero / Header | Available in Hero / Header | Hidden / Inactive | Hidden / Inactive | Hidden / Inactive |

---

## Verification & Testing

### 1. Targeted RBAC Automated Tests (`tests/test_rbac_p13.py`)
- `test_controller_full_authority`: Controller can run optimization, create, approve, defer, simulate what-if, and delete (PASSED).
- `test_planner_authority`: Planner can optimize, simulate what-if, and approve requests (PASSED).
- `test_field_roles_optimization_and_whatif_forbidden`: Verified `403 Forbidden` for Engineer, TRD Officer, S&T Officer on optimization and what-if simulation (PASSED).
- `test_field_roles_cannot_approve_or_defer`: Verified `403 Forbidden` when field roles attempt to set `status="APPROVED"` or `"DEFERRED"` (PASSED).
- `test_missing_and_invalid_token_returns_401`: Verified `401 Unauthorized` on missing, malformed, or invalid auth headers (PASSED).
- `test_anti_spoofing_payload_cannot_elevate_role`: Verified payload forgery cannot bypass role verification (PASSED).
- `test_department_scoping_enforcement_for_field_roles`: Verified cross-department request creation/deletion is blocked with `403` while intra-department operations succeed (PASSED).

### 2. Full Regression Test Suite
- Ran complete test suite across all 11 test files:
  - **Result**: **66 passed out of 66 tests (100% pass rate)** in 276.70s.

### 3. Browser Interactive Verification
- Verified all 5 operational roles live in the browser using the subagent recording flow:
  - Controller landed on `/dashboard` with full 7 navigation items and approval controls.
  - Engineer landed directly on `/maintenance-requests`, saw "Engineering Requests", only Civil jobs, and modal pre-locked to `ENG`.
  - TRD Officer landed directly on `/maintenance-requests`, saw "TRD / OHE Requests", only TRD jobs, and modal pre-locked to `TRD`.
  - S&T Officer landed directly on `/maintenance-requests`, saw "S&T Requests", only S&T jobs, and modal pre-locked to `S_T`.
  - Planner landed on `/dashboard` with planning permissions.

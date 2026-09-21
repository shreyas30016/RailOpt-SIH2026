# RailOpt — UI Navigation and Role Experience

## Goal
Role selection must create a materially different operational experience.

Avoid:
> every role gets the same dashboard/sidebar/actions.

## Common shell
All authenticated roles may share:
- RailOpt branding;
- active division indicator;
- profile/user menu;
- sign-out/switch-role;
- notification/settings controls where appropriate.

## Navigation matrix

| Module | Controller | Planner | Engineer | TRD | S&T |
|---|---:|---:|---:|---:|---:|
| Operations Dashboard | Full | Yes | Departmental/read-only | Departmental/read-only | Departmental/read-only |
| Maintenance Requests | Full | Full | Scoped | Scoped | Scoped |
| Block Planning | Yes | Yes | Read-only/limited | Read-only/limited | Read-only/limited |
| Gantt View | Full | Full | Read-only | Read-only | Read-only |
| What-If Analysis | Yes | Yes | Restricted/read-only | Restricted/read-only | Restricted/read-only |
| Constraints | Yes | Yes | Read-only | Read-only | Read-only |
| Review & Approvals | Yes | Yes | No | No | No |
| Reports | Yes | Yes | Scoped/read-only | Scoped/read-only | Scoped/read-only |
| Settings | Session/UI settings | Session/UI settings | Session/UI settings | Session/UI settings | Session/UI settings |

Exact route names must follow the existing application.

## Controller dashboard
Show operational overview:
- KPIs;
- demand breakdown;
- active/upcoming possessions;
- train movement status;
- conflicts;
- quick operational actions.

## Planner experience
Prioritize:
- optimization;
- pending demand;
- plan quality;
- schedule review;
- conflicts;
- What-If comparison.

## Field-role experience
Prioritize:
- own department requests;
- request status;
- upcoming relevant blocks;
- department-scoped operational information.

Do not show operational approval controls to field roles.

## UI enforcement
- Hide controls users cannot use.
- Block direct invocation where practical.
- Never rely on UI hiding as the only security layer.
- Unauthorized API calls return 403.
- Missing/invalid credentials return 401.

## Route handling
Where the static-page architecture cannot provide route middleware, page initialization must enforce the session/role policy, while sensitive backend mutations remain protected server-side.

## Role-switch acceptance test
1. Login Controller and record dashboard/sidebar/actions.
2. Sign out.
3. Login Engineer and compare.
4. Login TRD and compare.
5. Login S&T and compare.

The differences must be substantive, not just avatar/label changes.

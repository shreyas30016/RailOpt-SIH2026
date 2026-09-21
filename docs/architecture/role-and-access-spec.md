# RailOpt — Role and Access Specification

## Supported roles

| Role | Key | Approve | Optimize | Edit/Submit | Intended authority |
|---|---|---:|---:|---:|---|
| Controller | `CONTROLLER` | Yes | Yes | Yes | Full operational authority |
| Planner | `PLANNER` | Yes | Yes | Yes | Planning/review authority |
| Engineer | `ENGINEER` | No | No | Yes | Civil/engineering demand submitter |
| TRD Officer | `TRD_OFFICER` | No | No | Yes | TRD/OHE demand submitter |
| S&T Officer | `ST_OFFICER` | No | No | Yes | Signal & telecom demand submitter |

## Controller
Landing: operational dashboard.

Can:
- view KPIs/train movement;
- manage maintenance requests;
- approve/defer eligible requests;
- run optimization;
- run permitted What-If scenarios;
- inspect Gantt, constraints, explanations and reports;
- perform final operational actions allowed by the current backend policy.

## Planner
Landing: planning-focused operational/block-planning context.

Can:
- review maintenance demand;
- run optimization;
- compare/review plans;
- perform approval actions allowed by the documented policy.

## Engineer
Landing: departmental maintenance workflow.

Can:
- view relevant requests;
- create/submit Civil Engineering requests;
- review request status;
- use permitted read-only planning information.

Cannot:
- approve/defer;
- run system-wide optimization;
- run restricted What-If actions.

## TRD Officer
Landing: departmental maintenance workflow.

Can:
- view/review relevant TRD/OHE requests;
- create/submit TRD/OHE requests;
- use permitted read-only planning information.

Cannot:
- approve/defer;
- run restricted optimization/replanning actions.

## S&T Officer
Landing: departmental maintenance workflow.

Can:
- view/review relevant S&T requests;
- create/submit S&T requests;
- use permitted read-only planning information.

Cannot:
- approve/defer;
- run restricted optimization/replanning actions.

## Department scoping
For field roles, derive the permitted department from the authenticated role/session.

Changing a request payload's department value must not grant cross-department access.

## Division behavior
Keep the selected division visible in the authenticated session/header context.

Do not claim that every division has unique live railway data unless such integration actually exists. Synthetic/demo corridor data must be labeled.

## Critical acceptance test
Selecting Engineer + S&T context must NOT result in the same unrestricted operational experience as Controller.

The UI and backend must both reflect the role.

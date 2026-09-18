# RailOpt — Judge Demo Scenario

## Objective
Demonstrate a working optimization/decision-support system rather than a static dashboard.

## Primary demo
1. Login as Controller.
2. Open Operations Dashboard.
3. Show synthetic/demo label where applicable.
4. Open Maintenance Requests.
5. Show a real database-backed request.
6. Run optimization.
7. Show scheduled and unscheduled work.
8. Open Gantt View.
9. Select a scheduled job.
10. Open “Why this plan?” / decision explanation.
11. Open What-If.
12. Introduce a train delay.
13. Re-run the scenario.
14. Show Before vs After schedule differences and KPI deltas.
15. Explain that the solver recomputed a feasible plan under railway constraints.
16. Return to review/approval.

## Role differentiation demo
Repeat login with:
- Engineer;
- TRD Officer;
- S&T Officer.

Show:
- different operational focus;
- department-scoped requests;
- no approval/optimization actions;
- direct API protection still works.

## What judges should observe
- input changes produce computed output changes;
- Gantt corresponds to backend data;
- maintenance selection updates the detail panel;
- explanation corresponds to the selected job;
- role changes alter available actions.

## Avoid
- fake AI chat;
- static charts;
- hardcoded Gantt bars;
- fake internal-system access claims;
- manually changing numbers to look live.

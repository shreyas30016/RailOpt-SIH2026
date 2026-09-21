# RailOpt — Agent Entry Rules

## Project
SIH 2026 · SIH26027 — AI-Powered Automatic Block Planning System for Indian Railways.

Repository:
`A:\SHREYAS\RAILWAY BLOCK AI`

## Mandatory reading order
Before changing code, read these files in order:

1. `AGENTS.md`
2. `docs/architecture/project-rules.md`
3. `docs/architecture/role-and-access-spec.md`
4. `docs/architecture/ui-navigation-spec.md`
5. `docs/architecture/api-rbac-contract.md`
6. `docs/development/demo-scenario.md`
7. `PROJECT_MEMORY.md`

Then inspect the actual source code and existing tests.

## Core principle
This is a working decision-support prototype, not a static UI mockup.

Architecture:
`Prediction / data → Railway safety constraints → OR-Tools CP-SAT → recommended plan → human approval`

## Non-negotiable rules
- Preserve the existing Stitch visual language and railway-enterprise look.
- Do not rewrite the project from scratch.
- Do not replace working backend/solver architecture with mock UI logic.
- Do not hardcode runtime business outputs into HTML.
- Synthetic demo data is allowed when it is persisted/served dynamically and clearly presented as synthetic/demo data.
- Client fallbacks may remain for offline judging, but must not silently masquerade as live railway data.
- Do not claim access to internal Indian Railways/NTES/COA systems unless a real integration exists.
- Do not change OR-Tools mathematical constraints casually.
- Every new interactive control must have a real state transition, API call, or explicitly documented UI-only behavior.
- Role permissions must be enforced in the backend, not only hidden in the frontend.
- Do not start a second unrelated architecture while this repository is the active project.

## Sprint discipline
Work one sprint at a time.

At the end of every sprint:
- run targeted tests;
- run the complete regression suite;
- perform browser verification for changed flows;
- update `PROJECT_MEMORY.md`;
- create a concise sprint report in `docs/` when appropriate;
- stop and wait for the next sprint instruction.

Never silently broaden scope.

## Source of truth rule
These documents define intended behavior. If they conflict with actual code/tests:
1. investigate the conflict;
2. preserve already-working behavior where possible;
3. make the smallest justified change;
4. document the decision in `PROJECT_MEMORY.md`.

Do not invent requirements.

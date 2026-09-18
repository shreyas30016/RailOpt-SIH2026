# RailOpt — Project Rules

## 1. Product identity
RailOpt is an AI-assisted railway maintenance block-planning and decision-support system.

It should help an operational team:
- collect maintenance demands;
- understand train/track conflicts;
- generate a feasible block plan;
- compare alternatives;
- understand why the optimizer made a decision;
- simulate disruptions;
- review and approve the recommended plan.

## 2. What must stay real
Preserve:
- FastAPI backend;
- SQLAlchemy data model;
- SQLite/PostgreSQL compatibility where already implemented;
- OR-Tools CP-SAT optimizer;
- railway rule configuration;
- maintenance CRUD;
- live-train adapter/fallback;
- What-If differential re-optimization;
- Gantt rendering;
- decision explanation;
- reports/analytics;
- automated tests.

## 3. Synthetic data policy
Realistic synthetic seed data is acceptable for offline judging:
- sections;
- track lines;
- maintenance jobs;
- train movements;
- block windows.

Clearly label demo/synthetic data.

## 4. Hardcoding policy
### Allowed
- role definitions;
- division dictionaries;
- fixed engineering/safety parameters;
- application configuration;
- synthetic seed fixtures;
- UI labels.

### Not allowed
- hardcoded KPI values presented as current database results;
- static solver results replacing the solver;
- static Gantt bars replacing API-driven schedule output;
- static maintenance detail panels that ignore the selected request;
- fake claims of live internal railway-system access.

## 5. Optimization rule
Do not casually modify safety constraints, buffer logic, shadow-block pairing, or solver mathematics.

## 6. Authentication and authorization
Authentication is a lightweight prototype.

Authorization must be genuine:
- frontend guards improve UX;
- backend guards provide actual security;
- protected mutations validate the authenticated session/token server-side;
- role/division must not be trusted only from request payloads.

## 7. UI rule
Preserve the existing railway enterprise visual system and component style.

Prefer targeted fixes over redesigns.

## 8. Demo rule
The strongest demo changes an input and produces a different computed outcome.

Example:
Train delay → What-If simulation → changed schedule → changed KPI/delta → explanation.

Avoid chatbot-first demos.

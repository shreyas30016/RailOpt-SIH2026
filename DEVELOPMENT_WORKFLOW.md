# RailOpt — AI Agent Development Workflow

## Before coding
Read the required markdown files listed in `AGENTS.md`.

Inspect:
- relevant frontend page;
- relevant API/data service;
- relevant backend router;
- auth/permission helpers;
- existing tests.

## During coding
Prefer the smallest change that satisfies the sprint.

Avoid:
- rewrites;
- duplicate services;
- unnecessary frameworks;
- unrelated database migrations;
- changes to solver mathematics outside the sprint.

## After coding
Run:
1. targeted tests;
2. full `pytest tests/ -v`;
3. browser verification of affected flows;
4. browser-console/error check;
5. documentation update.

## Browser QA standard
For each changed interactive element verify:
- visible;
- clickable;
- correct handler;
- correct request/API behavior;
- loading state;
- success state;
- error state;
- resulting UI state.

## Sprint report
Use:
### Changed
Files and descriptions.

### Behavior
User-visible changes.

### Tests
Commands and pass/fail counts.

### Browser QA
Exact flows exercised.

### Risks / known limitations
Intentional limitations.

### Next
One sentence only. Do not start the next sprint automatically.

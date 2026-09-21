# Contributing to RailOpt

Thank you for contributing to RailOpt (SIH 2026 · Problem Statement SIH26027).

---

## Development Principles

1. **Safety First**:
   This is a railway decision-support system. Hard constraints (train headway safety buffers, non-overlap, machine exclusivity) are mathematical invariants. Never soften or bypass safety rules.

2. **Deterministic Optimization**:
   The primary scheduler is **Google OR-Tools CP-SAT**, not a heuristic or LLM approximation. The AI copilot provides explanations, queries, and scenarios; it does NOT directly schedule trains or alter database tables without controller approval.

3. **Role Scoping (RBAC)**:
   Any new endpoint or interactive UI element must declare its required permissions. Permissions are enforced on the backend via server-authoritative checks.

4. **No Synthetic Misrepresentation**:
   Corridor data, timetables, and train movements are simulated for demonstration purposes. Never label demo feeds as "live Indian Railways data" without an active, authentic external feed integration.

---

## Contribution Workflow

1. Fork the repository and create a feature branch:
   ```bash
   git checkout -b feature/my-feature-name
   ```
2. Make your changes adhering to the coding standards:
   - Python code must follow PEP 8 and use type hints.
   - JavaScript frontend code must use ES modules without unnecessary external frameworks.
3. Write or update automated tests in `tests/`.
4. Run the full regression test suite:
   ```bash
   pytest tests/ -v
   ```
5. Ensure no secrets, keys, or database files are committed.
6. Submit a Pull Request describing:
   - What problem is addressed
   - What changed
   - Test results and verification steps

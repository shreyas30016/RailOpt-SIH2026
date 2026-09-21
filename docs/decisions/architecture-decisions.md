# Architecture Decision Records (ADRs)

This document captures the key architectural and design decisions made throughout the RailOpt project.

---

## ADR-01: Google OR-Tools CP-SAT as Primary Optimization Engine
- **Status**: Accepted
- **Context**: Railway maintenance block scheduling is an NP-hard combinatorial problem with strict safety constraints (non-overlap, machine exclusivity, train headway) and multi-objective trade-offs (passenger delay vs maintenance execution).
- **Decision**: Use **Google OR-Tools CP-SAT** constraint programming rather than heuristics, genetic algorithms, or pure LLMs.
- **Consequences**:
  - Positive: 100% mathematical guarantee of safety constraint satisfaction, deterministic reproducibility, global optimality bounds.
  - Negative: Requires C++ binary wheels (~100 MB), precluding deployment on lightweight serverless runtimes.

---

## ADR-02: Decoupled Frontend (Vercel) & Backend (External Container Host)
- **Status**: Accepted
- **Context**: Vercel Serverless Functions enforce a 50 MB compressed bundle limit and 10–15 second timeouts, which conflicts with OR-Tools binary requirements and 60-second optimization budgets.
- **Decision**: Deploy the static UI on **Vercel Edge Network** (`frontend/`) and host the FastAPI + OR-Tools backend on a dedicated container platform (Render, Railway, Fly.io, or AWS).
- **Consequences**:
  - Positive: Instant global edge CDN delivery for UI, unlimited execution budget and memory for CP-SAT solver, clear separation of concerns.
  - Negative: Requires setting `API_BASE_URL` in frontend configuration to bridge the two domains.

---

## ADR-03: AI Copilot Role & Safety Boundary Filter
- **Status**: Accepted
- **Context**: Large language models can hallucinate or suggest actions violating railway safety protocols if given unconstrained access to execution APIs.
- **Decision**: Implement a **two-tier architecture**:
  1. DeepSeek V4 Flash / NVIDIA NIM provides intent classification, query routing, and natural language explanations.
  2. A deterministic Python safety layer inspects all tool invocations and strictly forbids direct database mutations or safety bypasses.
- **Consequences**:
  - Positive: Safety invariants cannot be compromised by prompt injection or model hallucinations.
  - Negative: Copilot actions are limited to explainability, simulation initiation, and querying.

---

## ADR-04: Server-Enforced Role-Based Access Control (RBAC)
- **Status**: Accepted
- **Context**: Railway operations demand strict division of authority between Section Controllers, Block Planners, and Field Officers.
- **Decision**: Implement server-authoritative role verification on every API route.
- **Consequences**:
  - Positive: Prevents unauthorized block approvals or solver budget modifications regardless of client-side manipulations.
  - Current Prototype Limitation: Authentication currently relies on a Base64-encoded token for local judging/demo purposes, requiring future replacement with cryptographically signed JWTs.

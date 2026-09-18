"""
RailOpt AI Copilot Architecture
================================
Provider-agnostic AI orchestration layer for the RailOpt Railway Planning Assistant.

Architecture layers:
  provider.py     — AIProvider ABC + MockAIProvider (live providers added tomorrow)
  tools.py        — RailOptToolRegistry (9 tools, each wired to an existing backend API)
  intent.py       — Intent enum + keyword-based IntentClassifier
  orchestrator.py — AIOrchestrator (message → intent → tool → result)
  safety.py       — AISafetyBoundary contract constants and validators
  schemas.py      — Pydantic schemas for ChatRequest / ChatResponse / ToolCall / ToolResult

Design principles:
  - AI is an INTERPRETER/ORCHESTRATOR only.
  - The RailOpt backend is the SOLE source of truth.
  - OR-Tools CP-SAT is the COMPUTATION ENGINE.
  - Railway safety constraints are HARD INVARIANTS — unreachable by AI.
  - Human operators are the FINAL DECISION MAKERS.
  - AI must NEVER become a privilege-escalation path.
"""

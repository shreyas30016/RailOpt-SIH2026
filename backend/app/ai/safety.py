"""
RailOpt AI — Safety Boundary Contract
=======================================

This module documents and enforces the hard safety boundary between the AI
layer and the RailOpt backend / OR-Tools solver.

Principle:
  AI = interpreter / orchestrator only
  RailOpt backend = source of truth
  OR-Tools CP-SAT = computation engine
  Railway constraints = safety authority
  Human operator = final decision maker

The AI layer must NEVER:
  1. Directly mutate the database.
  2. Bypass the backend RBAC (every action must go through the existing API).
  3. Invent solver results or claim a plan is feasible without backend validation.
  4. Approve, defer, or modify maintenance requests without backend authorization.
  5. Fabricate train positions or railway network data.
  6. Modify hard safety constraints (machine exclusivity, headway buffers, track overlap).
  7. Present unavailable data as available — return data_unavailable=True instead.
"""

from __future__ import annotations
from typing import List


# ---------------------------------------------------------------------------
# Hard-coded prohibited action constants
# ---------------------------------------------------------------------------

AI_PROHIBITED_ACTIONS: List[str] = [
    "direct_db_mutation",
    "bypass_backend_rbac",
    "invent_solver_results",
    "fabricate_train_positions",
    "fabricate_network_data",
    "approve_without_backend_authorization",
    "defer_without_backend_authorization",
    "modify_hard_safety_constraints",
    "claim_feasibility_without_solver_validation",
]

# Railway safety constraints that are MATHEMATICAL HARD CONSTRAINTS
# in the CP-SAT solver and must never be weighted, relaxed, or bypassed.
HARD_SAFETY_CONSTRAINTS: List[str] = [
    "machine_exclusivity_no_overlap",       # AddNoOverlap — one machine, one job at a time
    "track_line_non_overlap",               # Two jobs cannot share the same track simultaneously
    "train_headway_buffer_minutes",         # Minimum headway gap before/after passenger trains
    "power_25kv_isolation_synchrony",       # 25kV OHE blocks must be synchronised with traffic blocks
    "department_compatibility_matrix",      # Only compatible departments may form shadow blocks
]

# These permissions are GRANTED by the existing backend — NOT by the AI layer.
# AI must pre-check before invoking a tool, but the backend is the authority.
BACKEND_PERMISSION_AUTHORITY = "railopt_backend_rbac"


class AISafetyViolation(Exception):
    """
    Raised when the AI orchestrator detects an attempt to perform a prohibited action.
    This exception surfaces to the user as a structured refusal in ChatResponse.
    """
    def __init__(self, action: str, user_message: str = ""):
        self.action = action
        self.user_message = user_message
        super().__init__(
            f"AI Safety Boundary violated: action '{action}' is prohibited. "
            f"User query: '{user_message}'"
        )


def validate_tool_not_prohibited(tool_name: str, action_type: str) -> None:
    """
    Raises AISafetyViolation if the requested tool maps to a prohibited action.
    Called by AIOrchestrator before executing any tool.
    """
    # The AI tool layer must never call these internal actions directly.
    # All mutations go through existing authenticated backend endpoints.
    prohibited_tool_actions = {
        "direct_db_write",
        "direct_db_delete",
        "bypass_auth",
        "inline_status_change",
    }
    if action_type in prohibited_tool_actions:
        raise AISafetyViolation(action=action_type)


def build_refusal_message(action_description: str, role: str) -> str:
    """
    Return a structured refusal message when a user attempts a prohibited action.
    Used when role lacks permission, or action is fundamentally prohibited.
    """
    return (
        f"I cannot perform '{action_description}' for your current role ({role}). "
        "This action requires authorization through the RailOpt backend. "
        "Please use the Maintenance Requests page or contact a Controller/Planner to take this action."
    )


def build_data_unavailable_message(query: str) -> str:
    """
    Return a structured 'data unavailable' message rather than hallucinating.
    Used when a tool call returns no data from the backend.
    """
    return (
        f"The information you requested ('{query}') is currently unavailable from the RailOpt backend. "
        "This could mean no optimization has been run yet, or the requested data does not exist. "
        "Please ensure a block plan has been generated before querying this information."
    )

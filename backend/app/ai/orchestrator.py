"""
RailOpt AI — Orchestrator
===========================

AIOrchestrator ties together:
  1. IntentClassifier — maps the user message to a structured Intent
  2. RailOptToolRegistry — selects the appropriate tool
  3. RBAC pre-check — validates the authenticated user's permissions before tool execution
  4. AIProvider — generates the human-readable response from tool results
  5. AISafetyBoundary — ensures prohibited actions are refused with a structured message

Flow:
  User message
      → IntentClassifier.classify()
          → ToolSpec selection
              → RBAC pre-check (current_user permissions)
                  → ToolSpec.execute(args, db)
                      → AIProvider.generate(response)
                          → ChatResponse

The existing backend endpoints remain the AUTHORITY on all data and permissions.
This orchestrator is a thin, stateless routing layer.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from .schemas import (
    ChatRequest, ChatResponse, ClassifiedIntent, Intent,
    ToolCallRequest, ToolCallResult,
)
from .intent import IntentClassifier
from .tools import RailOptToolRegistry
from .provider import AIProvider, MockAIProvider
from .safety import (
    AISafetyViolation, build_refusal_message, build_data_unavailable_message,
)


# Intent → preferred tool mapping
_INTENT_TO_TOOL: Dict[Intent, Optional[str]] = {
    Intent.QUERY:      "get_maintenance_requests",
    Intent.EXPLAIN:    "get_job_explanation",
    Intent.OPTIMIZE:   "run_optimization",
    Intent.WHAT_IF:    "run_what_if",
    Intent.REPORT:     "get_reports_analytics",
    Intent.NAVIGATION: None,   # No tool needed — just a navigation hint
    Intent.UNKNOWN:    "get_dashboard_summary",  # Safe fallback
}

# Navigation intent → URL mapping
_NAVIGATION_URLS: Dict[str, str] = {
    "gantt":    "/block-planning",
    "planning": "/block-planning",
    "dashboard": "/dashboard",
    "maintenance": "/maintenance-requests",
    "reports":  "/reports",
    "whatif":   "/what-if",
}

# System prompt sent to the AI provider
_SYSTEM_PROMPT = """You are the RailOpt Railway Planning Copilot, an AI assistant for Indian Railways block planning operations.

You help Controllers, Planners, and Field Engineers understand maintenance schedules, optimization results, and safety decisions.

Strict rules you must ALWAYS follow:
1. Only report information from the tool results provided. Never invent data.
2. If tool result shows data_unavailable=true, say clearly that the data is not available.
3. You cannot approve, defer, or modify maintenance requests. Direct the user to the UI.
4. You cannot change hard railway safety constraints.
5. Be precise and professional — this is safety-critical railway infrastructure.
6. Always mention the job_code, run_id, or specific metric when discussing results.
7. Keep responses concise and actionable — under 200 words.
"""


class AIOrchestrator:
    """
    Stateless AI orchestrator for the RailOpt Railway Planning Copilot.
    One instance per request — receives authenticated user context.
    """

    def __init__(
        self,
        provider: AIProvider,
        db: Session,
        current_user: Dict[str, Any],
    ):
        self._provider = provider
        self._db = db
        self._user = current_user
        self._classifier = IntentClassifier()
        self._registry = RailOptToolRegistry()

    def process(self, request: ChatRequest) -> ChatResponse:
        """
        Main entry point. Process a ChatRequest and return a ChatResponse.
        Never raises — all errors are wrapped in ChatResponse.
        """
        try:
            return self._process_internal(request)
        except AISafetyViolation as e:
            role = self._user.get("role", "UNKNOWN")
            return ChatResponse(
                message=build_refusal_message(e.action, role),
                intent=Intent.UNKNOWN,
                safety_note=f"Action '{e.action}' is prohibited by the RailOpt AI safety boundary.",
                data_source="railopt_backend",
            )
        except Exception as e:
            return ChatResponse(
                message=(
                    "I encountered an unexpected error processing your request. "
                    "Please try again or use the RailOpt interface directly. "
                    f"Error: {str(e)[:100]}"
                ),
                intent=Intent.UNKNOWN,
                data_source="railopt_backend",
            )

    def _process_internal(self, request: ChatRequest) -> ChatResponse:
        # 1. Classify intent
        classified: ClassifiedIntent = self._classifier.classify(request.message)
        intent = classified.intent
        entities = classified.extracted_entities

        # 2. Select tool
        tool_name = self._select_tool(intent, entities, request)

        # 3. Handle navigation intent (no tool needed)
        if intent == Intent.NAVIGATION or tool_name is None:
            return self._handle_navigation(request.message, intent)

        # 4. Check tool exists
        tool_spec = self._registry.get(tool_name)
        if not tool_spec:
            return self._unknown_response(request.message)

        # 5. RBAC pre-check — refuse before hitting backend
        if tool_spec.required_permission:
            if not self._user.get(tool_spec.required_permission, False):
                role = self._user.get("role", "UNKNOWN")
                return ChatResponse(
                    message=build_refusal_message(
                        f"use '{tool_name}' (requires {tool_spec.required_permission})", role
                    ),
                    intent=intent,
                    tool_used=tool_name,
                    data_source="railopt_backend",
                    safety_note=f"User role '{role}' lacks permission '{tool_spec.required_permission}'.",
                )

        # 6. Build tool arguments from entities + context
        tool_args = self._build_tool_args(tool_name, entities, request.context or {})

        # 7. Execute tool (delegates to existing backend service)
        tool_result: ToolCallResult = tool_spec.execute(tool_args, self._db)

        # 8. Generate response via AI provider
        ai_text = self._generate_response(request.message, intent, tool_result)

        # 9. Build action suggestions
        suggestions = self._build_suggestions(intent, tool_result, entities)

        return ChatResponse(
            message=ai_text,
            intent=intent,
            tool_used=tool_name,
            tool_result=tool_result,
            action_suggestions=suggestions,
            data_source="railopt_backend" if not tool_result.data_unavailable else "unavailable",
        )

    def _select_tool(
        self,
        intent: Intent,
        entities: Dict[str, Any],
        request: ChatRequest,
    ) -> Optional[str]:
        """Refine tool selection using extracted entities."""
        # Explain with a job_code → get_job_explanation
        if intent == Intent.EXPLAIN and entities.get("job_code"):
            return "get_job_explanation"
        # Query with a job_code → get specific request
        if intent == Intent.QUERY and entities.get("job_code"):
            return "get_maintenance_request"
        # Dashboard query → summary
        msg_lower = request.message.lower()
        if intent == Intent.QUERY and any(
            kw in msg_lower for kw in ["dashboard", "summary", "overview", "kpi"]
        ):
            return "get_dashboard_summary"
        # Pending/unscheduled → unscheduled jobs
        if intent == Intent.QUERY and any(
            kw in msg_lower for kw in ["pending", "unscheduled", "not scheduled"]
        ):
            return "get_unscheduled_jobs"
        # Gantt query → timeline
        if intent == Intent.QUERY and "gantt" in msg_lower:
            return "get_gantt_timeline"
        # Train status / live-position question → honest feed lookup (never fabricated)
        if intent == Intent.QUERY and entities.get("train_number") and any(
            kw in msg_lower
            for kw in [
                "position", "live", "location", "running", "movement", "tracking",
                "status", "where", "delayed", "delay", "late", "depart", "arriv", "time",
            ]
        ):
            return "get_train_status"
        return _INTENT_TO_TOOL.get(intent)

    def _generate_response(
        self,
        user_message: str,
        intent: Intent,
        tool_result: ToolCallResult,
    ) -> str:
        """Ask the AI provider to generate a human-readable response from tool results."""
        if tool_result.data_unavailable:
            return build_data_unavailable_message(user_message)

        if not tool_result.success:
            return (
                f"I was unable to retrieve the requested information: {tool_result.error or 'unknown error'}. "
                "Please check the RailOpt backend or try again."
            )

        data_str = json.dumps(tool_result.data or {}, indent=2)[:1500]
        messages = [
            {
                "role": "user",
                "content": (
                    f"User asked: {user_message}\n\n"
                    f"Tool '{tool_result.tool_name}' returned this real data:\n{data_str}\n\n"
                    "Provide a concise, professional response based ONLY on this data."
                )
            }
        ]
        try:
            return self._provider.generate(
                messages=messages,
                system_prompt=_SYSTEM_PROMPT,
                max_tokens=512,
                temperature=0.1,
            )
        except Exception as e:
            # Fallback gracefully to deterministic summary derived from tool_result data if provider times out or has transient issue
            return self._format_deterministic_fallback(tool_result, user_message)

    def _format_deterministic_fallback(self, tool_result: ToolCallResult, user_message: str) -> str:
        """Deterministic summary of backend tool result when remote LLM provider is slow or unreachable."""
        t_name = tool_result.tool_name
        data = tool_result.data or {}
        if t_name == "get_dashboard_summary":
            return (
                f"Operational Summary: {data.get('total_jobs', 0)} total maintenance jobs, "
                f"{data.get('pending_jobs', 0)} pending review, {data.get('critical_high_jobs', 0)} critical/high priority. "
                f"Latest optimization run #{data.get('latest_run_id', 'N/A')} status: {data.get('latest_run_status', 'N/A')} "
                f"({data.get('latest_scheduled_count', 0)} scheduled blocks)."
            )
        elif t_name == "get_maintenance_requests" or t_name == "get_unscheduled_jobs":
            jobs = data.get("jobs", [])
            job_summary = ", ".join([f"{j.get('job_code')} ({j.get('status')})" for j in jobs[:5]])
            return f"Found {data.get('count', len(jobs))} maintenance requests. Top items: {job_summary}."
        elif t_name == "get_maintenance_request":
            return (
                f"Request {data.get('job_code')}: {data.get('title')}. "
                f"Status: {data.get('status')}, Urgency: {data.get('urgency')}, Duration: {data.get('duration_minutes')}m."
            )
        elif t_name == "get_job_explanation":
            return f"Decision explanation for {data.get('job_code', 'job')}: {data.get('message', 'Decision data loaded from backend.')}"
        elif t_name == "get_gantt_timeline":
            return f"Gantt timeline for run #{data.get('run_id')}: {data.get('scheduled_blocks_count', 0)} blocks plotted."
        elif t_name == "get_reports_analytics":
            return f"Analytics report: {data.get('total_runs', 0)} optimization runs, grant ratio {data.get('grant_ratio_pct')}%."
        elif t_name == "get_train_status":
            if data.get("found_in_feed"):
                return (
                    f"Train {data.get('train_number')} ({data.get('train_name')}) is currently {data.get('status')} "
                    f"at {data.get('current_location')}, heading towards {data.get('next_location')}. "
                    f"Delay: {data.get('delay_minutes', 0)} min. Source: {data.get('source')}."
                )
            if data.get("in_timetable"):
                return (
                    f"Train {data.get('train_number')} ({data.get('train_name')}) is in the corridor timetable "
                    f"({data.get('origin_station')} → {data.get('destination_station')}) but has no live movement entry "
                    f"in the current feed. Source: {data.get('source')}."
                )
            return (
                f"Train {data.get('train_number')} is not present in the {data.get('source')} corridor feed, so no live "
                "position is available. RailOpt does not claim live GPS tracking of trains outside this dataset."
            )
        return f"Backend result retrieved from {t_name}: {json.dumps(data)[:200]}."


    def _handle_navigation(self, message: str, intent: Intent) -> ChatResponse:
        msg_lower = message.lower()
        suggestions = []
        response = "I can help you navigate RailOpt."
        for keyword, url in _NAVIGATION_URLS.items():
            if keyword in msg_lower:
                suggestions.append({"label": f"Open {keyword.title()}", "href": url})
                response = f"Here's a link to the {keyword.title()} section."
                break
        return ChatResponse(
            message=response,
            intent=intent,
            action_suggestions=suggestions,
            data_source="railopt_backend",
        )

    def _unknown_response(self, message: str) -> ChatResponse:
        return ChatResponse(
            message=(
                "I'm not sure how to help with that specific query. "
                "I can assist with: viewing maintenance requests, explaining scheduling decisions, "
                "running block plan optimization (Controller/Planner only), "
                "simulating disruption scenarios, and viewing analytics. "
                "Try rephrasing your question."
            ),
            intent=Intent.UNKNOWN,
            data_source="railopt_backend",
        )

    def _build_tool_args(
        self,
        tool_name: str,
        entities: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build tool arguments from classified entities and frontend context."""
        args: Dict[str, Any] = {}
        if "job_code" in entities:
            args["job_code"] = entities["job_code"]
        if "department_code" in entities:
            args["department_code"] = entities["department_code"]
        if "delay_minutes" in entities:
            args["delay_minutes"] = entities["delay_minutes"]
        if "train_number" in entities:
            args["train_number"] = entities["train_number"]
        # Merge frontend context (e.g. currently selected run_id)
        if "run_id" in context:
            args["run_id"] = context["run_id"]

        # Server-side department scoping for field roles: an Engineer/TRD/S&T
        # officer can only ever query their own department's maintenance data
        # through the AI copilot, mirroring the REST endpoint enforcement.
        if tool_name in ("get_maintenance_requests", "get_unscheduled_jobs"):
            role_dept_map = {
                "ENGINEER": "ENG",
                "TRD_OFFICER": "TRD",
                "ST_OFFICER": "S_T",
            }
            user_role = (self._user.get("role") or "").upper()
            if user_role in role_dept_map:
                args["department_code"] = role_dept_map[user_role]

        return args

    def _build_suggestions(
        self,
        intent: Intent,
        tool_result: ToolCallResult,
        entities: Dict[str, Any],
    ) -> list:
        suggestions = []
        if intent == Intent.OPTIMIZE and tool_result.success and tool_result.data:
            run_id = tool_result.data.get("run_id")
            if run_id:
                suggestions.append({"label": "Open Block Plan & Gantt", "href": "/block-planning"})
        if intent == Intent.EXPLAIN:
            suggestions.append({"label": "View Decision Audit", "href": "/block-planning"})
        if intent == Intent.QUERY:
            suggestions.append({"label": "Open Maintenance Requests", "href": "/maintenance-requests"})
        if intent == Intent.REPORT:
            suggestions.append({"label": "Open Full Reports", "href": "/reports"})
        if intent == Intent.WHAT_IF and tool_result.success:
            suggestions.append({"label": "Open What-If Simulator", "href": "/what-if"})
        return suggestions

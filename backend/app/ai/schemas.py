"""
RailOpt AI — Pydantic schemas for the AI copilot chat layer.

These schemas define the contract between:
  - the frontend chat UI → POST /api/ai/chat
  - the AIOrchestrator → tool calls
  - tool results → structured response

NO business logic lives here. Only data contracts.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Intent
# ---------------------------------------------------------------------------

class Intent(str, Enum):
    QUERY      = "query"       # "Show me pending maintenance jobs"
    EXPLAIN    = "explain"     # "Why was JOB-ENG-101 scheduled at 02:10?"
    OPTIMIZE   = "optimize"    # "Run block plan with higher delay priority"
    WHAT_IF    = "what_if"     # "What if Train 12050 is delayed 30 minutes?"
    REPORT     = "report"      # "Show analytics for the ENG department"
    NAVIGATION = "navigation"  # "Take me to the Gantt chart"
    UNKNOWN    = "unknown"     # Classifier could not determine intent


# ---------------------------------------------------------------------------
# Tool Call / Result
# ---------------------------------------------------------------------------

class ToolCallRequest(BaseModel):
    tool_name: str = Field(..., description="Registered tool name from RailOptToolRegistry")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Validated tool arguments")


class ToolCallResult(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    data_unavailable: bool = False  # True when backend has no data (not a hallucination)


# ---------------------------------------------------------------------------
# Chat request / response
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000,
                         description="User's natural language query")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional frontend context (current page, selected job_code, run_id, etc.)"
    )


class ClassifiedIntent(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    extracted_entities: Dict[str, Any] = Field(default_factory=dict,
        description="Entities parsed from the message, e.g. job_code, train_number, delay_min")


class ChatResponse(BaseModel):
    message: str = Field(..., description="Human-readable AI response text")
    intent: Intent
    tool_used: Optional[str] = None
    tool_result: Optional[ToolCallResult] = None
    action_suggestions: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Optional UI action hints, e.g. [{label: 'Open in Gantt', href: '/block-planning'}]"
    )
    data_source: str = Field(
        default="railopt_backend",
        description="Always 'railopt_backend' for real data, 'unavailable' when data cannot be fetched"
    )
    safety_note: Optional[str] = None  # Present when AI declines a prohibited action


# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------

class AIProviderConfig(BaseModel):
    provider: str = Field(default="mock", description="Provider name: 'mock', 'nvidia', 'anthropic', 'openai', 'gemini'")
    api_key: str = Field(default="", description="API key (never logged, never hardcoded)")
    model: str = Field(default="mock-model", description="Model identifier string")
    base_url: Optional[str] = Field(default=None, description="Custom base URL for OpenAI-compatible providers")
    max_tokens: int = Field(default=1024, ge=64, le=8192)
    temperature: float = Field(default=0.1, ge=0.0, le=1.0,
        description="Low temperature for deterministic railway planning responses")

"""
RailOpt AI — Chat API Endpoint
=================================

POST /api/ai/chat

Authenticated endpoint that processes natural-language queries through
the RailOpt AI Copilot pipeline.

Authentication:
  Same Bearer token used for all other RailOpt endpoints.
  Role permissions are pre-checked against existing RBAC before any tool execution.

Rate / safety:
  The AI layer cannot mutate data directly — all writes go through existing
  authenticated endpoints with independent RBAC enforcement.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os

from ..database import get_db
from ..api.auth import get_current_user
from ..ai.schemas import ChatRequest, ChatResponse
from ..ai.provider import create_ai_provider, AIProviderConfigError
from ..ai.orchestrator import AIOrchestrator

router = APIRouter(prefix="/ai", tags=["AI Copilot"])


@router.post("/chat", response_model=ChatResponse)
def ai_chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """
    RailOpt AI Planning Copilot — natural language query endpoint.

    Accepts a user message and optional frontend context.
    Returns a structured response including:
      - AI-generated text (grounded in real backend data)
      - The tool used (if any)
      - The raw tool result (for UI rendering)
      - Optional action suggestions (navigation links)

    RBAC: Any authenticated user may call this endpoint.
    However, tools requiring elevated permissions (e.g. run_optimization)
    will be refused for field roles (Engineer, TRD, S&T) before execution.
    """
    try:
        provider = create_ai_provider()
    except AIProviderConfigError as e:
        raise HTTPException(
            status_code=503,
            detail=(
                f"AI provider is not configured: {e}. "
                "Set AI_PROVIDER, AI_API_KEY, and AI_MODEL environment variables."
            )
        )

    orchestrator = AIOrchestrator(
        provider=provider,
        db=db,
        current_user=current_user,
    )
    return orchestrator.process(request)


@router.get("/status")
def ai_status() -> dict:
    """
    Check AI provider configuration status without making a live API call.
    Returns which provider is configured and whether an API key is present.
    Does NOT expose the API key value.
    """
    provider_name = os.getenv("AI_PROVIDER", "mock").lower()
    has_api_key = bool(os.getenv("AI_API_KEY", ""))
    model = os.getenv("AI_MODEL", "mock-model")

    is_live = provider_name not in ("mock", "", "none", "disabled") and has_api_key

    return {
        "provider": provider_name,
        "model": model,
        "api_key_configured": has_api_key,
        "is_live": is_live,
        "status": "ready" if is_live else "mock_mode",
        "note": (
            "Live AI provider active." if is_live
            else "AI provider running in mock mode. Set AI_PROVIDER, AI_API_KEY, AI_MODEL to enable live responses."
        )
    }

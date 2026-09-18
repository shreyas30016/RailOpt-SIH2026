"""
RailOpt AI — Provider Abstraction
====================================

AIProvider is an abstract base class. All LLM providers implement it.
This makes the provider fully replaceable by changing one env variable.

Available implementations:
  MockAIProvider   — no network calls, used in tests and when AI_PROVIDER=mock
  NvidiaProvider   — NVIDIA NIM API (OpenAI-compatible) — connect tomorrow

Tomorrow's integration:
  1. Set AI_PROVIDER=nvidia in .env
  2. Set AI_API_KEY=nvapi-... in .env
  3. Set AI_MODEL=meta/llama-3.1-70b-instruct (or preferred NVIDIA NIM model)
  4. Instantiate NvidiaProvider — it uses the openai SDK with NVIDIA base URL.
  5. No other code changes required.
"""

from __future__ import annotations

import abc
import os
from typing import Any, Dict, List, Optional

from .schemas import AIProviderConfig


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class AIProviderConfigError(Exception):
    """
    Raised when a live AI provider is requested but required configuration
    (API key, model name) is missing. Surfaces as a clean 503 response,
    not a 500 crash.
    """
    def __init__(self, provider: str, missing_field: str):
        self.provider = provider
        self.missing_field = missing_field
        super().__init__(
            f"AI provider '{provider}' is not configured: missing '{missing_field}'. "
            "Set the required environment variables (AI_PROVIDER, AI_API_KEY, AI_MODEL) "
            "and restart the server."
        )


class AIProviderError(Exception):
    """Raised on recoverable provider API errors (rate limit, timeout, etc.)."""
    pass


# ---------------------------------------------------------------------------
# Abstract Base Class
# ---------------------------------------------------------------------------

class AIProvider(abc.ABC):
    """
    Abstract interface for all AI language model providers.

    The generate() method takes a list of messages (OpenAI-style chat format)
    and returns a plain text completion string.

    The structured_output() method returns a dict from a structured prompt.
    Implementations may use function-calling, JSON mode, or prompt engineering.
    """

    @abc.abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.1,
    ) -> str:
        """
        Generate a text completion from a list of chat messages.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."} dicts
            system_prompt: Optional system instruction prepended to messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (low for deterministic planning)

        Returns:
            Plain text completion string.

        Raises:
            AIProviderConfigError: If API key / model is not configured.
            AIProviderError: On API-level errors (rate limit, timeout).
        """

    @abc.abstractmethod
    def structured_output(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Request a structured (JSON) response from the provider.

        Args:
            prompt: The user instruction
            output_schema: Expected JSON schema for the response
            system_prompt: Optional system instruction

        Returns:
            Dict matching output_schema, or raises AIProviderError.
        """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name (e.g. 'nvidia', 'anthropic')."""


# ---------------------------------------------------------------------------
# Mock Provider — used in tests and local dev without an API key
# ---------------------------------------------------------------------------

class MockAIProvider(AIProvider):
    """
    Mock provider for tests, CI, and offline judging.
    Returns structured placeholder responses without making any network calls.
    Never used in production when a real provider is configured.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.1,
    ) -> str:
        """Returns a mock placeholder string. No network call."""
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            ""
        )
        return (
            f"[MOCK AI RESPONSE — no live provider configured] "
            f"Query received: '{last_user[:120]}'. "
            "Connect a real AI provider by setting AI_PROVIDER, AI_API_KEY, and AI_MODEL."
        )

    def structured_output(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Returns a mock empty structured response matching expected schema keys."""
        return {key: None for key in output_schema.get("properties", {}).keys()}


# ---------------------------------------------------------------------------
# NVIDIA NIM Provider — connect tomorrow
# ---------------------------------------------------------------------------

class NvidiaProvider(AIProvider):
    """
    NVIDIA NIM AI Provider — OpenAI-compatible API.

    Supports all NVIDIA NIM models including:
      - deepseek-ai/deepseek-v4-flash-0731  (thinking model, reasoning_content)
      - meta/llama-3.1-70b-instruct
      - meta/llama-3.1-8b-instruct
      - mistralai/mixtral-8x7b-instruct

    DeepSeek V4 Flash specifics:
      - Uses extra_body={"chat_template_kwargs": {"thinking": True, "reasoning_effort": "high"}}
      - Returns reasoning in completion.choices[0].message.reasoning_content
      - reasoning_content is captured internally but not surfaced in the response text
        (only the final answer is returned to the user)

    Environment:
      AI_PROVIDER=nvidia
      AI_API_KEY=nvapi-...
      AI_MODEL=deepseek-ai/deepseek-v4-flash-0731
      AI_BASE_URL=https://integrate.api.nvidia.com/v1  (default)
    """

    NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

    # Models that support DeepSeek-style thinking/reasoning
    THINKING_MODELS = {
        "deepseek-ai/deepseek-v4-flash-0731",
        "deepseek-ai/deepseek-r1-0528",
        "deepseek-ai/deepseek-r1",
    }

    def __init__(self, config: AIProviderConfig):
        if not config.api_key:
            raise AIProviderConfigError("nvidia", "AI_API_KEY")
        if not config.model:
            raise AIProviderConfigError("nvidia", "AI_MODEL")

        # Import lazily — openai package not required unless nvidia provider is used
        try:
            from openai import OpenAI
        except ImportError:
            raise AIProviderConfigError(
                "nvidia",
                "openai package (run: pip install openai)"
            )

        self._client = OpenAI(
            base_url=config.base_url or self.NVIDIA_BASE_URL,
            api_key=config.api_key,
            timeout=25.0,  # Prevent indefinite hangs on overloaded remote provider
        )
        self._model = config.model
        self._max_tokens = config.max_tokens
        self._temperature = config.temperature
        self._is_thinking_model = config.model in self.THINKING_MODELS

    @property
    def provider_name(self) -> str:
        return "nvidia"

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.1,
    ) -> str:
        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)

        try:
            kwargs: Dict[str, Any] = dict(
                model=self._model,
                messages=all_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,
            )

            # DeepSeek V4 Flash / thinking models: enable chain-of-thought reasoning
            if self._is_thinking_model:
                kwargs["extra_body"] = {
                    "chat_template_kwargs": {
                        "thinking": True,
                        "reasoning_effort": "high",
                    }
                }
                # DeepSeek requires top_p when thinking is enabled
                kwargs["top_p"] = 0.95

            completion = self._client.chat.completions.create(timeout=15.0, **kwargs)

            # Extract final answer (reasoning_content is internal chain-of-thought only)
            content = completion.choices[0].message.content or ""
            return content

        except Exception as e:
            raise AIProviderError(f"NVIDIA NIM API error: {e}") from e

    def structured_output(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        import json as _json
        schema_str = _json.dumps(output_schema, indent=2)
        system = (system_prompt or "") + (
            f"\n\nRespond ONLY with valid JSON matching this schema:\n{schema_str}\n"
            "Do not include markdown fences or any text outside the JSON object."
        )
        text = self.generate(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system,
            temperature=0.0,
        )
        try:
            # Strip markdown fences if model includes them despite instructions
            clean = text.strip()
            for fence in ("```json", "```"):
                if clean.startswith(fence):
                    clean = clean[len(fence):]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
            return _json.loads(clean)
        except Exception as e:
            raise AIProviderError(f"Failed to parse structured output from NVIDIA: {e}") from e


# ---------------------------------------------------------------------------
# Provider Factory
# ---------------------------------------------------------------------------

def create_ai_provider(config: Optional[AIProviderConfig] = None) -> AIProvider:
    """
    Factory function. Reads AI_PROVIDER env variable and returns the appropriate provider.

    If AI_PROVIDER is not set or is 'mock', returns MockAIProvider (no API key needed).
    If AI_PROVIDER is 'nvidia', returns NvidiaProvider (requires AI_API_KEY + AI_MODEL).
    """
    if config is None:
        config = AIProviderConfig(
            provider=os.getenv("AI_PROVIDER", "mock"),
            api_key=os.getenv("AI_API_KEY", ""),
            model=os.getenv("AI_MODEL", "mock-model"),
            base_url=os.getenv("AI_BASE_URL", None),
        )

    provider_name = config.provider.lower().strip()

    if provider_name in ("mock", "", "none", "disabled"):
        return MockAIProvider()
    elif provider_name == "nvidia":
        return NvidiaProvider(config)
    else:
        raise AIProviderConfigError(provider_name, f"unknown provider '{provider_name}'")

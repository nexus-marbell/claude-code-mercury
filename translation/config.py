"""Translation layer configuration.

Model name mapping, feature support matrix, and system prompt
template path. All configuration is centralized here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from enrichment.system_preamble import get_system_preamble


# Anthropic model name -> Inception Labs Mercury model name
MODEL_MAP: dict[str, str] = {
    "claude-sonnet-4-20250514": "mercury-2",
    "claude-opus-4-20250514": "mercury-2",
    "claude-haiku-3-20240307": "mercury-2",
    "claude-3-5-sonnet-20241022": "mercury-2",
    "claude-3-5-haiku-20241022": "mercury-2",
}

# OpenAI finish_reason -> Anthropic stop_reason
STOP_REASON_MAP: dict[str, str] = {
    "stop": "end_turn",
    "tool_calls": "tool_use",
    "length": "max_tokens",
    "content_filter": "end_turn",
}

# Features that degrade gracefully (log warning, continue)
DEGRADED_FEATURES: frozenset[str] = frozenset({
    "stop_sequences",
    "top_k",
    "metadata",
    "tool_choice",
})

# Features that fail loudly (raise NotImplementedError)
UNSUPPORTED_FEATURES: frozenset[str] = frozenset()

# Features stripped from requests (mapped to Mercury's native reasoning_effort)
STRIPPED_FEATURES: frozenset[str] = frozenset({
    "thinking",
})

# Valid reasoning_effort values for Mercury 2
VALID_REASONING_EFFORTS: frozenset[str] = frozenset({
    "instant", "low", "medium", "high",
})

# Mercury 2 temperature range
MERCURY_TEMP_MIN: float = 0.5
MERCURY_TEMP_MAX: float = 1.0


def _resolve_reasoning_effort() -> str:
    """Resolve reasoning_effort from env var with validation."""
    value = os.getenv("MERCURY_REASONING_EFFORT", "high")
    if value not in VALID_REASONING_EFFORTS:
        raise ValueError(
            f"Invalid MERCURY_REASONING_EFFORT='{value}'. "
            f"Must be one of: {', '.join(sorted(VALID_REASONING_EFFORTS))}"
        )
    return value


@dataclass(frozen=True)
class TranslationConfig:
    """Immutable translation configuration."""

    default_model: str = "mercury-2"
    default_temperature: float = 0.7
    default_max_tokens: int = 8192
    default_reasoning_effort: str = field(
        default_factory=_resolve_reasoning_effort
    )
    system_prompt_preamble: str = field(
        default_factory=get_system_preamble
    )
    inception_api_key: str = field(
        default_factory=lambda: os.getenv("INCEPTION_API_KEY", "")
    )

    def resolve_model(self, anthropic_model: str) -> str:
        """Map an Anthropic model name to a Mercury model name."""
        env_model = os.getenv("MERCURY_MODEL")
        if env_model:
            return env_model
        return MODEL_MAP.get(anthropic_model, self.default_model)

    def map_stop_reason(self, finish_reason: str | None) -> str | None:
        """Map OpenAI finish_reason to Anthropic stop_reason."""
        if finish_reason is None:
            return None
        return STOP_REASON_MAP.get(finish_reason, "end_turn")

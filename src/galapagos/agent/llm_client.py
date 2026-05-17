from __future__ import annotations

from typing import Any

from galapagos.agent.decision_parser import parse_decision_response_with_metadata
from galapagos.agent.decision_prompt import build_decision_prompt
from galapagos.agent.decision_schema import AgentDecision
from galapagos.agent.llm_providers import CodexCLIProvider, MockLLMProvider, OpenAICodexProvider


def build_provider(
    provider_name: str,
    *,
    allow_mock_fallback: bool = False,
    config: dict | None = None,
    mock_decision: str = "NO_TRADE",
):
    if provider_name == "openai-codex":
        return OpenAICodexProvider(config)
    if provider_name == "codex_cli":
        return CodexCLIProvider(config)
    if provider_name == "mock" or allow_mock_fallback:
        return MockLLMProvider(mock_decision)
    raise ValueError(f"Unsupported LLM provider: {provider_name}")


class LLMDecisionClient:
    def __init__(self, provider) -> None:
        self.provider = provider

    def decide(self, context: dict[str, Any]) -> tuple[AgentDecision, str, str]:
        profile = context.get("profile", {})
        messages = build_decision_prompt(context)
        raw = self.provider.complete(messages, context)
        parsed = parse_decision_response_with_metadata(
            raw,
            profile=profile.get("name", "unknown"),
            asset=profile.get("symbol", "unknown"),
            horizon=profile.get("timeframe", "unknown"),
        )
        return parsed.decision, raw, parsed.validity

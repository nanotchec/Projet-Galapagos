from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from galapagos.agent.decision_schema import AgentDecision, DecisionType, no_trade_decision


@dataclass(frozen=True)
class LLMSafetyResult:
    decision: AgentDecision
    flags: list[str]
    fallback_applied: bool


def apply_llm_safety(
    decision: AgentDecision,
    *,
    profile: dict[str, Any],
    risk_config: dict[str, Any],
    unavailable_features: list[str],
    recent_decisions: list[dict[str, Any]] | None = None,
    prompt_mode: str = "conservative",
) -> LLMSafetyResult:
    flags: list[str] = []
    max_risk = float(risk_config.get("max_risk_per_trade", 0.0) or 0.0)
    if decision.risk_fraction > max_risk:
        flags.append("risk_fraction_exceeds_max")
    if decision.confidence > 0.95:
        flags.append("suspicious_confidence")
    used_unavailable = sorted(set(decision.critical_data_used) & set(unavailable_features))
    if used_unavailable:
        flags.append("uses_unavailable_data:" + ",".join(used_unavailable))
    active = decision.decision in {DecisionType.LONG, DecisionType.SHORT}
    if active and len(unavailable_features) >= 4:
        if prompt_mode == "balanced":
            summary = decision.reasoning_summary.lower()
            if not any(
                term in summary
                for term in ["technical", "trend", "breakout", "momentum", "support", "resistance"]
            ):
                flags.append("balanced_missing_technical_compensation_for_unavailable_derivatives")
        else:
            flags.append("too_many_unavailable_features_for_active_decision")
    recent_decisions = recent_decisions or []
    active_streak = 0
    for item in reversed(recent_decisions):
        if item.get("decision") in {"LONG", "SHORT"}:
            active_streak += 1
        else:
            break
    cooldown_limit = 2 if prompt_mode == "balanced" else 3
    if active and active_streak >= cooldown_limit:
        flags.append("active_decision_cooldown")
    setup_quality = str(getattr(decision, "setup_quality", "poor") or "poor")
    if prompt_mode == "balanced" and active and setup_quality == "acceptable":
        acceptable_max = max_risk * 0.5 if max_risk else 0.0025
        if decision.risk_fraction > acceptable_max:
            flags.append("balanced_acceptable_setup_risk_too_high")
    fallback_flags = [
        flag
        for flag in flags
        if flag != "suspicious_confidence"
    ]
    if fallback_flags:
        return LLMSafetyResult(
            decision=no_trade_decision(
                profile=profile.get("name", decision.profile),
                asset=profile.get("symbol", decision.asset),
                horizon=profile.get("timeframe", decision.horizon),
                reason="LLM safety fallback: " + "; ".join(fallback_flags),
            ),
            flags=flags,
            fallback_applied=True,
        )
    return LLMSafetyResult(decision=decision, flags=flags, fallback_applied=False)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from galapagos.agent.decision_schema import AgentDecision, DecisionType, no_trade_decision


@dataclass(frozen=True)
class ContextValidationResult:
    decision: AgentDecision
    validity: str
    reasons: list[str]


def validate_decision_context(
    decision: AgentDecision,
    *,
    profile: dict[str, Any],
    market: dict[str, Any],
    derivatives: dict[str, Any],
    config: dict[str, Any],
) -> ContextValidationResult:
    validation_config = config.get("context_validation", {})
    if not validation_config.get("enabled", True):
        return ContextValidationResult(decision, "valid_schema", [])

    reasons: list[str] = []
    if decision.profile != profile.get("name"):
        reasons.append("Decision profile does not match current profile")
    if decision.asset != profile.get("symbol"):
        reasons.append("Decision asset does not match current symbol")
    if decision.horizon != profile.get("timeframe"):
        reasons.append("Decision horizon does not match current timeframe")

    if decision.decision in {DecisionType.LONG, DecisionType.SHORT}:
        current_price = float(market.get("last_close") or 0.0)
        if current_price <= 0 or decision.reference_entry_price is None:
            reasons.append("Missing current price or reference entry price")
        else:
            deviation_bps = (
                abs(decision.reference_entry_price - current_price) / current_price * 10_000
            )
            max_deviation = float(validation_config.get("max_entry_price_deviation_bps", 50))
            if deviation_bps > max_deviation:
                reasons.append(
                    "reference_entry_price deviation "
                    f"{deviation_bps:.2f} bps exceeds {max_deviation:.2f}"
                )

    unavailable = unavailable_derivative_features(derivatives)
    used_unavailable = sorted(set(decision.critical_data_used) & unavailable)
    if used_unavailable:
        reasons.append(
            "critical_data_used contains unavailable data: " + ", ".join(used_unavailable)
        )

    if decision.strategy == "derivatives_signal" and unavailable:
        reasons.append("derivatives_signal strategy requires unavailable derivatives data")

    if (
        reasons
        and validation_config.get("unavailable_data_policy", "fallback_no_trade")
        == "fallback_no_trade"
    ):
        return ContextValidationResult(
            no_trade_decision(
                profile=profile.get("name", decision.profile),
                asset=profile.get("symbol", decision.asset),
                horizon=profile.get("timeframe", decision.horizon),
                reason="Context validation failed: " + "; ".join(reasons),
            ),
            "context_fallback",
            reasons,
        )
    validity = "valid_schema" if not reasons else "context_warning"
    return ContextValidationResult(decision, validity, reasons)


def unavailable_derivative_features(derivatives: dict[str, Any]) -> set[str]:
    unavailable: set[str] = set()
    for key, value in derivatives.items():
        if not isinstance(value, dict):
            continue
        status = value.get("status")
        if status != "available":
            unavailable.add(key)
    return unavailable

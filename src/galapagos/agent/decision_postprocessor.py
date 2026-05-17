from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from galapagos.agent.decision_schema import AgentDecision, DecisionType, no_trade_decision


@dataclass(frozen=True)
class DecisionPostprocessResult:
    decision: AgentDecision
    warnings: list[str]
    action: str
    missing_required: list[str]
    stateful_override: bool = False
    original_decision: str | None = None


def postprocess_decision_for_risk(
    decision: AgentDecision,
    *,
    decision_context: Any,
    config: dict[str, Any],
) -> DecisionPostprocessResult:
    stateful = _stateful_position_guard(decision, decision_context)
    if stateful is not None:
        return stateful

    if decision.decision not in {DecisionType.LONG, DecisionType.SHORT}:
        return DecisionPostprocessResult(
            decision=decision,
            warnings=[],
            action="unchanged_non_entry",
            missing_required=[],
        )

    post_config = config.get("decision_postprocessing") or {}
    required = list(post_config.get("active_required_critical_data") or ["price", "volatility"])
    policy = str(post_config.get("missing_required_policy") or "fallback_no_trade")
    available = _available_critical_data(decision_context)
    used = _canonical_used(decision.critical_data_used)
    warnings = []
    missing_required = [item for item in required if item not in used]
    missing_but_available = [item for item in missing_required if available.get(item)]
    missing_unavailable = [item for item in missing_required if not available.get(item)]

    if missing_but_available:
        warnings.append(
            "critical_data_used_missing_but_context_available: "
            + ", ".join(missing_but_available)
        )
    if missing_unavailable:
        warnings.append(
            "critical_data_unavailable_for_active_decision: "
            + ", ".join(missing_unavailable)
        )

    if missing_required and policy == "fallback_no_trade":
        return DecisionPostprocessResult(
            decision=no_trade_decision(
                decision.profile,
                decision.asset,
                decision.horizon,
                "Active decision missing required critical_data_used: "
                + ", ".join(missing_required),
            ),
            warnings=warnings,
            action="fallback_no_trade",
            missing_required=missing_required,
        )

    optional = ["trend_short", "trend_long", "candidate_setup"]
    optional_missing = [item for item in optional if item not in used and available.get(item)]
    if optional_missing:
        warnings.append(
            "critical_data_used_optional_missing_but_context_available: "
            + ", ".join(optional_missing)
        )
    return DecisionPostprocessResult(
        decision=decision,
        warnings=warnings,
        action="unchanged_active",
        missing_required=missing_required,
    )


def _available_critical_data(decision_context: Any) -> dict[str, bool]:
    payload = _context_payload(decision_context)
    available = payload.get("available_critical_data") or {}
    return {str(key): bool(value) for key, value in available.items()}


def _stateful_position_guard(
    decision: AgentDecision,
    decision_context: Any,
) -> DecisionPostprocessResult | None:
    if decision.decision not in {DecisionType.LONG, DecisionType.SHORT}:
        return None
    payload = _context_payload(decision_context)
    portfolio = payload.get("portfolio") or {}
    if not portfolio.get("has_open_position"):
        return None
    position_side = str(portfolio.get("position_side") or "").upper()
    original = decision.decision.value
    if position_side == original:
        return DecisionPostprocessResult(
            decision=decision.model_copy(
                update={
                    "decision": DecisionType.HOLD,
                    "risk_fraction": 0.0,
                    "max_duration_minutes": 0,
                    "reasoning_summary": (
                        "Stateful safety override: position already open in the same "
                        "direction, HOLD instead of repeated entry."
                    ),
                }
            ),
            warnings=["stateful_safety_override: repeated_entry_same_direction"],
            action="stateful_override_hold",
            missing_required=[],
            stateful_override=True,
            original_decision=original,
        )
    summary = decision.reasoning_summary.lower()
    if any(term in summary for term in ["invalid", "invalidation"]):
        return DecisionPostprocessResult(
            decision=decision.model_copy(
                update={
                    "decision": DecisionType.CLOSE,
                    "risk_fraction": 0.0,
                    "max_duration_minutes": 0,
                    "reasoning_summary": (
                        "Stateful safety override: opposite active setup indicates possible "
                        "invalidation, CLOSE current paper position."
                    ),
                }
            ),
            warnings=["stateful_safety_override: opposite_entry_to_close"],
            action="stateful_override_close",
            missing_required=[],
            stateful_override=True,
            original_decision=original,
        )
    return DecisionPostprocessResult(
        decision=no_trade_decision(
            decision.profile,
            decision.asset,
            decision.horizon,
            "Stateful safety override: opposite active setup without explicit invalidation.",
        ),
        warnings=["stateful_safety_override: opposite_entry_to_no_trade"],
        action="stateful_override_no_trade",
        missing_required=[],
        stateful_override=True,
        original_decision=original,
    )


def _context_payload(decision_context: Any) -> dict[str, Any]:
    if hasattr(decision_context, "to_dict"):
        return decision_context.to_dict()
    if isinstance(decision_context, dict):
        return decision_context
    return {}


def _canonical_used(values: list[str]) -> set[str]:
    canonical = set()
    for value in values:
        text = str(value).strip().lower()
        if text in {"price", "current_price"} or text.startswith("current_price"):
            canonical.add("price")
        if text == "volatility" or "volatility" in text or "volatil" in text:
            canonical.add("volatility")
        if text == "trend_short" or text.startswith("trend_short"):
            canonical.add("trend_short")
        if text == "trend_long" or text.startswith("trend_long"):
            canonical.add("trend_long")
        if text == "market_regime" or text.startswith("market_regime"):
            canonical.add("market_regime")
        if text == "candidate_setup" or "candidate_setup" in text:
            canonical.add("candidate_setup")
        if text == "funding" or text.startswith("funding"):
            canonical.add("funding")
        if text == "open_interest" or text.startswith("open_interest"):
            canonical.add("open_interest")
    return canonical

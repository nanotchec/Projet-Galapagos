from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from galapagos.agent.decision_schema import AgentDecision, DecisionType, StrategyType


@dataclass(frozen=True)
class ExitPolicyResult:
    decision: AgentDecision
    exit_policy_override: str | None
    original_decision: str
    final_decision: str
    bars_in_position: int
    min_holding_bars: int
    action: str
    warnings: list[str]


def apply_exit_policy(
    decision: AgentDecision,
    *,
    portfolio: dict[str, Any],
    config: dict[str, Any] | None,
) -> ExitPolicyResult:
    policy = ((config or {}).get("holding_aware") or {})
    bars = int(portfolio.get("bars_in_position") or 0)
    min_bars = int(policy.get("min_holding_bars_before_agent_close") or 0)
    original = decision.decision.value
    warnings: list[str] = []
    has_open_position = bool(
        portfolio.get("has_open_position")
        or portfolio.get("current_position")
        or portfolio.get("open_positions")
    )

    if not policy.get("enabled"):
        return _unchanged(decision, original, bars, min_bars, warnings)

    if decision.decision != DecisionType.CLOSE or not has_open_position:
        return _unchanged(decision, original, bars, min_bars, warnings)

    if bars >= min_bars:
        return _unchanged(decision, original, bars, min_bars, warnings)

    configured = str(policy.get("agent_close_before_min_policy", "convert_to_hold"))
    if configured != "convert_to_hold":
        warnings.append(f"unsupported_agent_close_before_min_policy:{configured}")
    hold = AgentDecision(
        decision=DecisionType.HOLD,
        profile=decision.profile,
        asset=decision.asset,
        strategy=StrategyType.RISK_REDUCTION,
        confidence=min(decision.confidence, 0.5),
        reasoning_summary=(
            "Exit policy override: agent_close delayed before minimum holding bars."
        ),
        horizon=decision.horizon,
        reference_entry_price=None,
        stop_loss=None,
        take_profit=None,
        risk_fraction=0.0,
        max_duration_minutes=0,
        invalidation_conditions=[],
        critical_data_used=[],
        setup_quality=decision.setup_quality,
        setup_quality_score=decision.setup_quality_score,
        why_not_no_trade=decision.why_not_no_trade,
    )
    return ExitPolicyResult(
        decision=hold,
        exit_policy_override="agent_close_delayed",
        original_decision=original,
        final_decision=hold.decision.value,
        bars_in_position=bars,
        min_holding_bars=min_bars,
        action="convert_to_hold",
        warnings=warnings,
    )


def _unchanged(
    decision: AgentDecision,
    original: str,
    bars: int,
    min_bars: int,
    warnings: list[str],
) -> ExitPolicyResult:
    return ExitPolicyResult(
        decision=decision,
        exit_policy_override=None,
        original_decision=original,
        final_decision=decision.decision.value,
        bars_in_position=bars,
        min_holding_bars=min_bars,
        action="unchanged",
        warnings=warnings,
    )

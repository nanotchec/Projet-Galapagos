from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from galapagos.agent.decision_schema import AgentDecision, DecisionType, no_trade_decision


@dataclass(frozen=True)
class TradeConstraintResult:
    decision: AgentDecision
    constraint_override: str | None
    original_decision: str
    action: str
    warnings: list[str]


def apply_trade_constraints(
    decision: AgentDecision,
    config: dict[str, Any] | None,
) -> TradeConstraintResult:
    constraints = config or {}
    original = decision.decision.value
    warnings: list[str] = []

    if decision.decision == DecisionType.SHORT and constraints.get("allow_short") is False:
        policy = str(constraints.get("short_policy", "fallback_no_trade"))
        if policy != "fallback_no_trade":
            warnings.append(f"unsupported_short_policy:{policy}")
        return TradeConstraintResult(
            decision=_constraint_no_trade(decision, "SHORT disabled for this experiment."),
            constraint_override="short_disabled",
            original_decision=original,
            action="fallback_no_trade",
            warnings=warnings,
        )

    if decision.decision == DecisionType.LONG and constraints.get("allow_long") is False:
        return TradeConstraintResult(
            decision=_constraint_no_trade(decision, "LONG disabled for this experiment."),
            constraint_override="long_disabled",
            original_decision=original,
            action="fallback_no_trade",
            warnings=warnings,
        )

    if decision.decision == DecisionType.HOLD and constraints.get("allow_hold") is False:
        return TradeConstraintResult(
            decision=_constraint_no_trade(decision, "HOLD disabled for this experiment."),
            constraint_override="hold_disabled",
            original_decision=original,
            action="fallback_no_trade",
            warnings=warnings,
        )

    if decision.decision == DecisionType.CLOSE and constraints.get("allow_close") is False:
        return TradeConstraintResult(
            decision=_constraint_no_trade(decision, "CLOSE disabled for this experiment."),
            constraint_override="close_disabled",
            original_decision=original,
            action="fallback_no_trade",
            warnings=warnings,
        )

    return TradeConstraintResult(
        decision=decision,
        constraint_override=None,
        original_decision=original,
        action="unchanged",
        warnings=warnings,
    )


def _constraint_no_trade(decision: AgentDecision, reason: str) -> AgentDecision:
    return no_trade_decision(
        profile=decision.profile,
        asset=decision.asset,
        horizon=decision.horizon,
        reason=f"Trade constraint override: {reason}",
    )

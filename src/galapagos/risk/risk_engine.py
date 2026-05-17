from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from galapagos.agent.decision_schema import AgentDecision, DecisionType
from galapagos.risk.kill_switch import KillSwitch
from galapagos.risk.position_sizing import size_from_risk


@dataclass(frozen=True)
class RiskResult:
    approved: bool
    final_action: DecisionType
    reasons: list[str]
    adjusted_risk_fraction: float


class RiskEngine:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.kill_switch = KillSwitch()

    def evaluate(
        self,
        decision: AgentDecision,
        *,
        profile_config: dict[str, Any],
        daily_trade_count: int = 0,
        daily_loss_fraction: float = 0.0,
        weekly_loss_fraction: float = 0.0,
        data_available: bool = True,
        volatility_regime: str | None = None,
        open_positions: list[Any] | None = None,
        current_price: float | None = None,
        current_capital: float | None = None,
    ) -> RiskResult:
        reasons: list[str] = []
        open_positions = open_positions or []
        if not profile_config.get("paper_trading_only", False):
            reasons.append("Profile is not paper_trading_only")

        kill = self.kill_switch.evaluate(
            enabled=bool(self.config.get("kill_switch_enabled", True)),
            data_available=data_available,
            daily_loss_fraction=daily_loss_fraction,
            weekly_loss_fraction=weekly_loss_fraction,
            max_daily_loss=float(self.config.get("max_daily_loss", 0.02)),
            max_weekly_loss=float(self.config.get("max_weekly_loss", 0.05)),
            volatility_regime=volatility_regime,
        )
        reasons.extend(kill.reasons)

        max_trades = min(
            int(self.config.get("max_trades_per_day", 0) or 0),
            int(profile_config.get("max_trades_per_day", 0) or 0),
        )
        if max_trades and daily_trade_count >= max_trades:
            reasons.append("Max trades per day reached")

        if decision.decision in {DecisionType.LONG, DecisionType.SHORT}:
            self._validate_trade_decision(decision, reasons)
            self._validate_exposure(
                decision,
                reasons,
                open_positions=open_positions,
                current_price=current_price,
                current_capital=current_capital,
            )
        elif decision.decision in {DecisionType.CLOSE, DecisionType.HOLD, DecisionType.NO_TRADE}:
            pass
        else:
            reasons.append(f"Unsupported decision: {decision.decision}")

        max_risk = float(self.config.get("max_risk_per_trade", 0.0))
        adjusted = min(decision.risk_fraction, max_risk)
        if decision.risk_fraction > max_risk:
            reasons.append("risk_fraction exceeds max_risk_per_trade")

        approved = not reasons and not kill.active
        return RiskResult(
            approved=approved,
            final_action=decision.decision if approved else DecisionType.NO_TRADE,
            reasons=reasons,
            adjusted_risk_fraction=adjusted if approved else 0.0,
        )

    def _validate_trade_decision(self, decision: AgentDecision, reasons: list[str]) -> None:
        if self.config.get("stop_loss_required", True) and decision.stop_loss is None:
            reasons.append("LONG/SHORT requires stop_loss")
        if (
            self.config.get("take_profit_or_time_exit_required", True)
            and decision.take_profit is None
            and decision.max_duration_minutes <= 0
        ):
            reasons.append("LONG/SHORT requires take_profit or max_duration_minutes")
        if not self.config.get("leverage_allowed", False):
            pass
        required = set(self.config.get("required_critical_data", []))
        used = set(decision.critical_data_used)
        missing = sorted(required - used)
        if missing:
            reasons.append(f"Missing required critical data: {', '.join(missing)}")
        if decision.reference_entry_price is not None and decision.stop_loss is not None:
            if decision.decision == DecisionType.LONG:
                if decision.stop_loss >= decision.reference_entry_price:
                    reasons.append("LONG stop_loss must be below entry")
                if (
                    decision.take_profit is not None
                    and decision.take_profit <= decision.reference_entry_price
                ):
                    reasons.append("LONG take_profit must be above entry")
            if decision.decision == DecisionType.SHORT:
                if decision.stop_loss <= decision.reference_entry_price:
                    reasons.append("SHORT stop_loss must be above entry")
                if (
                    decision.take_profit is not None
                    and decision.take_profit >= decision.reference_entry_price
                ):
                    reasons.append("SHORT take_profit must be below entry")

    def _validate_exposure(
        self,
        decision: AgentDecision,
        reasons: list[str],
        *,
        open_positions: list[Any],
        current_price: float | None,
        current_capital: float | None,
    ) -> None:
        max_global = int(self.config.get("max_open_positions_global", 0) or 0)
        max_profile = int(self.config.get("max_open_positions_per_profile", 0) or 0)
        allow_same_asset = bool(self.config.get("allow_multiple_positions_same_asset", False))

        if max_global and len(open_positions) >= max_global:
            reasons.append("Max open positions global reached")

        same_profile = [
            position
            for position in open_positions
            if self._position_value(position, "profile") == decision.profile
        ]
        if max_profile and len(same_profile) >= max_profile:
            reasons.append("Max open positions per profile reached")

        same_asset_profile = [
            position
            for position in open_positions
            if self._position_value(position, "profile") == decision.profile
            and self._position_value(position, "asset") == decision.asset
        ]
        if same_asset_profile and not allow_same_asset:
            reasons.append("Open position already exists for this profile and asset")

        max_exposure = float(self.config.get("max_total_exposure_fraction", 0.0) or 0.0)
        if not max_exposure or current_capital is None or current_capital <= 0:
            return
        existing_exposure = sum(
            abs(float(self._position_value(position, "entry_price") or 0.0))
            * abs(float(self._position_value(position, "size") or 0.0))
            for position in open_positions
        )
        new_exposure = 0.0
        if (
            decision.reference_entry_price is not None
            and decision.stop_loss is not None
            and decision.risk_fraction > 0
        ):
            risk_fraction = min(
                decision.risk_fraction,
                float(self.config.get("max_risk_per_trade", decision.risk_fraction)),
            )
            size = size_from_risk(
                current_capital,
                risk_fraction,
                decision.reference_entry_price,
                decision.stop_loss,
            )
            new_exposure = abs(decision.reference_entry_price * size)
        price = current_price or decision.reference_entry_price or 0.0
        exposure_fraction = (existing_exposure + new_exposure) / current_capital
        if price > 0 and exposure_fraction > max_exposure:
            reasons.append("Max total exposure fraction exceeded")

    def _position_value(self, position: Any, field: str) -> Any:
        if isinstance(position, dict):
            return position.get(field)
        return getattr(position, field, None)

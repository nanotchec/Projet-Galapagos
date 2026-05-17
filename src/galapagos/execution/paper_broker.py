from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from galapagos.agent.decision_schema import AgentDecision, DecisionType
from galapagos.execution.fee_model import FeeModel
from galapagos.execution.position_manager import Position
from galapagos.execution.slippage_model import SlippageModel
from galapagos.risk.position_sizing import size_from_risk


class RealTradingDisabledError(RuntimeError):
    pass


class PaperBroker:
    def __init__(
        self,
        *,
        initial_capital: float,
        fee_model: FeeModel | None = None,
        slippage_model: SlippageModel | None = None,
        cash: float | None = None,
        positions: dict[str, Position] | None = None,
    ) -> None:
        self.initial_capital = initial_capital
        self.cash = initial_capital if cash is None else cash
        self.fee_model = fee_model or FeeModel()
        self.slippage_model = slippage_model or SlippageModel()
        self.positions: dict[str, Position] = positions or {}
        self.closed_trades: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []

    def create_order(self, *args, **kwargs):
        raise RealTradingDisabledError("Real order execution is disabled in Galapagos V1.")

    def execute_decision(
        self,
        decision: AgentDecision,
        *,
        approved_risk_fraction: float,
        capital: float | None = None,
        current_price: float | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        timestamp = timestamp or datetime.now(UTC).isoformat()
        if decision.decision in {DecisionType.NO_TRADE, DecisionType.HOLD}:
            event = {
                "action": decision.decision.value,
                "timestamp": timestamp,
                "status": "NO_EXECUTION",
            }
            self.events.append(event)
            return event
        if decision.decision == DecisionType.CLOSE:
            return self.close_matching_position(
                profile=decision.profile,
                asset=decision.asset,
                exit_price=current_price or decision.reference_entry_price,
                reason="agent_close",
                timestamp=timestamp,
            )
        if decision.decision not in {DecisionType.LONG, DecisionType.SHORT}:
            return {"action": "REJECTED", "timestamp": timestamp, "status": "UNSUPPORTED_DECISION"}

        assert decision.reference_entry_price is not None
        assert decision.stop_loss is not None
        adjusted_entry, slippage = self.slippage_model.apply(
            decision.reference_entry_price, decision.decision.value, "entry"
        )
        size = size_from_risk(
            capital or self.cash,
            approved_risk_fraction,
            adjusted_entry,
            decision.stop_loss,
        )
        notional = adjusted_entry * size
        fee = self.fee_model.calculate(notional)
        self.cash -= fee
        position = Position(
            id=str(uuid4()),
            profile=decision.profile,
            asset=decision.asset,
            side=decision.decision.value,
            entry_price=adjusted_entry,
            size=size,
            stop_loss=decision.stop_loss,
            take_profit=decision.take_profit,
            max_duration_minutes=decision.max_duration_minutes,
            strategy=decision.strategy.value,
            entry_timestamp=timestamp,
            entry_fee=fee,
            entry_slippage=slippage,
        )
        self.positions[position.id] = position
        event = {"action": "OPEN_POSITION", "timestamp": timestamp, "position": asdict(position)}
        self.events.append(event)
        return event

    def close_position(
        self,
        position_id: str,
        exit_price: float,
        reason: str,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        if exit_price is None:
            raise ValueError("exit_price is required to close a paper position")
        position = self.positions.pop(position_id)
        timestamp = timestamp or datetime.now(UTC).isoformat()
        adjusted_exit, slippage = self.slippage_model.apply(exit_price, position.side, "exit")
        pnl = self._pnl(position, adjusted_exit)
        exit_fee = self.fee_model.calculate(adjusted_exit * position.size)
        self.cash += pnl - exit_fee
        trade = {
            **asdict(position),
            "exit_timestamp": timestamp,
            "exit_price": adjusted_exit,
            "exit_fee": exit_fee,
            "exit_slippage": slippage,
            "fees": position.entry_fee + exit_fee,
            "slippage": position.entry_slippage + slippage,
            "pnl": pnl - position.entry_fee - exit_fee,
            "pnl_percent": (
                (pnl - position.entry_fee - exit_fee) / (position.entry_price * position.size)
                if position.entry_price * position.size
                else 0.0
            ),
            "status": "CLOSED",
            "close_reason": reason,
        }
        self.closed_trades.append(trade)
        return trade

    def close_matching_position(
        self,
        *,
        profile: str,
        asset: str,
        exit_price: float | None,
        reason: str,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        for position_id, position in list(self.positions.items()):
            if position.profile == profile and position.asset == asset:
                trade = self.close_position(position_id, float(exit_price), reason, timestamp)
                event = {"action": "CLOSE_POSITION", "status": "CLOSED", "trade": trade}
                self.events.append(event)
                return event
        event = {"action": "CLOSE_IGNORED", "status": "NO_OPEN_POSITION"}
        self.events.append(event)
        return event

    def evaluate_position_exits(
        self,
        *,
        candle: dict[str, float],
        timestamp: str | None = None,
        kill_switch_active: bool = False,
    ) -> list[dict[str, Any]]:
        timestamp = timestamp or datetime.now(UTC).isoformat()
        closed_events: list[dict[str, Any]] = []
        for position_id, position in list(self.positions.items()):
            exit_price, reason = self._exit_signal(position, candle, timestamp, kill_switch_active)
            if exit_price is None or reason is None:
                continue
            trade = self.close_position(position_id, exit_price, reason, timestamp)
            event = {"action": "AUTO_CLOSE_POSITION", "status": "CLOSED", "trade": trade}
            closed_events.append(event)
            self.events.append(event)
        return closed_events

    def _exit_signal(
        self,
        position: Position,
        candle: dict[str, float],
        timestamp: str,
        kill_switch_active: bool,
    ) -> tuple[float | None, str | None]:
        high = float(candle["high"])
        low = float(candle["low"])
        close = float(candle["close"])
        if kill_switch_active:
            return close, "kill_switch"

        # Conservative intrabar rule: if stop and take profit are both touched,
        # stop_loss wins because OHLCV does not expose event ordering.
        if position.side == "LONG":
            if low <= position.stop_loss:
                return position.stop_loss, "stop_loss"
            if position.take_profit is not None and high >= position.take_profit:
                return position.take_profit, "take_profit"
        else:
            if high >= position.stop_loss:
                return position.stop_loss, "stop_loss"
            if position.take_profit is not None and low <= position.take_profit:
                return position.take_profit, "take_profit"

        entry_time = datetime.fromisoformat(position.entry_timestamp)
        current_time = datetime.fromisoformat(timestamp)
        if position.max_duration_minutes > 0 and current_time - entry_time >= timedelta(
            minutes=position.max_duration_minutes
        ):
            return close, "max_duration"
        return None, None

    def mark_to_market(self, price: float) -> float:
        unrealized = sum(self._pnl(position, price) for position in self.positions.values())
        return self.cash + unrealized

    def _pnl(self, position: Position, price: float) -> float:
        if position.side == "LONG":
            return (price - position.entry_price) * position.size
        return (position.entry_price - price) * position.size

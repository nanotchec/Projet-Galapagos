from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

from galapagos.agent.decision_schema import AgentDecision, DecisionType, StrategyType
from galapagos.agent.trade_constraints import apply_trade_constraints
from galapagos.execution.paper_broker import PaperBroker

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_codex_setup_review.py"
sys.path.insert(0, str(_SCRIPT_PATH.parent))
_SPEC = importlib.util.spec_from_file_location("run_codex_setup_review", _SCRIPT_PATH)
assert _SPEC and _SPEC.loader
_SCRIPT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_SCRIPT)
_build_report = _SCRIPT._build_report
_force_close_open_positions_at_window_end = _SCRIPT._force_close_open_positions_at_window_end


def test_short_becomes_no_trade_when_short_disabled() -> None:
    result = apply_trade_constraints(
        _active_decision(DecisionType.SHORT),
        {"allow_short": False, "short_policy": "fallback_no_trade"},
    )

    assert result.decision.decision == DecisionType.NO_TRADE
    assert result.original_decision == "SHORT"
    assert result.constraint_override == "short_disabled"
    assert "SHORT disabled" in result.decision.reasoning_summary


def test_long_is_allowed_when_long_enabled() -> None:
    decision = _active_decision(DecisionType.LONG)
    result = apply_trade_constraints(
        decision,
        {"allow_long": True, "allow_short": False},
    )

    assert result.decision is decision
    assert result.constraint_override is None
    assert result.action == "unchanged"


def test_hold_and_close_are_allowed_when_configured() -> None:
    for decision_type in (DecisionType.HOLD, DecisionType.CLOSE):
        decision = AgentDecision(
            decision=decision_type,
            profile="galapagos_4h",
            asset="BTC/USD",
            strategy=StrategyType.CLOSE_POSITION
            if decision_type == DecisionType.CLOSE
            else StrategyType.RISK_REDUCTION,
            confidence=0.5,
            reasoning_summary="Manage existing position.",
            horizon="4h",
            reference_entry_price=None,
            stop_loss=None,
            take_profit=None,
            risk_fraction=0.0,
            max_duration_minutes=0,
            invalidation_conditions=[],
            critical_data_used=[],
        )
        result = apply_trade_constraints(
            decision,
            {"allow_hold": True, "allow_close": True, "allow_short": False},
        )

        assert result.decision.decision == decision_type
        assert result.constraint_override is None


def test_report_contains_constraint_overrides() -> None:
    report = _build_report(
        candidates=[],
        reviews=[
            {
                "decision": "NO_TRADE",
                "raw_decision": "SHORT",
                "decision_after_constraints": "NO_TRADE",
                "baseline_decision": "SHORT",
                "parser_validity": "valid_schema",
                "parser_repair_applied": False,
                "raw_json_valid": True,
                "enum_violations": [],
                "risk_approved": True,
                "stateful_safety_override": None,
                "constraint_override": "short_disabled",
                "postprocessing_action": "unchanged",
                "decision_before_postprocessing": "SHORT",
                "portfolio_before_decision": {"has_open_position": False},
                "execution_event": {"action": "NO_EXECUTION"},
                "provider_duration_seconds": 0.1,
                "raw_response": "{}",
                "candidate": {},
                "risk_reasons": [],
                "postprocessing_missing_required": [],
                "postprocessing_warnings": [],
            }
        ],
        trades=[],
        data=[],
        broker=_BrokerStub(),
        closed_trades_ledger=[],
        position_events=[],
    )

    assert report["constraint_overrides"] == 1
    assert report["short_overrides"] == 1
    assert report["raw_decision_distribution"] == {"SHORT": 1}


def test_report_final_equity_is_realized_plus_unrealized() -> None:
    report = _build_report(
        candidates=[],
        reviews=[],
        trades=[{"pnl": 10.0, "fees": 1.0, "slippage": 2.0}],
        data=_sample_candles([100.0]),
        broker=_BrokerStub(cash=10_000.0, mark_to_market_value=10_005.0),
        closed_trades_ledger=[{"net_pnl": 10.0}],
        position_events=[],
    )

    assert report["realized_pnl"] == 10.0
    assert report["unrealized_pnl"] == 5.0
    assert report["final_equity_pnl"] == 15.0
    assert report["final_equity_pnl_per_window"] == 15.0


def test_force_close_at_end_closes_open_position_and_updates_ledger() -> None:
    broker = PaperBroker(initial_capital=10_000.0)
    decision = _active_decision(DecisionType.LONG)
    event = broker.execute_decision(
        decision,
        approved_risk_fraction=0.01,
        current_price=100.0,
        timestamp="2026-01-01T00:00:00",
    )
    position = event["position"]
    metadata = {
        position["id"]: {
            "candidate_id_entry": "candidate-1",
            "entry_decision": decision.model_dump(mode="json"),
            "entry_context_hash": "hash",
            "entry_context_index": 0,
            "candidate_setup": {},
            "setup_quality": "acceptable",
            "setup_quality_score": 0.6,
            "confidence": 0.7,
            "risk_fraction": 0.01,
            "risk_reward_initial": 2.0,
            "critical_data_used": ["price", "volatility"],
        }
    }
    trades: list[dict] = []
    recent_trades: list[dict] = []
    ledger: list[dict] = []
    events: list[dict] = []

    _force_close_open_positions_at_window_end(
        broker=broker,
        data=_sample_candles([100.0, 102.0]),
        trades=trades,
        recent_trades=recent_trades,
        closed_trades_ledger=ledger,
        position_events=events,
        open_position_metadata=metadata,
    )

    assert not broker.positions
    assert trades[0]["close_reason"] == "evaluation_window_end"
    assert ledger[0]["exit_reason"] == "evaluation_window_end"
    assert events[0]["reason"] == "evaluation_window_end"


def _active_decision(decision: DecisionType) -> AgentDecision:
    return AgentDecision(
        decision=decision,
        profile="galapagos_4h",
        asset="BTC/USD",
        strategy=StrategyType.MOMENTUM,
        confidence=0.7,
        reasoning_summary="Active setup.",
        horizon="4h",
        reference_entry_price=100.0,
        stop_loss=95.0 if decision == DecisionType.LONG else 105.0,
        take_profit=110.0 if decision == DecisionType.LONG else 90.0,
        risk_fraction=0.01,
        max_duration_minutes=240,
        invalidation_conditions=["setup invalidated"],
        critical_data_used=["price", "volatility"],
        setup_quality="acceptable",
        setup_quality_score=0.55,
    )


def _sample_candles(closes: list[float]) -> pd.DataFrame:
    start = pd.Timestamp("2026-01-01T00:00:00")
    rows = []
    for index, close in enumerate(closes):
        rows.append(
            {
                "timestamp": start + pd.Timedelta(hours=4 * index),
                "candle_close_timestamp": start + pd.Timedelta(hours=4 * (index + 1)),
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 100,
            }
        )
    return pd.DataFrame(rows)


class _BrokerStub:
    positions = {}

    def __init__(self, *, cash: float = 10_000.0, mark_to_market_value: float | None = None):
        self.cash = cash
        self._mark_to_market_value = cash if mark_to_market_value is None else mark_to_market_value

    def mark_to_market(self, _price: float) -> float:
        return self._mark_to_market_value

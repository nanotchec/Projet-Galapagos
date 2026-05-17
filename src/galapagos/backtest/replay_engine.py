from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from galapagos.agent.decision_context import build_decision_context
from galapagos.agent.decision_parser import parse_decision_response_with_metadata
from galapagos.agent.decision_prompt import build_llm_decision_prompt
from galapagos.agent.decision_validator import validate_decision_context
from galapagos.agent.llm_providers import CodexCLIProvider, LLMProviderResult
from galapagos.agent.offline_llm_policy import (
    generate_offline_llm_response,
    is_offline_llm_policy,
)
from galapagos.analysis.backtest_metrics import calculate_backtest_metrics
from galapagos.backtest.anti_leakage import (
    assert_replay_window,
    assert_strictly_increasing_timestamps,
    check_timeframe_gaps,
)
from galapagos.backtest.historical_data import load_historical_ohlcv
from galapagos.backtest.mock_policy import decide_with_policy
from galapagos.backtest.timeframe_utils import candle_close_time
from galapagos.data.binance_futures_collector import unavailable_derivatives
from galapagos.data.data_quality import assess_ohlcv_quality
from galapagos.data.market_snapshot import MarketSnapshot
from galapagos.execution.paper_broker import PaperBroker
from galapagos.indicators.market_regime import detect_market_regime
from galapagos.indicators.technical_indicators import compute_technical_indicators
from galapagos.indicators.volatility import realized_volatility
from galapagos.risk.risk_engine import RiskEngine
from galapagos.strategies.scenario_builder import build_scenarios
from galapagos.utils.config_loader import load_yaml
from galapagos.utils.time_utils import utc_now_iso


class ReplayEngine:
    def __init__(
        self,
        *,
        profile: dict[str, Any],
        data_path: str | Path,
        risk_config: dict[str, Any],
        initial_capital: float,
        policy: str = "simple_momentum",
        warmup_bars: int = 50,
        force_close_at_end: bool = False,
        llm_provider: CodexCLIProvider | None = None,
        max_llm_calls: int | None = None,
        prompt_mode: str = "conservative",
    ) -> None:
        self.profile = profile
        self.data_path = Path(data_path)
        self.risk_config = risk_config
        self.initial_capital = initial_capital
        self.policy = policy
        self.warmup_bars = warmup_bars
        self.force_close_at_end = force_close_at_end
        self.llm_provider = llm_provider
        self.max_llm_calls = max_llm_calls
        self.prompt_mode = prompt_mode

    def run(self) -> dict[str, Any]:
        data = load_historical_ohlcv(self.data_path).reset_index(drop=True)
        data = self._with_candle_times(data)
        assert_strictly_increasing_timestamps(data, timestamp_column="candle_open_timestamp")
        gap_status = check_timeframe_gaps(
            data,
            timeframe=self.profile["timeframe"],
            timestamp_column="candle_open_timestamp",
        )
        broker = PaperBroker(initial_capital=self.initial_capital)
        run_id = str(uuid4())
        decisions: list[dict[str, Any]] = []
        trades: list[dict[str, Any]] = []
        equity_curve: list[dict[str, Any]] = []
        llm_call_count = 0
        for replay_index in range(len(data)):
            window = data.iloc[: replay_index + 1].copy()
            if len(window) < self.warmup_bars:
                continue
            current = data.iloc[replay_index]
            decision_timestamp = pd.Timestamp(current["candle_close_timestamp"])
            window_check = assert_replay_window(
                window,
                replay_index=replay_index,
                decision_timestamp=decision_timestamp,
                timeframe=self.profile["timeframe"],
                warmup_bars=self.warmup_bars,
            )
            candle = {
                "high": float(current["high"]),
                "low": float(current["low"]),
                "close": float(current["close"]),
            }
            for event in broker.evaluate_position_exits(
                candle=candle,
                timestamp=decision_timestamp.isoformat(),
            ):
                trades.append(event["trade"])
            snapshot = self._snapshot(window, decision_timestamp)
            context = {
                "profile": self.profile,
                "market": snapshot.market,
                "indicators": snapshot.indicators,
                "derivatives": snapshot.derivatives,
                "scenarios": snapshot.scenarios,
                "data_quality": snapshot.data_quality,
                "portfolio": self._policy_portfolio_context(
                    broker=broker,
                    current_price=snapshot.market["last_close"],
                    timestamp=decision_timestamp,
                    replay_index=replay_index,
                ),
                "ohlcv_window": window.tail(_context_window_bars(self.policy)).to_dict("records"),
                "recent_decisions": _recent_decisions_for_context(self.policy, decisions),
                "recent_trades": trades[-20:],
            }
            llm_metadata: dict[str, Any] = {}
            if is_offline_llm_policy(self.policy) or self.policy == "codex_cli":
                decision_context = build_decision_context(
                    profile=self.profile,
                    market=snapshot.market,
                    indicators=snapshot.indicators,
                    derivatives=snapshot.derivatives,
                    scenarios=snapshot.scenarios,
                    portfolio=context["portfolio"],
                    risk_config=self.risk_config,
                    decision_timestamp=decision_timestamp.isoformat(),
                    data_mode="historical_replay",
                    run_id=run_id,
                    ohlcv_window=context["ohlcv_window"],
                    recent_decisions=context["recent_decisions"],
                    recent_trades=trades[-20:],
                )
                prompt = build_llm_decision_prompt(decision_context, prompt_mode=self.prompt_mode)
                if self.policy == "codex_cli":
                    if self.llm_provider is None:
                        provider_result = LLMProviderResult(
                            provider_name="codex_cli",
                            model=None,
                            reasoning_effort=None,
                            raw_response="",
                            error="Codex CLI provider is not configured.",
                            available=False,
                        )
                    elif self.max_llm_calls is not None and llm_call_count >= self.max_llm_calls:
                        provider_result = LLMProviderResult(
                            provider_name="codex_cli",
                            model=self.llm_provider.config.model,
                            reasoning_effort=self.llm_provider.config.reasoning_effort,
                            raw_response="",
                            error="max_llm_calls reached; fallback NO_TRADE.",
                            available=True,
                        )
                    else:
                        provider_result = self.llm_provider.generate(prompt)
                        llm_call_count += 1
                    raw_response = provider_result.raw_response or _fallback_no_trade_raw(
                        self.profile,
                        reason=provider_result.error or "Codex CLI empty response.",
                    )
                    provider_metadata = {
                        "provider_name": provider_result.provider_name,
                        "provider_model": provider_result.model,
                        "provider_reasoning_effort": provider_result.reasoning_effort,
                        "provider_exit_code": provider_result.exit_code,
                        "provider_duration_seconds": provider_result.duration_seconds,
                        "provider_error": provider_result.error,
                        "provider_available": provider_result.available,
                        "prompt_mode": self.prompt_mode,
                        "stdout_preview": provider_result.stdout_preview,
                        "stderr_preview": provider_result.stderr_preview,
                    }
                else:
                    offline_response = generate_offline_llm_response(self.policy, decision_context)
                    raw_response = offline_response.raw_response
                    provider_metadata = {
                        "offline_policy_name": self.policy,
                        "provider_name": "offline_llm",
                    }
                parse_result = parse_decision_response_with_metadata(
                    raw_response,
                    self.profile["name"],
                    self.profile["symbol"],
                    self.profile["timeframe"],
                )
                validation = validate_decision_context(
                    parse_result.decision,
                    profile=self.profile,
                    market=snapshot.market,
                    derivatives=snapshot.derivatives,
                    config=load_yaml("configs/llm.yaml"),
                )
                decision = validation.decision
                llm_metadata = {
                    "context_hash": decision_context.to_dict()["context_hash"],
                    "prompt_hash": _hash_text(prompt),
                    "raw_response": raw_response,
                    "decision_validity": validation.validity
                    if validation.validity != "valid_schema"
                    else parse_result.validity,
                    "parser_validity": parse_result.validity,
                    "context_validation_reasons": validation.reasons,
                    **provider_metadata,
                }
            else:
                decision = decide_with_policy(self.policy, context, seed=replay_index)
            risk = RiskEngine(self.risk_config).evaluate(
                decision,
                profile_config=self.profile,
                data_available=True,
                volatility_regime=snapshot.indicators.get("market_regime", {}).get(
                    "volatility_regime"
                ),
                open_positions=list(broker.positions.values()),
                current_price=snapshot.market["last_close"],
                current_capital=broker.cash,
            )
            if risk.approved:
                event = broker.execute_decision(
                    decision,
                    approved_risk_fraction=risk.adjusted_risk_fraction,
                    current_price=snapshot.market["last_close"],
                    timestamp=decision_timestamp.isoformat(),
                )
                if event.get("trade"):
                    trades.append(event["trade"])
            decisions.append(
                {
                    "timestamp": decision_timestamp.isoformat(),
                    "candle_open_timestamp": pd.Timestamp(
                        current["candle_open_timestamp"]
                    ).isoformat(),
                    "candle_close_timestamp": pd.Timestamp(
                        current["candle_close_timestamp"]
                    ).isoformat(),
                    "available_at_utc": pd.Timestamp(current["available_at_utc"]).isoformat(),
                    "decision_timestamp": decision_timestamp.isoformat(),
                    "decision": decision.decision.value,
                    "profile": decision.profile,
                    "asset": decision.asset,
                    "strategy": decision.strategy.value,
                    "risk_approved": risk.approved,
                    "risk_reasons": risk.reasons,
                    "replay_index": replay_index,
                    "anti_leakage": asdict(window_check),
                    **llm_metadata,
                }
            )
            equity_curve.append(
                {
                    "timestamp": decision_timestamp.isoformat(),
                    "candle_open_timestamp": pd.Timestamp(
                        current["candle_open_timestamp"]
                    ).isoformat(),
                    "candle_close_timestamp": pd.Timestamp(
                        current["candle_close_timestamp"]
                    ).isoformat(),
                    "decision_timestamp": decision_timestamp.isoformat(),
                    "equity": broker.mark_to_market(snapshot.market["last_close"]),
                    "open_position_count": len(broker.positions),
                }
            )
        if self.force_close_at_end and len(data):
            last = data.iloc[-1]
            last_close = float(last["close"])
            for position_id in list(broker.positions):
                trade = broker.close_position(
                    position_id,
                    last_close,
                    "backtest_end",
                    timestamp=pd.Timestamp(last["candle_close_timestamp"]).isoformat(),
                )
                trades.append(trade)
            if equity_curve:
                equity_curve[-1]["equity"] = broker.mark_to_market(last_close)
                equity_curve[-1]["open_position_count"] = len(broker.positions)
        latest_price = float(data["close"].iloc[-1]) if len(data) else None
        open_positions = [asdict(position) for position in broker.positions.values()]
        backtest_days = _period_days(data)
        final_equity = (
            broker.mark_to_market(latest_price) if latest_price is not None else broker.cash
        )
        return {
            "run_id": run_id,
            "profile": self.profile["name"],
            "data_path": str(self.data_path),
            "policy": self.policy,
            "period": {
                "start": str(data["candle_open_timestamp"].iloc[0]) if len(data) else None,
                "end": str(data["candle_close_timestamp"].iloc[-1]) if len(data) else None,
                "first_candle_open": (
                    str(data["candle_open_timestamp"].iloc[0]) if len(data) else None
                ),
                "last_candle_close": (
                    str(data["candle_close_timestamp"].iloc[-1]) if len(data) else None
                ),
            },
            "time_convention": {
                "source_timestamp": "candle_open_timestamp",
                "decision_timestamp": "candle_close_timestamp",
                "available_at_utc": "candle_close_timestamp",
            },
            "force_close_at_end": self.force_close_at_end,
            "final_equity": final_equity,
            "llm_call_count": llm_call_count,
            "prompt_mode": self.prompt_mode if self.policy == "codex_cli" else None,
            "anti_leakage": {
                "timestamps_strictly_increasing": True,
                "timeframe_gaps": gap_status,
                "decision_at_candle_close": True,
                "warmup_bars": self.warmup_bars,
            },
            "decisions": decisions,
            "trades": trades,
            "open_positions": open_positions,
            "equity_curve": equity_curve,
            "metrics": calculate_backtest_metrics(
                trades=trades,
                decisions=decisions,
                equity_curve=equity_curve,
                total_bars=max(0, len(data) - self.warmup_bars),
                open_positions=open_positions,
                current_price=latest_price,
                backtest_days=backtest_days,
            ),
        }

    def _snapshot(self, window: pd.DataFrame, timestamp: pd.Timestamp) -> MarketSnapshot:
        indicators = compute_technical_indicators(window)
        vol = realized_volatility(window)
        indicators["realized_volatility"] = vol
        regime = detect_market_regime(indicators, vol)
        indicators["market_regime"] = regime
        derivatives = unavailable_derivatives("BTC/USDT:USDT")
        scenarios = build_scenarios(indicators, regime, derivatives)
        quality = assess_ohlcv_quality(window)
        quality["data_mode"] = "historical_replay"
        market = {
            "last_open": float(window["open"].iloc[-1]),
            "last_high": float(window["high"].iloc[-1]),
            "last_low": float(window["low"].iloc[-1]),
            "last_close": float(window["close"].iloc[-1]),
            "last_volume": float(window["volume"].iloc[-1]),
            "source": "historical_cache",
            "candle_open_timestamp": pd.Timestamp(
                window["candle_open_timestamp"].iloc[-1]
            ).isoformat(),
            "candle_close_timestamp": pd.Timestamp(
                window["candle_close_timestamp"].iloc[-1]
            ).isoformat(),
            "available_at_utc": pd.Timestamp(window["available_at_utc"].iloc[-1]).isoformat(),
        }
        return MarketSnapshot(
            profile=self.profile["name"],
            asset=self.profile["symbol"],
            timeframe=self.profile["timeframe"],
            market=market,
            indicators=indicators,
            derivatives=derivatives,
            scenarios=scenarios,
            data_quality=quality,
            timestamp_utc=timestamp.isoformat(),
            collected_at_utc=utc_now_iso(),
            data_mode="historical_replay",
        )

    def _with_candle_times(self, data: pd.DataFrame) -> pd.DataFrame:
        enriched = data.copy()
        enriched["candle_open_timestamp"] = pd.to_datetime(enriched["timestamp"])
        enriched["candle_close_timestamp"] = enriched["candle_open_timestamp"].apply(
            lambda timestamp: candle_close_time(timestamp, self.profile["timeframe"])
        )
        enriched["available_at_utc"] = enriched["candle_close_timestamp"]
        return enriched

    def _policy_portfolio_context(
        self,
        *,
        broker: PaperBroker,
        current_price: float,
        timestamp: pd.Timestamp,
        replay_index: int,
    ) -> dict[str, Any]:
        positions = [
            asdict(position)
            for position in broker.positions.values()
            if position.profile == self.profile["name"] and position.asset == self.profile["symbol"]
        ]
        current = positions[0] if positions else None
        if current is None:
            return {
                "open_positions": [],
                "current_position": None,
                "current_price": current_price,
                "timestamp": timestamp.isoformat(),
                "replay_index": replay_index,
                "bars_in_position": 0,
                "unrealized_pnl": 0.0,
            }
        entry_ts = pd.Timestamp(current["entry_timestamp"])
        interval_minutes = int(self.profile.get("check_interval_minutes", 30) or 30)
        bars_in_position = int(
            max(0.0, (timestamp - entry_ts).total_seconds() / max(1, interval_minutes * 60))
        )
        if current["side"] == "LONG":
            unrealized = (current_price - current["entry_price"]) * current["size"]
        else:
            unrealized = (current["entry_price"] - current_price) * current["size"]
        return {
            "open_positions": positions,
            "current_position": current,
            "current_price": current_price,
            "timestamp": timestamp.isoformat(),
            "replay_index": replay_index,
            "bars_in_position": bars_in_position,
            "unrealized_pnl": unrealized,
        }


def _period_days(data: pd.DataFrame) -> float:
    if data.empty:
        return 0.0
    start = data["candle_open_timestamp"].iloc[0]
    end = data["candle_close_timestamp"].iloc[-1]
    if isinstance(start, str):
        start = datetime.fromisoformat(start)
    if isinstance(end, str):
        end = datetime.fromisoformat(end)
    return max(0.0, (pd.Timestamp(end) - pd.Timestamp(start)).total_seconds() / 86_400)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _context_window_bars(policy: str) -> int:
    return 40 if policy == "codex_cli" else 120


def _recent_decisions_for_context(
    policy: str,
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if policy != "codex_cli":
        return decisions[-20:]
    return [
        {
            "timestamp": decision.get("timestamp"),
            "decision": decision.get("decision"),
            "risk_approved": decision.get("risk_approved"),
            "risk_reasons": decision.get("risk_reasons", []),
        }
        for decision in decisions[-5:]
    ]


def _fallback_no_trade_raw(profile: dict[str, Any], *, reason: str) -> str:
    return json.dumps(
        {
            "decision": "NO_TRADE",
            "profile": profile["name"],
            "asset": profile["symbol"],
            "strategy": "no_trade",
            "confidence": 0.0,
            "reasoning_summary": reason,
            "horizon": profile["timeframe"],
            "reference_entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "risk_fraction": 0.0,
            "max_duration_minutes": 0,
            "invalidation_conditions": [],
            "critical_data_used": [],
        }
    )

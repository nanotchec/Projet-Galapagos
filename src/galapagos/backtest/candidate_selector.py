from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.backtest.historical_data import load_historical_ohlcv
from galapagos.backtest.mock_policy import decide_with_policy
from galapagos.backtest.timeframe_utils import candle_close_time
from galapagos.data.binance_futures_collector import unavailable_derivatives
from galapagos.data.data_quality import assess_ohlcv_quality
from galapagos.indicators.market_regime import detect_market_regime
from galapagos.indicators.technical_indicators import compute_technical_indicators
from galapagos.indicators.volatility import realized_volatility
from galapagos.strategies.scenario_builder import build_scenarios


@dataclass(frozen=True)
class CandidateSetup:
    candidate_id: str
    profile: str
    asset: str
    timeframe: str
    decision_timestamp: str
    baseline_policy: str
    baseline_decision: str
    baseline_strategy: str
    baseline_confidence_hint: float
    baseline_reason_summary: str
    current_price: float
    suggested_stop_loss: float | None
    suggested_take_profit: float | None
    recent_market_summary: dict[str, Any]
    context_index: int
    data_hash: str


def select_candidate_setups(
    *,
    profile: dict[str, Any],
    data_path: str | Path,
    source_policies: list[str],
    max_candidates: int = 20,
    warmup_bars: int = 50,
    min_spacing_bars: int = 3,
) -> list[CandidateSetup]:
    if profile.get("timeframe") != "4h":
        raise ValueError("Candidate setup review is limited to 4h in V1.8C.3.")
    data = _with_candle_times(load_historical_ohlcv(data_path).reset_index(drop=True), profile)
    return select_candidate_setups_from_data(
        profile=profile,
        data=data,
        source_policies=source_policies,
        max_candidates=max_candidates,
        warmup_bars=warmup_bars,
        min_spacing_bars=min_spacing_bars,
        data_hash=_data_hash(data),
        index_offset=0,
    )


def select_candidate_setups_from_data(
    *,
    profile: dict[str, Any],
    data: pd.DataFrame,
    source_policies: list[str],
    max_candidates: int = 20,
    warmup_bars: int = 50,
    min_spacing_bars: int = 3,
    data_hash: str | None = None,
    index_offset: int = 0,
) -> list[CandidateSetup]:
    if profile.get("timeframe") != "4h":
        raise ValueError("Candidate setup review is limited to 4h in V1.8C.3.")
    if data.empty:
        return []
    prepared = data.reset_index(drop=True)
    if "candle_close_timestamp" not in prepared.columns:
        prepared = _with_candle_times(prepared, profile)
    data_hash = data_hash or _data_hash(prepared)
    candidates: list[CandidateSetup] = []
    last_index = -10_000
    for replay_index in range(warmup_bars - 1, len(prepared)):
        if replay_index - last_index < min_spacing_bars:
            continue
        window = prepared.iloc[: replay_index + 1].copy()
        context = build_policy_context(profile, window)
        for policy in source_policies:
            decision = decide_with_policy(policy, context, seed=replay_index)
            if decision.decision.value not in {"LONG", "SHORT"}:
                continue
            current_price = float(context["market"]["last_close"])
            candidates.append(
                CandidateSetup(
                    candidate_id=_candidate_id(
                        profile=profile,
                        data_hash=data_hash,
                        replay_index=index_offset + replay_index,
                        policy=policy,
                        decision=decision.decision.value,
                    ),
                    profile=profile["name"],
                    asset=profile["symbol"],
                    timeframe=profile["timeframe"],
                    decision_timestamp=pd.Timestamp(
                        window["candle_close_timestamp"].iloc[-1]
                    ).isoformat(),
                    baseline_policy=policy,
                    baseline_decision=decision.decision.value,
                    baseline_strategy=decision.strategy.value,
                    baseline_confidence_hint=float(decision.confidence),
                    baseline_reason_summary=decision.reasoning_summary,
                    current_price=current_price,
                    suggested_stop_loss=decision.stop_loss,
                    suggested_take_profit=decision.take_profit,
                    recent_market_summary={
                        "last_close": current_price,
                        "last_high": float(window["high"].iloc[-1]),
                        "last_low": float(window["low"].iloc[-1]),
                        "bars_seen": len(window),
                    },
                    context_index=index_offset + replay_index,
                    data_hash=data_hash,
                )
            )
            last_index = replay_index
            break
        if len(candidates) >= max_candidates:
            break
    return candidates


def build_policy_context(profile: dict[str, Any], window: pd.DataFrame) -> dict[str, Any]:
    indicators = compute_technical_indicators(window)
    vol = realized_volatility(window)
    indicators["realized_volatility"] = vol
    regime = detect_market_regime(indicators, vol)
    indicators["market_regime"] = regime
    derivatives = unavailable_derivatives("BTC/USDT:USDT")
    scenarios = build_scenarios(indicators, regime, derivatives)
    return {
        "profile": profile,
        "market": {
            "last_open": float(window["open"].iloc[-1]),
            "last_high": float(window["high"].iloc[-1]),
            "last_low": float(window["low"].iloc[-1]),
            "last_close": float(window["close"].iloc[-1]),
            "last_volume": float(window["volume"].iloc[-1]),
            "candle_open_timestamp": pd.Timestamp(
                window["candle_open_timestamp"].iloc[-1]
            ).isoformat(),
            "candle_close_timestamp": pd.Timestamp(
                window["candle_close_timestamp"].iloc[-1]
            ).isoformat(),
        },
        "indicators": indicators,
        "derivatives": derivatives,
        "scenarios": scenarios,
        "data_quality": assess_ohlcv_quality(window),
        "portfolio": {
            "open_positions": [],
            "current_position": None,
            "current_price": float(window["close"].iloc[-1]),
            "timestamp": pd.Timestamp(window["candle_close_timestamp"].iloc[-1]).isoformat(),
            "replay_index": len(window) - 1,
            "bars_in_position": 0,
            "unrealized_pnl": 0.0,
        },
        "ohlcv_window": window.tail(40).to_dict("records"),
        "recent_decisions": [],
        "recent_trades": [],
    }


def candidate_to_dict(candidate: CandidateSetup) -> dict[str, Any]:
    return asdict(candidate)


def _candidate_id(
    *,
    profile: dict[str, Any],
    data_hash: str,
    replay_index: int,
    policy: str,
    decision: str,
) -> str:
    payload = "|".join(
        [
            str(profile["name"]),
            str(profile["symbol"]),
            str(profile["timeframe"]),
            str(data_hash),
            str(replay_index),
            str(policy),
            str(decision),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _with_candle_times(data: pd.DataFrame, profile: dict[str, Any]) -> pd.DataFrame:
    enriched = data.copy()
    enriched["candle_open_timestamp"] = pd.to_datetime(enriched["timestamp"])
    enriched["candle_close_timestamp"] = enriched["candle_open_timestamp"].apply(
        lambda timestamp: candle_close_time(timestamp, profile["timeframe"])
    )
    enriched["available_at_utc"] = enriched["candle_close_timestamp"]
    return enriched


def _data_hash(data: pd.DataFrame) -> str:
    return hashlib.sha256(data.to_csv(index=False).encode("utf-8")).hexdigest()

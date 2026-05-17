"""Ledger builder to transform signals into trade candidates."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

import pandas as pd

from .policy import atr_proxy_policy, fixed_percent_policy, horizon_only_policy
from .schema import TradeCandidate, TradeSide


def build_trade_candidates(
    signals_df: pd.DataFrame,
    ohlcv_4h_df: pd.DataFrame,
    policy_name: str,
    config: dict[str, Any] = None,
) -> list[TradeCandidate]:
    """Transform signals into TradeCandidate instances based on a policy."""
    candidates = []
    config = config or {}

    # Standardize OHLCV
    ohlcv_4h_df = ohlcv_4h_df.copy()
    ohlcv_4h_df["timestamp"] = pd.to_datetime(ohlcv_4h_df["timestamp"])
    if ohlcv_4h_df["timestamp"].dt.tz is None:
        ohlcv_4h_df["timestamp"] = ohlcv_4h_df["timestamp"].dt.tz_localize("UTC")

    # Pre-calculate ATR proxy if needed
    if policy_name == "atr_proxy":
        ohlcv_4h_df["tr"] = (ohlcv_4h_df["high"] - ohlcv_4h_df["low"]) / ohlcv_4h_df["close"]
        ohlcv_4h_df["atr_pct"] = ohlcv_4h_df["tr"].rolling(14).mean()

    for _, sig in signals_df.iterrows():
        ts = sig["timestamp"]
        side_str = sig.get("side_suggestion", "LONG")

        # Entry logic: prefer open of the next 4h candle
        next_candle_ts = ts + timedelta(hours=4)
        entry_row = ohlcv_4h_df[ohlcv_4h_df["timestamp"] == next_candle_ts]

        if not entry_row.empty:
            entry_price = entry_row.iloc[0]["open"]
            entry_time = next_candle_ts
            fallback = False
            current_row = entry_row
        else:
            # Fallback: use current signal candle close
            fallback_row = ohlcv_4h_df[ohlcv_4h_df["timestamp"] == ts]
            if fallback_row.empty:
                continue
            entry_price = fallback_row.iloc[0]["close"]
            entry_time = ts
            fallback = True
            current_row = fallback_row

        # Apply deterministic policy
        if policy_name == "fixed_percent":
            params = fixed_percent_policy(entry_price, side_str)
        elif policy_name == "atr_proxy":
            atr_val = current_row.iloc[0].get("atr_pct", 0.015)  # Fallback to 1.5% ATR if missing
            params = atr_proxy_policy(entry_price, side_str, atr_val)
        else:  # horizon_only
            params = horizon_only_policy(
                entry_price, side_str, bars=config.get("max_holding_bars", 6)
            )

        max_holding_bars = params["max_holding_bars"]
        max_holding_time = entry_time + timedelta(hours=4 * max_holding_bars)

        try:
            candidate = TradeCandidate(
                candidate_id=f"sig_{ts.strftime('%Y%m%dT%H%M')}_entry_{entry_time.strftime('%Y%m%dT%H%M')}_{policy_name}_{side_str}",
                signal_time=ts,
                entry_time=entry_time,
                side=TradeSide(side_str),
                entry_price=entry_price,
                stop_loss=params["stop_loss"],
                take_profit=params["take_profit"],
                max_holding_bars=max_holding_bars,
                max_holding_time=max_holding_time,
                source=sig.get("model_name", "unknown"),
                source_version=sig.get("source_version", "v1.16.3"),
                signal_score=sig.get("signal_score"),
                confidence=sig.get("confidence"),
                policy_name=policy_name,
                policy_version="v1.19.1",
                policy_parameters=params,
                data_availability={"fallback_entry": fallback},
                research_only=True,
            )
            candidates.append(candidate)
        except Exception:
            # Skip invalid candidates silently for now (e.g. SL/TP issues)
            continue

    return candidates

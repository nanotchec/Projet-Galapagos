from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any

import pandas as pd

from galapagos.backtest.timeframe_utils import candle_close_time, timeframe_to_timedelta


class AntiLeakageError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReplayWindowCheck:
    replay_index: int
    rows_seen: int
    last_candle_open: pd.Timestamp
    last_candle_close: pd.Timestamp
    decision_timestamp: pd.Timestamp
    timeframe: str
    passed: bool


def assert_strictly_increasing_timestamps(
    df: pd.DataFrame,
    *,
    timestamp_column: str = "timestamp",
) -> None:
    if not df[timestamp_column].is_monotonic_increasing:
        raise AntiLeakageError("OHLCV timestamps are not strictly increasing")
    if df[timestamp_column].duplicated().any():
        raise AntiLeakageError("OHLCV timestamps contain duplicates")


def check_timeframe_gaps(
    df: pd.DataFrame,
    *,
    timeframe: str,
    timestamp_column: str = "candle_open_timestamp",
) -> dict[str, Any]:
    expected = pd.Timedelta(timeframe_to_timedelta(timeframe))
    diffs = pd.to_datetime(df[timestamp_column]).diff().dropna()
    abnormal = diffs[diffs != expected]
    status = "ok" if abnormal.empty else "degraded"
    if not abnormal.empty:
        warnings.warn(
            f"OHLCV timeframe gaps detected for {timeframe}: {len(abnormal)} abnormal gaps",
            RuntimeWarning,
            stacklevel=2,
        )
    return {
        "status": status,
        "expected_seconds": expected.total_seconds(),
        "abnormal_gap_count": int(len(abnormal)),
    }


def assert_replay_window(
    window: pd.DataFrame,
    *,
    replay_index: int,
    decision_timestamp: pd.Timestamp,
    timeframe: str,
    warmup_bars: int,
) -> ReplayWindowCheck:
    if len(window) < warmup_bars:
        raise AntiLeakageError("Not enough warmup bars before decision")
    if len(window) != replay_index + 1:
        raise AntiLeakageError("Replay index does not match visible window length")
    open_column = (
        "candle_open_timestamp" if "candle_open_timestamp" in window.columns else "timestamp"
    )
    visible = window.copy()
    visible[open_column] = pd.to_datetime(visible[open_column])
    if "candle_close_timestamp" not in visible.columns:
        visible["candle_close_timestamp"] = visible[open_column].apply(
            lambda timestamp: candle_close_time(timestamp, timeframe)
        )
    else:
        visible["candle_close_timestamp"] = pd.to_datetime(visible["candle_close_timestamp"])

    last_open = pd.Timestamp(visible[open_column].iloc[-1])
    last_close = pd.Timestamp(visible["candle_close_timestamp"].iloc[-1])
    decision_ts = pd.Timestamp(decision_timestamp)
    if decision_ts < last_close:
        raise AntiLeakageError(
            "Decision timestamp is before the visible candle close; "
            "this would use close/high/low/volume at candle open"
        )
    if (visible[open_column] >= decision_ts).any():
        raise AntiLeakageError("Replay window contains a candle opening at or after decision time")
    if visible["candle_close_timestamp"].max() > decision_ts:
        raise AntiLeakageError("Replay window contains candles not yet available at decision time")
    return ReplayWindowCheck(
        replay_index=replay_index,
        rows_seen=len(window),
        last_candle_open=last_open,
        last_candle_close=last_close,
        decision_timestamp=decision_ts,
        timeframe=timeframe,
        passed=True,
    )

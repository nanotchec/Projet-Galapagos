from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class EvaluationWindow:
    label: str
    start_index: int
    end_index: int
    start_timestamp: str
    end_timestamp: str
    bars: int
    data_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def split_ohlcv_into_windows(
    data: pd.DataFrame,
    n_windows: int,
    min_bars_per_window: int,
) -> list[EvaluationWindow]:
    _assert_valid_ohlcv(data)
    if n_windows <= 0:
        raise ValueError("n_windows must be positive.")
    if min_bars_per_window <= 0:
        raise ValueError("min_bars_per_window must be positive.")
    if len(data) < n_windows * min_bars_per_window:
        raise ValueError(
            f"Insufficient history: {len(data)} bars for {n_windows} windows "
            f"with at least {min_bars_per_window} bars each."
        )
    base_size = len(data) // n_windows
    windows: list[EvaluationWindow] = []
    for index in range(n_windows):
        start = index * base_size
        end = (index + 1) * base_size if index < n_windows - 1 else len(data)
        windows.append(select_candidate_window(data, f"window_{index + 1}", start, end))
    ensure_no_overlap(windows)
    return windows


def select_candidate_window(
    data: pd.DataFrame,
    label: str,
    start_index: int,
    end_index: int,
) -> EvaluationWindow:
    _assert_valid_ohlcv(data)
    if start_index < 0 or end_index > len(data) or start_index >= end_index:
        raise ValueError(
            f"Invalid window indexes for {label}: start={start_index}, end={end_index}."
        )
    window = data.iloc[start_index:end_index].copy()
    timestamps = _timestamps(window)
    return EvaluationWindow(
        label=label,
        start_index=start_index,
        end_index=end_index,
        start_timestamp=pd.Timestamp(timestamps.iloc[0]).isoformat(),
        end_timestamp=pd.Timestamp(timestamps.iloc[-1]).isoformat(),
        bars=len(window),
        data_hash=_data_hash(window),
    )


def ensure_no_overlap(windows: list[EvaluationWindow]) -> bool:
    ordered = sorted(windows, key=lambda item: item.start_index)
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if current.start_index < previous.end_index:
            raise ValueError(
                f"Evaluation windows overlap: {previous.label} and {current.label}."
            )
    return True


def _assert_valid_ohlcv(data: pd.DataFrame) -> None:
    if data.empty:
        raise ValueError("OHLCV data is empty.")
    timestamps = _timestamps(data)
    if not timestamps.is_monotonic_increasing:
        raise ValueError("OHLCV timestamps must be increasing.")
    if timestamps.duplicated().any():
        raise ValueError("OHLCV timestamps must not contain duplicates.")


def _timestamps(data: pd.DataFrame) -> pd.Series:
    if "timestamp" in data.columns:
        return pd.to_datetime(data["timestamp"])
    if "candle_open_timestamp" in data.columns:
        return pd.to_datetime(data["candle_open_timestamp"])
    raise ValueError("OHLCV data must contain timestamp or candle_open_timestamp.")


def _data_hash(data: pd.DataFrame) -> str:
    return hashlib.sha256(data.to_csv(index=False).encode("utf-8")).hexdigest()


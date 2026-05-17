from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd


def compute_forward_returns(
    data: pd.DataFrame,
    horizons: Iterable[int] = (1, 3, 6, 12),
) -> pd.DataFrame:
    labeled = data.copy()
    close = labeled["close"].astype(float)
    for horizon in horizons:
        labeled[f"forward_return_{horizon}bar"] = close.shift(-int(horizon)) / close - 1.0
    return labeled


def compute_mfe_mae(data: pd.DataFrame, horizons: Iterable[int] = (1, 3, 6, 12)) -> pd.DataFrame:
    labeled = data.copy()
    close = labeled["close"].astype(float)
    high = labeled["high"].astype(float)
    low = labeled["low"].astype(float)
    for horizon in horizons:
        mfe_values: list[float | None] = []
        mae_values: list[float | None] = []
        for index, entry in enumerate(close):
            future = slice(index + 1, index + int(horizon) + 1)
            if index + int(horizon) >= len(labeled):
                mfe_values.append(None)
                mae_values.append(None)
                continue
            mfe_values.append(float(high.iloc[future].max() / entry - 1.0))
            mae_values.append(float(low.iloc[future].min() / entry - 1.0))
        labeled[f"max_favorable_excursion_{horizon}bar"] = mfe_values
        labeled[f"max_adverse_excursion_{horizon}bar"] = mae_values
    return labeled


def compute_directional_labels(data: pd.DataFrame, cost_threshold: float) -> pd.DataFrame:
    labeled = data.copy()
    for horizon in (3, 6):
        column = f"forward_return_{horizon}bar"
        if column not in labeled.columns:
            labeled = compute_forward_returns(labeled, horizons=[horizon])
        labeled[f"direction_up_after_cost_{horizon}bar"] = labeled[column].apply(
            lambda value: None if pd.isna(value) else bool(float(value) > cost_threshold)
        )
    return labeled


def compute_tp_sl_first_label(
    data: pd.DataFrame,
    tp_pct: float,
    sl_pct: float,
    horizon_bars: int,
    intrabar_mode: str = "ohlcv_conservative",
) -> pd.DataFrame:
    if intrabar_mode != "ohlcv_conservative":
        raise ValueError("Only ohlcv_conservative is supported in V1.11 research labels.")
    labeled = data.copy()
    close = labeled["close"].astype(float)
    high = labeled["high"].astype(float)
    low = labeled["low"].astype(float)
    values: list[bool | None] = []
    for index, entry in enumerate(close):
        if index + horizon_bars >= len(labeled):
            values.append(None)
            continue
        tp = entry * (1.0 + tp_pct)
        sl = entry * (1.0 - sl_pct)
        outcome: bool | None = None
        for future_index in range(index + 1, index + horizon_bars + 1):
            hit_tp = high.iloc[future_index] >= tp
            hit_sl = low.iloc[future_index] <= sl
            if hit_sl:
                outcome = False
                break
            if hit_tp:
                outcome = True
                break
        values.append(outcome)
    labeled["tp_before_sl_conservative"] = values
    return labeled


def add_research_labels(data: pd.DataFrame, cost_threshold: float = 0.003) -> pd.DataFrame:
    labeled = compute_forward_returns(data)
    labeled = compute_mfe_mae(labeled)
    labeled = compute_directional_labels(labeled, cost_threshold=cost_threshold)
    return compute_tp_sl_first_label(labeled, tp_pct=0.02, sl_pct=0.01, horizon_bars=6)


def label_row_snapshot(row: pd.Series) -> dict[str, Any]:
    keys = [key for key in row.index if "forward_return" in key or "excursion" in key]
    return {key: (None if pd.isna(row[key]) else row[key]) for key in keys}

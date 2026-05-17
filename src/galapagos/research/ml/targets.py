"""ML target / label construction — research-only, uses future for labels only."""
from __future__ import annotations

import pandas as pd

REGRESSION_TARGETS = [
    "target_return_1bar",
    "target_return_3bar",
    "target_return_6bar",
    "target_return_12bar",
]

CLASSIFICATION_TARGETS = [
    "target_up_after_cost_3bar",
    "target_up_after_cost_6bar",
    "target_up_after_cost_12bar",
    "target_large_move_up_6bar",
    "target_large_move_down_6bar",
    "target_abs_move_after_cost_6bar",
]

TP_SL_TARGETS = [
    "target_tp_before_sl_conservative",
    "target_sl_before_tp_conservative",
]

ALL_TARGET_COLUMNS = REGRESSION_TARGETS + CLASSIFICATION_TARGETS + TP_SL_TARGETS

TARGET_HORIZONS = {
    "target_return_1bar": 1,
    "target_return_3bar": 3,
    "target_return_6bar": 6,
    "target_return_12bar": 12,
    "target_up_after_cost_3bar": 3,
    "target_up_after_cost_6bar": 6,
    "target_up_after_cost_12bar": 12,
    "target_large_move_up_6bar": 6,
    "target_large_move_down_6bar": 6,
    "target_abs_move_after_cost_6bar": 6,
    "target_tp_before_sl_conservative": 6,
    "target_sl_before_tp_conservative": 6,
}


def build_ml_targets(
    dataset: pd.DataFrame,
    *,
    cost_threshold: float = 0.003,
    large_move_threshold: float = 0.03,
    tp_pct: float = 0.02,
    sl_pct: float = 0.01,
    tp_sl_horizon: int = 6,
) -> pd.DataFrame:
    """Build all ML targets from research dataset. Future is used only for labels."""
    frame = dataset.copy()
    close = pd.to_numeric(frame["close"], errors="coerce")
    high = pd.to_numeric(frame["high"], errors="coerce")
    low = pd.to_numeric(frame["low"], errors="coerce")

    # Regression targets
    for horizon in (1, 3, 6, 12):
        col = f"target_return_{horizon}bar"
        frame[col] = close.shift(-horizon) / close - 1.0

    # Classification: up after cost
    for horizon in (3, 6, 12):
        ret_col = f"target_return_{horizon}bar"
        frame[f"target_up_after_cost_{horizon}bar"] = frame[ret_col].apply(
            lambda v: None if pd.isna(v) else int(v > cost_threshold)
        )

    # Large moves
    ret_6 = frame["target_return_6bar"]
    frame["target_large_move_up_6bar"] = ret_6.apply(
        lambda v: None if pd.isna(v) else int(v > large_move_threshold)
    )
    frame["target_large_move_down_6bar"] = ret_6.apply(
        lambda v: None if pd.isna(v) else int(v < -large_move_threshold)
    )
    frame["target_abs_move_after_cost_6bar"] = ret_6.apply(
        lambda v: None if pd.isna(v) else int(abs(v) > cost_threshold)
    )

    # TP/SL conservative
    tp_values: list[int | None] = []
    sl_values: list[int | None] = []
    for idx in range(len(frame)):
        if idx + tp_sl_horizon >= len(frame):
            tp_values.append(None)
            sl_values.append(None)
            continue
        entry = close.iloc[idx]
        tp_level = entry * (1.0 + tp_pct)
        sl_level = entry * (1.0 - sl_pct)
        outcome: int | None = None
        for future_idx in range(idx + 1, idx + tp_sl_horizon + 1):
            hit_sl = low.iloc[future_idx] <= sl_level
            hit_tp = high.iloc[future_idx] >= tp_level
            if hit_sl:
                outcome = 0  # SL first
                break
            if hit_tp:
                outcome = 1  # TP first
                break
        tp_values.append(outcome if outcome is not None else None)
        sl_values.append(
            (1 - outcome) if outcome is not None else None
        )
    frame["target_tp_before_sl_conservative"] = tp_values
    frame["target_sl_before_tp_conservative"] = sl_values

    return frame


def target_report(frame: pd.DataFrame) -> dict:
    """Summary of target distribution and NaN counts."""
    report: dict = {"targets": {}}
    for col in ALL_TARGET_COLUMNS:
        if col not in frame.columns:
            continue
        series = frame[col]
        valid = series.dropna()
        info: dict = {
            "total_rows": len(series),
            "nan_count": int(series.isna().sum()),
            "valid_count": len(valid),
            "horizon_bars": TARGET_HORIZONS.get(col),
        }
        if col in REGRESSION_TARGETS and len(valid):
            info["mean"] = float(valid.mean())
            info["std"] = float(valid.std())
            info["min"] = float(valid.min())
            info["max"] = float(valid.max())
        elif len(valid):
            info["class_distribution"] = valid.value_counts().to_dict()
            info["base_rate_positive"] = float(
                (valid == 1).sum() / len(valid) if len(valid) else 0
            )
        report["targets"][col] = info
    return report

"""Feature shift diagnostics for payoff-objective failure."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def analyze_feature_shift(analysis_frame: pd.DataFrame) -> dict[str, Any]:
    frame = analysis_frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    pre = frame[frame["timestamp"].dt.year < 2026].copy()
    recent = frame[frame["timestamp"].dt.year == 2026].copy()
    numeric_columns = [
        column
        for column in [
            "predicted_probability",
            "predicted_probability_calibrated",
            "ev_calibrated_proxy",
            "avg_win_past",
            "avg_loss_past",
            "combined_alpha_score",
            "combined_alpha_score_no_derivatives",
            "combined_alpha_score_no_macro",
            "ohlcv_only_alpha_score",
            "macro_derivatives_score",
            "ohlcv_momentum_score",
            "ohlcv_breakout_score",
            "volatility_quality_score",
            "macro_regime_score",
            "cost_penalty_score",
            "crowded_trade_penalty",
            "missing_data_penalty",
            "volume_quality_score",
            "derivatives_regime_score",
            "derivatives_crowding_score",
            "derivatives_leverage_score",
            "derivatives_score",
            "funding_rate_zscore_30d",
            "funding_rate_zscore_90d",
            "open_interest_zscore_30d",
            "open_interest_zscore_90d",
            "premium_zscore_30d",
            "taker_imbalance_zscore",
            "long_short_ratio_zscore",
        ]
        if column in frame.columns
    ]
    rows = []
    for column in numeric_columns:
        pre_series = pd.to_numeric(pre[column], errors="coerce").dropna()
        recent_series = pd.to_numeric(recent[column], errors="coerce").dropna()
        if pre_series.empty or recent_series.empty:
            continue
        pre_mean = float(pre_series.mean())
        recent_mean = float(recent_series.mean())
        pre_std = float(pre_series.std() or 1e-9)
        recent_std = float(recent_series.std() or 1e-9)
        shift_score = abs(recent_mean - pre_mean) / (pre_std + recent_std + 1e-9)
        missingness_shift = float(recent[column].isna().mean() - pre[column].isna().mean())
        rows.append(
            {
                "feature": column,
                "pre_mean": pre_mean,
                "recent_mean": recent_mean,
                "pre_std": pre_std,
                "recent_std": recent_std,
                "shift_score": shift_score,
                "missingness_shift": missingness_shift,
            }
        )
    rows = sorted(rows, key=lambda item: item["shift_score"], reverse=True)
    top_shift_score = rows[0]["shift_score"] if rows else 0.0
    if top_shift_score >= 0.35:
        status = "PAYOFF_FEATURE_SHIFT_DETECTED_2026"
    elif top_shift_score >= 0.15:
        status = "PAYOFF_FEATURE_SHIFT_LIMITED"
    else:
        status = "PAYOFF_FEATURE_SHIFT_DIAGNOSTIC_INCONCLUSIVE"
    return {
        "feature_shift_status": status,
        "top_shift_score": top_shift_score,
        "top_shifted_features": rows[:10],
        "feature_count": int(len(rows)),
        "pre_rows": int(len(pre)),
        "recent_rows": int(len(recent)),
    }


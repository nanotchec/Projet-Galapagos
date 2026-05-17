"""Explicit EV/cost feature rebuild for V1.38."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from galapagos.research.calibration_ev.prediction_frame_builder import build_prediction_frames
from galapagos.research.walk_forward_calibration.platt_calibrator import PlattCalibrator
from galapagos.research.walk_forward_calibration.split_builder import build_walk_forward_splits


def rebuild_canonical_ev_features(
    df: pd.DataFrame,
    *,
    cost_proxy_bps: float = 10.0,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Rebuild calibrated probability, payoff estimates and EV/cost proxies causally."""
    frame = df.copy()
    if "timestamp" not in frame.columns:
        raise ValueError("timestamp column is required for canonical EV rebuild")

    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True).dt.tz_convert(None)
    frame = frame.sort_values("timestamp").reset_index(drop=True)

    required = {"predicted_probability", "actual_target", "forward_return_12bar"}
    missing_required = sorted(required - set(frame.columns))
    if missing_required:
        raise ValueError(f"Missing required columns for EV rebuild: {missing_required}")

    frame["calibrated_probability_rebuilt"] = np.nan
    frame["calibrated_probability"] = np.nan
    frame["predicted_probability_calibrated"] = np.nan
    frame["avg_win_past_rebuilt"] = np.nan
    frame["avg_loss_past_rebuilt"] = np.nan
    frame["avg_win_past"] = np.nan
    frame["avg_loss_past"] = np.nan
    frame["cost_proxy_rebuilt"] = cost_proxy_bps / 10000.0
    frame["cost_proxy"] = frame["cost_proxy_rebuilt"]
    frame["ev_calibrated_proxy_rebuilt"] = np.nan
    frame["ev_calibrated_proxy"] = np.nan
    frame["ev_raw_proxy"] = np.nan

    calibration_rows = 0
    fallback_probability_used = False
    splits = build_walk_forward_splits(frame)
    for split in splits:
        train_mask = (frame["timestamp"] >= split.train_start) & (frame["timestamp"] <= split.train_end)
        test_mask = (frame["timestamp"] >= split.test_start) & (frame["timestamp"] <= split.test_end)
        train_df = frame.loc[train_mask, ["predicted_probability", "actual_target"]].dropna()
        test_df = frame.loc[test_mask, ["predicted_probability"]].dropna()
        if len(train_df) < 100 or len(test_df) == 0:
            continue
        calibrator = PlattCalibrator()
        calibrator.fit(train_df["actual_target"].to_numpy(), train_df["predicted_probability"].to_numpy())
        calibrated = calibrator.predict(test_df["predicted_probability"].to_numpy())
        frame.loc[test_df.index, "calibrated_probability_rebuilt"] = calibrated
        calibration_rows += len(test_df)

    wins = frame["forward_return_12bar"].where(frame["actual_target"] == 1)
    losses = frame["forward_return_12bar"].where(frame["actual_target"] == 0)
    frame["avg_win_past_rebuilt"] = wins.shift(1).expanding(min_periods=100).mean()
    frame["avg_loss_past_rebuilt"] = losses.shift(1).expanding(min_periods=100).mean()
    frame["avg_win_past"] = frame["avg_win_past_rebuilt"]
    frame["avg_loss_past"] = frame["avg_loss_past_rebuilt"]

    ready_mask = (
        frame["calibrated_probability_rebuilt"].notna()
        & frame["avg_win_past_rebuilt"].notna()
        & frame["avg_loss_past_rebuilt"].notna()
    )
    frame.loc[ready_mask, "ev_calibrated_proxy_rebuilt"] = _ev_from_components(
        frame.loc[ready_mask]
    )
    frame["ev_calibrated_proxy"] = frame["ev_calibrated_proxy_rebuilt"]
    frame["predicted_probability_calibrated"] = frame["calibrated_probability_rebuilt"]
    frame.loc[ready_mask, "ev_raw_proxy"] = _ev_from_raw_probability(frame.loc[ready_mask])
    frame["ev_proxy_ready"] = frame["ev_calibrated_proxy"].notna()
    frame["payoff_estimate_ready"] = frame["avg_win_past"].notna() & frame["avg_loss_past"].notna()

    selection_frame, outcome_frame, split_integrity = build_prediction_frames(frame)
    selection_forbidden = split_integrity.get("forbidden_columns_in_selection", [])

    ev_ready_rows = int(frame["ev_proxy_ready"].sum())
    warmup_blocked_rows = int((~frame["ev_proxy_ready"]).sum())
    result = {
        "rebuild_rows": int(len(frame)),
        "rebuild_rows_2026": int(frame["timestamp"].astype(str).str.contains("2026").sum()),
        "calibrated_probability_rebuilt": {
            "rows_with_values": int(frame["calibrated_probability_rebuilt"].notna().sum()),
            "rows_without_values": int(frame["calibrated_probability_rebuilt"].isna().sum()),
            "calibration_splits": len(splits),
            "calibration_rows_written": calibration_rows,
        },
        "payoff_estimates_rebuilt": {
            "avg_win_past_rows": int(frame["avg_win_past"].notna().sum()),
            "avg_loss_past_rows": int(frame["avg_loss_past"].notna().sum()),
            "payoff_ready_rows": int(frame["payoff_estimate_ready"].sum()),
        },
        "cost_proxy_rebuilt": {
            "fixed_cost_bps": cost_proxy_bps,
            "fixed_cost_pct": cost_proxy_bps / 10000.0,
        },
        "ev_calibrated_proxy_rebuilt": {
            "rows_with_values": ev_ready_rows,
            "rows_without_values": warmup_blocked_rows,
        },
        "warmup_blocked_rows": warmup_blocked_rows,
        "ev_ready_rows": ev_ready_rows,
        "ev_ready_rows_2026": int(
            frame.loc[frame["timestamp"].astype(str).str.contains("2026"), "ev_proxy_ready"].sum()
        ),
        "default_payoff_used": False,
        "fallback_probability_used": fallback_probability_used,
        "artificial_probability_threshold_used": False,
        "selection_frame_forbidden_columns": selection_forbidden,
        "selection_frame_status": split_integrity.get("selection_frame_status"),
        "outcome_frame_status": split_integrity.get("outcome_frame_status"),
        "selection_outcome_split_status": split_integrity.get("integrity_status"),
        "ev_feature_rebuild_status": (
            "EV_NET_FEATURE_REBUILD_COMPLETE"
            if ev_ready_rows > 0 and not fallback_probability_used
            else "EV_NET_FEATURE_REBUILD_PARTIAL"
        ),
        "selection_dataset_rows": int(len(selection_frame)),
        "outcome_dataset_rows": int(len(outcome_frame)),
    }
    if ev_ready_rows == 0:
        result["ev_feature_rebuild_status"] = "EV_NET_FEATURE_REBUILD_FAILED"
    return frame, result


def _ev_from_components(frame: pd.DataFrame) -> pd.Series:
    calibrated_probability = pd.to_numeric(
        frame["calibrated_probability_rebuilt"], errors="coerce"
    ).fillna(0.5)
    avg_win = pd.to_numeric(frame["avg_win_past_rebuilt"], errors="coerce").fillna(0.0)
    avg_loss = pd.to_numeric(frame["avg_loss_past_rebuilt"], errors="coerce").fillna(0.0)
    cost = pd.to_numeric(frame["cost_proxy_rebuilt"], errors="coerce").fillna(0.001)
    return calibrated_probability * avg_win + (1.0 - calibrated_probability) * avg_loss - cost


def _ev_from_raw_probability(frame: pd.DataFrame) -> pd.Series:
    raw_probability = pd.to_numeric(frame["predicted_probability"], errors="coerce").fillna(0.5)
    avg_win = pd.to_numeric(frame["avg_win_past_rebuilt"], errors="coerce").fillna(0.0)
    avg_loss = pd.to_numeric(frame["avg_loss_past_rebuilt"], errors="coerce").fillna(0.0)
    cost = pd.to_numeric(frame["cost_proxy_rebuilt"], errors="coerce").fillna(0.001)
    return raw_probability * avg_win + (1.0 - raw_probability) * avg_loss - cost

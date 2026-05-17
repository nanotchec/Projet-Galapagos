"""Signal loader for trade candidates."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def load_ml_signals(
    predictions_path: str,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
    selection_policy: str = "max_predicted_probability",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load and audit ML signals from parquet."""
    audit = {
        "raw_signal_rows": 0,
        "unique_signal_timestamps": 0,
        "duplicate_signal_rows": 0,
        "duplicates_per_timestamp_max": 0,
        "selected_signal_policy": selection_policy,
        "models_count": 0,
        "feature_sets_count": 0,
        "targets_count": 0,
    }

    if not Path(predictions_path).exists():
        return pd.DataFrame(), audit

    df = pd.read_parquet(predictions_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

    if start_time:
        if start_time.tzinfo is None:
            start_time = start_time.tz_localize("UTC")
        df = df[df["timestamp"] >= start_time]
    if end_time:
        if end_time.tzinfo is None:
            end_time = end_time.tz_localize("UTC")
        df = df[df["timestamp"] <= end_time]

    # Only predicted_label == 1 are considered candidates (LONG)
    # We keep predicted_label == 0 as WAIT if we want to evaluate everything,
    # but the instruction says "predicted_label == 1 => LONG candidate".
    signals_raw = df[df["predicted_label"] == 1].copy()
    audit["raw_signal_rows"] = len(signals_raw)

    if signals_raw.empty:
        return pd.DataFrame(), audit

    audit["models_count"] = (
        signals_raw["model_name"].nunique() if "model_name" in signals_raw.columns else 0
    )
    audit["feature_sets_count"] = (
        signals_raw["feature_set"].nunique() if "feature_set" in signals_raw.columns else 0
    )
    audit["targets_count"] = (
        signals_raw["target"].nunique() if "target" in signals_raw.columns else 0
    )

    ts_counts = signals_raw.groupby("timestamp").size()
    audit["unique_signal_timestamps"] = len(ts_counts)
    audit["duplicate_signal_rows"] = audit["raw_signal_rows"] - audit["unique_signal_timestamps"]
    audit["duplicates_per_timestamp_max"] = int(ts_counts.max())

    # Deduplicate: keep max predicted_probability by default
    if selection_policy == "max_predicted_probability" and "predicted_probability" in df.columns:
        signals_dedup = signals_raw.sort_values(
            "predicted_probability", ascending=False
        ).drop_duplicates("timestamp")
    else:
        # Default or fallback
        signals_dedup = signals_raw.drop_duplicates("timestamp")

    # Final cleanup and formatting
    signals_dedup = signals_dedup.sort_values("timestamp")
    signals_dedup["side_suggestion"] = "LONG"
    signals_dedup["signal_score"] = signals_dedup.get("predicted_probability", 0.0)
    signals_dedup["confidence"] = signals_dedup.get("predicted_probability", 0.0)

    return signals_dedup, audit

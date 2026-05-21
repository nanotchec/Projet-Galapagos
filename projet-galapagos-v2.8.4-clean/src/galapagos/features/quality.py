from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any

from galapagos.features.schemas import FEATURE_COLUMNS_V2_5, FORBIDDEN_TERMS


def assess_feature_quality(
    df: pd.DataFrame,
    expected_rows: int,
    timeframe: str,
) -> dict[str, Any]:
    """Assesses the physical data quality and causal consistency of a features dataframe."""
    errors: list[str] = []
    warnings: list[str] = []
    
    rows = len(df)
    if rows != expected_rows:
        errors.append(f"{timeframe} features rows mismatch: got {rows}, expected {expected_rows}")
        
    warmup_rows = int(df["warmup_row"].sum()) if "warmup_row" in df.columns else 0
    rows_after_warmup = rows - warmup_rows
    
    # Check duplicates
    duplicate_rows = 0
    if "event_ts" in df.columns:
        duplicate_rows = int(df.duplicated(subset=["event_ts"]).sum())
        if duplicate_rows > 0:
            errors.append(f"{timeframe} features contain {duplicate_rows} duplicate timestamps")
            
    # Check monotonic event_ts
    monotonic_event_ts = False
    if "event_ts" in df.columns and rows > 0:
        event_dt = pd.to_datetime(df["event_ts"], utc=True)
        monotonic_event_ts = bool(event_dt.is_monotonic_increasing)
        if not monotonic_event_ts:
            errors.append(f"{timeframe} features event_ts is not monotonic increasing")
            
    # Check timestamps UTC
    timestamps_utc = False
    if "event_ts" in df.columns and rows > 0:
        event_ts_series = pd.to_datetime(df["event_ts"], utc=True)
        timestamps_utc = str(event_ts_series.dt.tz) == "UTC"
        if not timestamps_utc:
            errors.append(f"{timeframe} features event_ts must be UTC strings ending with Z")
            
    # Check feature available timestamps and decision timestamps
    feature_available_ts_valid = False
    decision_ts_valid = False
    causal_guard_passed = False
    
    if "feature_available_ts" in df.columns and "available_ts" in df.columns:
        avail = pd.to_datetime(df["available_ts"], utc=True)
        feat_avail = pd.to_datetime(df["feature_available_ts"], utc=True)
        feature_available_ts_valid = bool((feat_avail >= avail).all())
        if not feature_available_ts_valid:
            errors.append(f"{timeframe} features contain feature_available_ts < available_ts")
            
        if "decision_ts" in df.columns:
            dec = pd.to_datetime(df["decision_ts"], utc=True)
            decision_ts_valid = bool((dec >= feat_avail).all())
            if not decision_ts_valid:
                errors.append(f"{timeframe} features contain decision_ts < feature_available_ts")
                
            causal_guard_passed = feature_available_ts_valid and decision_ts_valid
            
    # Check forbidden columns
    forbidden_columns_present = False
    for col in df.columns:
        if col in FEATURE_COLUMNS_V2_5:
            continue
        for term in FORBIDDEN_TERMS:
            if term in col.lower():
                forbidden_columns_present = True
                errors.append(f"{timeframe} features contain forbidden column: {col}")
                break
                    
    # Calculate nulls and infs by column on calculated features only
    null_counts: dict[str, int] = {}
    inf_counts: dict[str, int] = {}
    
    # Identify numeric features
    numeric_cols = [
        "close_lag_1", "return_1", "log_return_1", "return_3", "log_return_3",
        "return_5", "log_return_5", "rolling_vol_5", "rolling_vol_15", "rolling_vol_30",
        "candle_range", "candle_body", "upper_wick", "lower_wick", "close_position_in_range",
        "volume_lag_1", "volume_return_1", "rolling_volume_mean_5", "rolling_volume_mean_15",
        "rolling_volume_zscore_15", "sma_5", "sma_15", "sma_30", "close_to_sma_5",
        "close_to_sma_15", "close_to_sma_30"
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            series = df[col]
            nulls = int(series.isna().sum())
            null_counts[col] = nulls
            
            # Check infinities
            try:
                infs = int(np.isinf(series).sum())
            except Exception:
                infs = 0
            inf_counts[col] = infs
            
            if infs > 0:
                errors.append(f"{timeframe} features column {col} contains {infs} infinite values")
                
    return {
        "rows": rows,
        "expected_rows": expected_rows,
        "warmup_rows": warmup_rows,
        "rows_after_warmup": rows_after_warmup,
        "duplicate_rows": duplicate_rows,
        "null_counts_by_column": null_counts,
        "inf_counts_by_column": inf_counts,
        "forbidden_columns_present": forbidden_columns_present,
        "timestamps_utc": timestamps_utc,
        "monotonic_event_ts": monotonic_event_ts,
        "feature_available_ts_valid": feature_available_ts_valid,
        "decision_ts_valid": decision_ts_valid,
        "causal_guard_passed": causal_guard_passed,
        "errors": errors,
        "warnings": warnings,
    }

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from galapagos.features.ohlcv_trades_1y_schemas import (
    FORBIDDEN_OHLCV_TRADES_FEATURE_COLUMNS_V8_3,
    OHLCV_TRADES_FEATURE_COLUMNS_V8_3,
    OHLCV_TRADES_VALUE_COLUMNS_V8_3,
)


def assess_ohlcv_trades_feature_quality_v8_3(
    frame: pd.DataFrame,
    timeframe: str,
    *,
    expected_rows: int,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    rows = int(len(frame))
    if rows != expected_rows:
        errors.append(f"{timeframe} V8.3 rows mismatch: got {rows}, expected {expected_rows}")

    if list(frame.columns) != OHLCV_TRADES_FEATURE_COLUMNS_V8_3:
        errors.append(f"{timeframe} V8.3 feature schema mismatch")

    duplicate_rows = int(frame.duplicated(subset=["event_ts"]).sum()) if "event_ts" in frame.columns else 0
    if duplicate_rows:
        errors.append(f"{timeframe} V8.3 features contain duplicate event_ts rows: {duplicate_rows}")

    timestamps_utc = False
    monotonic_event_ts = False
    if rows and "event_ts" in frame.columns:
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        timestamps_utc = str(event_ts.dt.tz) == "UTC"
        monotonic_event_ts = bool(event_ts.is_monotonic_increasing)
        if not timestamps_utc:
            errors.append(f"{timeframe} V8.3 event_ts must be UTC")
        if not monotonic_event_ts:
            errors.append(f"{timeframe} V8.3 event_ts is not monotonic increasing")

    feature_available_ts_valid = False
    decision_ts_valid = False
    if {"available_ts", "feature_available_ts", "decision_ts"}.issubset(frame.columns):
        available_ts = pd.to_datetime(frame["available_ts"], utc=True)
        feature_available_ts = pd.to_datetime(frame["feature_available_ts"], utc=True)
        decision_ts = pd.to_datetime(frame["decision_ts"], utc=True)
        feature_available_ts_valid = bool((feature_available_ts >= available_ts).all())
        decision_ts_valid = bool((decision_ts >= feature_available_ts).all())
        if not feature_available_ts_valid:
            errors.append(f"{timeframe} V8.3 feature_available_ts < available_ts")
        if not decision_ts_valid:
            errors.append(f"{timeframe} V8.3 decision_ts < feature_available_ts")

    warmup_rows = int(frame["warmup_row"].sum()) if "warmup_row" in frame.columns else 0
    rows_after_warmup = rows - warmup_rows
    if rows >= 60 and warmup_rows < 60:
        errors.append(f"{timeframe} V8.3 warmup rows below expected rolling_60 minimum: {warmup_rows}")

    bars_without_trades = int((frame["agg_trade_count"].fillna(0) == 0).sum()) if "agg_trade_count" in frame.columns else 0
    forbidden_columns = forbidden_columns_present_v8_3(frame)
    if forbidden_columns:
        errors.append(f"{timeframe} V8.3 forbidden columns present: {forbidden_columns}")

    median_volume_relative_diff = _median_relative_diff(frame, "agg_trade_quantity_sum", "volume")
    median_quote_volume_relative_diff = _median_relative_diff(frame, "agg_trade_quote_quantity_sum", "quote_volume")
    if median_volume_relative_diff is not None:
        if median_volume_relative_diff > 0.50:
            errors.append(f"{timeframe} V8.3 median volume relative diff above 0.50: {median_volume_relative_diff}")
        elif median_volume_relative_diff > 0.10:
            warnings.append(f"{timeframe} V8.3 median volume relative diff above 0.10: {median_volume_relative_diff}")
    if median_quote_volume_relative_diff is not None:
        if median_quote_volume_relative_diff > 0.50:
            errors.append(f"{timeframe} V8.3 median quote volume relative diff above 0.50: {median_quote_volume_relative_diff}")
        elif median_quote_volume_relative_diff > 0.10:
            warnings.append(
                f"{timeframe} V8.3 median quote volume relative diff above 0.10: {median_quote_volume_relative_diff}"
            )

    null_counts: dict[str, int] = {}
    inf_counts: dict[str, int] = {}
    for column in OHLCV_TRADES_VALUE_COLUMNS_V8_3:
        if column not in frame.columns:
            null_counts[column] = -1
            inf_counts[column] = -1
            continue
        series = frame[column]
        null_counts[column] = int(series.isna().sum())
        if pd.api.types.is_numeric_dtype(series):
            numeric = series.astype("float64")
            inf_counts[column] = int(np.isinf(numeric).sum())
            if inf_counts[column]:
                errors.append(f"{timeframe} V8.3 feature column {column} contains infinities")
        else:
            inf_counts[column] = 0

    return {
        "rows": rows,
        "expected_rows": int(expected_rows),
        "warmup_rows": warmup_rows,
        "rows_after_warmup": rows_after_warmup,
        "bars_without_trades": bars_without_trades,
        "median_volume_relative_diff": median_volume_relative_diff,
        "median_quote_volume_relative_diff": median_quote_volume_relative_diff,
        "duplicate_rows": duplicate_rows,
        "null_counts_by_column": null_counts,
        "inf_counts_by_column": inf_counts,
        "forbidden_columns_present": bool(forbidden_columns),
        "timestamps_utc": timestamps_utc,
        "monotonic_event_ts": monotonic_event_ts,
        "feature_available_ts_valid": feature_available_ts_valid,
        "decision_ts_valid": decision_ts_valid,
        "source_hashes_valid": False,
        "causal_guard_passed": feature_available_ts_valid and decision_ts_valid,
        "errors": errors,
        "warnings": warnings,
    }


def forbidden_columns_present_v8_3(frame: pd.DataFrame) -> list[str]:
    forbidden: list[str] = []
    for column in frame.columns:
        if column in OHLCV_TRADES_FEATURE_COLUMNS_V8_3:
            continue
        lowered = str(column).casefold()
        if lowered in FORBIDDEN_OHLCV_TRADES_FEATURE_COLUMNS_V8_3:
            forbidden.append(str(column))
    return sorted(forbidden)


def _median_relative_diff(frame: pd.DataFrame, numerator_column: str, denominator_column: str) -> float | None:
    if numerator_column not in frame.columns or denominator_column not in frame.columns:
        return None
    denominator = frame[denominator_column].astype("float64")
    valid = denominator > 0
    if not bool(valid.any()):
        return None
    diff = (frame.loc[valid, numerator_column].astype("float64") - denominator.loc[valid]).abs() / denominator.loc[valid]
    if diff.empty:
        return None
    return float(diff.median())

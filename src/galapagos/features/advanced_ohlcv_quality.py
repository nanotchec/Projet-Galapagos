from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from galapagos.features.advanced_ohlcv_schemas import (
    ADVANCED_OHLCV_FEATURE_COLUMNS_V6_0,
    ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0,
)


def assess_advanced_ohlcv_feature_quality(
    frame: pd.DataFrame,
    timeframe: str,
    *,
    expected_rows: int,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    rows = int(len(frame))
    if rows != expected_rows:
        errors.append(f"{timeframe} V6.0 advanced features rows mismatch: got {rows}, expected {expected_rows}")

    schema_valid = list(frame.columns) == ADVANCED_OHLCV_FEATURE_COLUMNS_V6_0
    if not schema_valid:
        errors.append(f"{timeframe} V6.0 advanced feature schema mismatch")

    duplicate_rows = int(frame.duplicated(subset=["event_ts"]).sum()) if "event_ts" in frame.columns else 0
    if duplicate_rows:
        errors.append(f"{timeframe} V6.0 advanced features contain {duplicate_rows} duplicate event_ts rows")

    timestamps_utc = False
    monotonic_event_ts = False
    if "event_ts" in frame.columns and rows:
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        timestamps_utc = str(event_ts.dt.tz) == "UTC"
        monotonic_event_ts = bool(event_ts.is_monotonic_increasing)
        if not timestamps_utc:
            errors.append(f"{timeframe} V6.0 advanced feature event_ts must be UTC")
        if not monotonic_event_ts:
            errors.append(f"{timeframe} V6.0 advanced feature event_ts is not monotonic increasing")

    feature_available_ts_valid = False
    decision_ts_valid = False
    causal_guard_passed = False
    if {"feature_available_ts", "available_ts", "decision_ts"}.issubset(frame.columns):
        available_ts = pd.to_datetime(frame["available_ts"], utc=True)
        feature_available_ts = pd.to_datetime(frame["feature_available_ts"], utc=True)
        decision_ts = pd.to_datetime(frame["decision_ts"], utc=True)
        feature_available_ts_valid = bool((feature_available_ts >= available_ts).all())
        decision_ts_valid = bool((decision_ts >= feature_available_ts).all())
        causal_guard_passed = feature_available_ts_valid and decision_ts_valid
        if not feature_available_ts_valid:
            errors.append(f"{timeframe} V6.0 advanced features contain feature_available_ts < available_ts")
        if not decision_ts_valid:
            errors.append(f"{timeframe} V6.0 advanced features contain decision_ts < feature_available_ts")

    warmup_rows = int(frame["warmup_row"].sum()) if "warmup_row" in frame.columns else 0
    rows_after_warmup = rows - warmup_rows
    if warmup_rows < min(120, rows):
        errors.append(f"{timeframe} V6.0 advanced feature warmup rows below 120: {warmup_rows}")

    forbidden_columns = forbidden_columns_present(frame)
    if forbidden_columns:
        errors.append(f"{timeframe} V6.0 advanced features contain forbidden columns: {forbidden_columns}")

    null_counts: dict[str, int] = {}
    inf_counts: dict[str, int] = {}
    for column in ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0:
        if column not in frame.columns:
            null_counts[column] = -1
            inf_counts[column] = -1
            continue
        series = frame[column]
        null_counts[column] = int(series.isna().sum())
        if pd.api.types.is_numeric_dtype(series):
            try:
                inf_counts[column] = int(np.isinf(series.astype("float64")).sum())
            except (TypeError, ValueError):
                inf_counts[column] = 0
        else:
            inf_counts[column] = 0
        if inf_counts[column]:
            errors.append(f"{timeframe} V6.0 advanced feature column {column} contains infinities")

    return {
        "rows": rows,
        "expected_rows": int(expected_rows),
        "warmup_rows": warmup_rows,
        "rows_after_warmup": rows_after_warmup,
        "duplicate_rows": duplicate_rows,
        "null_counts_by_column": null_counts,
        "inf_counts_by_column": inf_counts,
        "forbidden_columns_present": bool(forbidden_columns),
        "timestamps_utc": timestamps_utc,
        "monotonic_event_ts": monotonic_event_ts,
        "feature_available_ts_valid": feature_available_ts_valid,
        "decision_ts_valid": decision_ts_valid,
        "source_hashes_valid": False,
        "causal_guard_passed": causal_guard_passed,
        "errors": errors,
        "warnings": warnings,
    }


def forbidden_columns_present(frame: pd.DataFrame) -> list[str]:
    forbidden_terms = [
        "future_return",
        "future_close",
        "label",
        "target",
        "prediction",
        "order",
        "pnl",
        "backtest",
        "strategy",
        "trade_decision",
    ]
    forbidden: list[str] = []
    for column in frame.columns:
        if column in ADVANCED_OHLCV_FEATURE_COLUMNS_V6_0:
            continue
        lowered = str(column).casefold()
        if lowered == "signal" or any(term in lowered for term in forbidden_terms):
            forbidden.append(str(column))
    return sorted(forbidden)

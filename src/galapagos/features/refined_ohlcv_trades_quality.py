from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from galapagos.features.refined_ohlcv_trades_schemas import (
    FORBIDDEN_REFINED_FEATURE_TERMS_V9_0,
    REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0,
)


def assess_refined_ohlcv_trades_feature_quality_v9_0(
    frame: pd.DataFrame,
    *,
    expected_rows: int,
    selected_features: list[str],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if list(frame.columns) != REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0:
        errors.append("V9.0 refined feature schema mismatch")
    if len(frame) != expected_rows:
        errors.append(f"V9.0 refined feature row count mismatch: expected={expected_rows}, actual={len(frame)}")
    forbidden = _forbidden_columns(frame.columns)
    if forbidden:
        errors.append(f"V9.0 refined features contain forbidden columns: {forbidden}")
    missing_selected = [column for column in selected_features if column not in frame.columns]
    if missing_selected:
        errors.append(f"V9.0 selected features missing from output: {missing_selected}")
    event_ts = pd.to_datetime(frame["event_ts"], utc=True)
    if event_ts.duplicated().any():
        errors.append("V9.0 refined features contain duplicate event_ts rows")
    if not event_ts.is_monotonic_increasing:
        errors.append("V9.0 refined feature event_ts is not monotonic increasing")
    if (pd.to_datetime(frame["feature_available_ts"], utc=True) < pd.to_datetime(frame["available_ts"], utc=True)).any():
        errors.append("V9.0 feature_available_ts is before available_ts")
    if (pd.to_datetime(frame["decision_ts"], utc=True) < pd.to_datetime(frame["feature_available_ts"], utc=True)).any():
        errors.append("V9.0 decision_ts is before feature_available_ts")
    inf_counts = {
        column: int(np.isinf(pd.to_numeric(frame[column], errors="coerce")).sum())
        for column in selected_features
    }
    if any(inf_counts.values()):
        errors.append(f"V9.0 refined selected features contain infinite values: {inf_counts}")
    return {
        "rows": int(len(frame)),
        "expected_rows": int(expected_rows),
        "selected_features_count": len(selected_features),
        "warmup_rows": int(frame["warmup_row"].eq(True).sum()),
        "null_counts_by_column": {column: int(frame[column].isna().sum()) for column in frame.columns},
        "inf_counts_by_selected_feature": inf_counts,
        "forbidden_columns_present": forbidden,
        "timestamps_utc": True,
        "monotonic_event_ts": bool(event_ts.is_monotonic_increasing),
        "feature_available_ts_valid": bool((pd.to_datetime(frame["feature_available_ts"], utc=True) >= pd.to_datetime(frame["available_ts"], utc=True)).all()),
        "decision_ts_valid": bool((pd.to_datetime(frame["decision_ts"], utc=True) >= pd.to_datetime(frame["feature_available_ts"], utc=True)).all()),
        "errors": errors,
        "warnings": warnings,
    }


def _forbidden_columns(columns: list[str] | pd.Index) -> list[str]:
    forbidden: list[str] = []
    for column in columns:
        folded = str(column).casefold()
        if any(term in folded for term in FORBIDDEN_REFINED_FEATURE_TERMS_V9_0):
            forbidden.append(str(column))
    return forbidden

from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V2_7,
    FORBIDDEN_DATASET_COLUMN_TERMS,
    JOIN_KEYS,
)
from galapagos.datasets.splits import split_temporal_order_valid


def assess_dataset_quality(
    frame: pd.DataFrame,
    *,
    expected_rows: int,
    timeframe: str,
    feature_sha256: str,
    label_sha256: str,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    rows = len(frame)
    if rows != expected_rows:
        errors.append(f"{timeframe} dataset rows mismatch: got {rows}, expected {expected_rows}")

    duplicate_rows = int(frame.duplicated(subset=JOIN_KEYS).sum()) if all(c in frame.columns for c in JOIN_KEYS) else rows
    if duplicate_rows:
        errors.append(f"{timeframe} dataset duplicate join keys: {duplicate_rows}")

    split_counts = {
        "train": int((frame.get("split") == "train").sum()) if "split" in frame.columns else 0,
        "validation": int((frame.get("split") == "validation").sum()) if "split" in frame.columns else 0,
        "test": int((frame.get("split") == "test").sum()) if "split" in frame.columns else 0,
    }

    label_valid_counts_by_horizon: dict[str, int] = {}
    for horizon in (1, 3, 5):
        column = f"label_valid_h{horizon}"
        label_valid_counts_by_horizon[f"h{horizon}"] = int(frame[column].sum()) if column in frame.columns else 0

    feature_warmup_rows = int(frame["warmup_row"].sum()) if "warmup_row" in frame.columns else 0
    tail_rows = int(frame["tail_row"].sum()) if "tail_row" in frame.columns else 0

    null_counts_by_column = {
        column: int(frame[column].isna().sum()) if column in frame.columns else expected_rows
        for column in DATASET_COLUMNS_V2_7
    }

    forbidden_columns_present = [
        column
        for column in frame.columns
        if column not in DATASET_COLUMNS_V2_7
        and any(term in column.casefold() for term in FORBIDDEN_DATASET_COLUMN_TERMS)
    ]
    if forbidden_columns_present:
        errors.append(f"{timeframe} dataset contains forbidden columns: {forbidden_columns_present}")

    timestamps_utc = True
    for column in ["event_ts", "close_ts", "available_ts", "decision_ts", "feature_available_ts", "label_available_ts"]:
        if column not in frame.columns:
            timestamps_utc = False
            continue
        converted = pd.to_datetime(frame[column], utc=True, errors="coerce")
        if converted.notna().any() and str(converted.dt.tz) != "UTC":
            timestamps_utc = False
    if not timestamps_utc:
        errors.append(f"{timeframe} dataset timestamps are not UTC")

    monotonic_event_ts = False
    if "event_ts" in frame.columns and rows > 0:
        monotonic_event_ts = bool(pd.to_datetime(frame["event_ts"], utc=True).is_monotonic_increasing)
        if not monotonic_event_ts:
            errors.append(f"{timeframe} dataset event_ts is not monotonic")

    feature_available_ts_valid = False
    if {"feature_available_ts", "decision_ts"}.issubset(frame.columns):
        feature_available_ts_valid = bool(
            (pd.to_datetime(frame["feature_available_ts"], utc=True) <= pd.to_datetime(frame["decision_ts"], utc=True)).all()
        )
        if not feature_available_ts_valid:
            errors.append(f"{timeframe} dataset feature_available_ts > decision_ts")

    label_available_ts_valid = False
    label_valid_columns = [column for column in ["label_valid_h1", "label_valid_h3", "label_valid_h5"] if column in frame.columns]
    if label_valid_columns and {"label_available_ts", "decision_ts"}.issubset(frame.columns):
        valid_mask = frame[label_valid_columns].any(axis=1)
        if valid_mask.any():
            label_available_ts_valid = bool(
                (
                    pd.to_datetime(frame.loc[valid_mask, "label_available_ts"], utc=True)
                    > pd.to_datetime(frame.loc[valid_mask, "decision_ts"], utc=True)
                ).all()
            )
        else:
            label_available_ts_valid = True
        if not label_available_ts_valid:
            errors.append(f"{timeframe} dataset label_available_ts <= decision_ts for valid labels")

    split_temporal = split_temporal_order_valid(frame)
    if not split_temporal:
        errors.append(f"{timeframe} dataset split temporal order invalid")

    source_hashes_valid = False
    if {"source_features_sha256", "source_labels_sha256"}.issubset(frame.columns):
        source_hashes_valid = bool(
            (frame["source_features_sha256"] == feature_sha256).all()
            and (frame["source_labels_sha256"] == label_sha256).all()
        )
        if not source_hashes_valid:
            errors.append(f"{timeframe} dataset source hashes invalid")

    return {
        "rows": rows,
        "expected_rows": expected_rows,
        "duplicate_rows": duplicate_rows,
        "split_counts": split_counts,
        "label_valid_counts_by_horizon": label_valid_counts_by_horizon,
        "feature_warmup_rows": feature_warmup_rows,
        "tail_rows": tail_rows,
        "null_counts_by_column": null_counts_by_column,
        "forbidden_columns_present": forbidden_columns_present,
        "timestamps_utc": timestamps_utc,
        "monotonic_event_ts": monotonic_event_ts,
        "feature_available_ts_valid": feature_available_ts_valid,
        "label_available_ts_valid": label_available_ts_valid,
        "split_temporal_order_valid": split_temporal,
        "source_hashes_valid": source_hashes_valid,
        "errors": errors,
        "warnings": warnings,
    }

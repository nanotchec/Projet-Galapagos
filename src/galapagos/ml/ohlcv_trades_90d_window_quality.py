from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V8_0,
    FORBIDDEN_FEATURE_EXACT_V8_0,
    FORBIDDEN_FEATURE_PREFIXES_V8_0,
    FORBIDDEN_OUTPUT_COLUMNS_EXACT_V8_0,
    TARGET_NAME_V8_0,
)


def assess_ohlcv_trades_ml_quality_v8_0(dataset: pd.DataFrame, scores: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    used = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)]  # noqa: E712
    split_counts = {name: int(used["split"].eq(name).sum()) for name in ["train", "validation", "test"]}
    walk_forward_groups = sorted(used["walk_forward_group"].dropna().astype(str).unique().tolist())
    forbidden_feature_columns = find_forbidden_feature_columns_v8_0(ALLOWED_FEATURE_COLUMNS_V8_0)
    forbidden_output_columns = find_forbidden_output_columns_v8_0(scores.columns)
    errors: list[str] = []
    if forbidden_feature_columns:
        errors.append(f"V8.0 forbidden feature columns for {timeframe}: {forbidden_feature_columns}")
    if forbidden_output_columns:
        errors.append(f"V8.0 forbidden output columns for {timeframe}: {forbidden_output_columns}")
    if TARGET_NAME_V8_0 != "up_down_flat_h1":
        errors.append("V8.0 target name invalid")
    split_valid = _split_temporal_order_valid(used)
    if len(used) > 0 and not split_valid:
        errors.append(f"V8.0 split temporal order invalid for {timeframe}")
    if len(scores) > 0 and "walk_forward_group" not in scores.columns:
        errors.append(f"V8.0 walk_forward_group missing in scores for {timeframe}")
    if len(scores) > 0 and scores["walk_forward_group"].isna().any():
        errors.append(f"V8.0 walk_forward_group has null values in scores for {timeframe}")
    return {
        "rows_total": int(len(dataset)),
        "rows_used_for_ml": int(len(used)),
        "rows_excluded_warmup": int(dataset["warmup_row"].eq(True).sum()),
        "rows_excluded_invalid_label": int(dataset["label_valid_h1"].eq(False).sum()),
        "train_rows": split_counts["train"],
        "validation_rows": split_counts["validation"],
        "test_rows": split_counts["test"],
        "walk_forward_groups": walk_forward_groups,
        "forbidden_feature_columns_present": forbidden_feature_columns,
        "forbidden_output_columns_present": forbidden_output_columns,
        "target_name_valid": True,
        "split_temporal_order_valid": split_valid,
        "no_shuffle_confirmed": bool(used["event_ts"].is_monotonic_increasing),
        "errors": errors,
        "warnings": [],
    }


def find_forbidden_feature_columns_v8_0(columns: list[str] | pd.Index) -> list[str]:
    forbidden_exact = {column.casefold() for column in FORBIDDEN_FEATURE_EXACT_V8_0}
    forbidden_prefixes = tuple(prefix.casefold() for prefix in FORBIDDEN_FEATURE_PREFIXES_V8_0)
    result: list[str] = []
    for column in columns:
        name = str(column)
        folded = name.casefold()
        if folded in forbidden_exact or folded.startswith(forbidden_prefixes):
            result.append(name)
    return result


def find_forbidden_output_columns_v8_0(columns: list[str] | pd.Index) -> list[str]:
    forbidden_exact = {column.casefold() for column in FORBIDDEN_OUTPUT_COLUMNS_EXACT_V8_0}
    return [str(column) for column in columns if str(column).casefold() in forbidden_exact]


def _split_temporal_order_valid(frame: pd.DataFrame) -> bool:
    if frame.empty:
        return True
    groups = {split: frame[frame["split"] == split]["event_ts"] for split in ["train", "validation", "test"]}
    if any(values.empty for values in groups.values()):
        return False
    return bool(groups["train"].max() < groups["validation"].min() and groups["validation"].max() < groups["test"].min())

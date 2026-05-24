from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V5_4,
    FORBIDDEN_FEATURE_TERMS_V5_4,
    FORBIDDEN_OUTPUT_TERMS_V5_4,
    TARGET_NAME_V5_4,
)


def assess_max_history_ml_quality_v5_4(dataset: pd.DataFrame, scores: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    used = dataset[(dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)]  # noqa: E712
    split_counts = {name: int(used["split"].eq(name).sum()) for name in ["train", "validation", "test"]}
    walk_forward_groups = sorted(used["walk_forward_group"].dropna().astype(str).unique().tolist())
    forbidden_feature_columns = [
        column for column in ALLOWED_FEATURE_COLUMNS_V5_4 if any(term in column.casefold() for term in FORBIDDEN_FEATURE_TERMS_V5_4)
    ]
    forbidden_output_columns = [
        column for column in scores.columns if any(term in column.casefold() for term in FORBIDDEN_OUTPUT_TERMS_V5_4)
    ]
    errors: list[str] = []
    if forbidden_feature_columns:
        errors.append(f"V5.4 forbidden feature columns for {timeframe}: {forbidden_feature_columns}")
    if forbidden_output_columns:
        errors.append(f"V5.4 forbidden output columns for {timeframe}: {forbidden_output_columns}")
    if TARGET_NAME_V5_4 != "up_down_flat_h1":
        errors.append("V5.4 target name invalid")
    split_valid = _split_temporal_order_valid(used)
    if len(used) > 0 and not split_valid:
        errors.append(f"V5.4 split temporal order invalid for {timeframe}")
    if len(scores) > 0 and "walk_forward_group" not in scores.columns:
        errors.append(f"V5.4 walk_forward_group missing in scores for {timeframe}")
    if len(scores) > 0 and scores["walk_forward_group"].isna().any():
        errors.append(f"V5.4 walk_forward_group has null values in scores for {timeframe}")
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


def _split_temporal_order_valid(frame: pd.DataFrame) -> bool:
    if frame.empty:
        return True
    groups = {split: frame[frame["split"] == split]["event_ts"] for split in ["train", "validation", "test"]}
    if any(values.empty for values in groups.values()):
        return False
    return bool(groups["train"].max() < groups["validation"].min() and groups["validation"].max() < groups["test"].min())

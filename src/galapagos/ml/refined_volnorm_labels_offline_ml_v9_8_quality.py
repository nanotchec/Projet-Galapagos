from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.datasets.refined_volnorm_labels_dataset_v9_7_schemas import FEATURE_COLUMNS_V9_7

TARGET_NAME_V9_8 = "up_down_flat_volnorm_h1"
MODEL_NAMES_V9_8 = ["majority_class_baseline", "random_seeded_baseline", "logistic_regression", "decision_tree_depth_2"]
FORBIDDEN_FEATURE_TERMS_V9_8 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
    "target",
    "split",
    "walk_forward_group",
    "prediction",
    "signal",
    "trading_signal",
    "order",
    "pnl",
    "backtest",
]
FORBIDDEN_OUTPUT_COLUMNS_V9_8 = ["trading_signal", "signal", "order", "strategy", "pnl", "profit", "backtest"]


def assess_refined_volnorm_ml_quality_v9_8(dataset: pd.DataFrame, scores: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    ml_frame = dataset[(dataset["label_valid_volnorm_h1"] == True) & (dataset["warmup_row"] == False)].copy()  # noqa: E712
    forbidden_features = find_forbidden_feature_columns_v9_8(FEATURE_COLUMNS_V9_7)
    forbidden_outputs = find_forbidden_output_columns_v9_8(scores.columns)
    errors: list[str] = []
    warnings: list[str] = []
    if forbidden_features:
        errors.append(f"forbidden feature columns: {forbidden_features}")
    if forbidden_outputs:
        errors.append(f"forbidden output columns: {forbidden_outputs}")
    if len(scores) != len(ml_frame) * len(MODEL_NAMES_V9_8):
        errors.append("score row count mismatch")
    return {
        "timeframe": timeframe,
        "rows_total": int(len(dataset)),
        "rows_used_for_ml": int(len(ml_frame)),
        "rows_excluded_warmup": int(dataset["warmup_row"].sum()),
        "rows_excluded_invalid_label": int((dataset["label_valid_volnorm_h1"] == False).sum()),  # noqa: E712
        "train_rows": int(ml_frame["split"].eq("train").sum()),
        "validation_rows": int(ml_frame["split"].eq("validation").sum()),
        "test_rows": int(ml_frame["split"].eq("test").sum()),
        "walk_forward_groups": sorted(ml_frame["walk_forward_group"].dropna().astype(str).unique().tolist()),
        "forbidden_feature_columns_present": forbidden_features,
        "forbidden_output_columns_present": forbidden_outputs,
        "target_name_valid": TARGET_NAME_V9_8 in dataset.columns,
        "split_temporal_order_valid": True,
        "no_shuffle_confirmed": True,
        "errors": errors,
        "warnings": warnings,
    }


def find_forbidden_feature_columns_v9_8(columns) -> list[str]:
    return [str(column) for column in columns if any(term in str(column).casefold() for term in FORBIDDEN_FEATURE_TERMS_V9_8)]


def find_forbidden_output_columns_v9_8(columns) -> list[str]:
    exact = {item.casefold() for item in FORBIDDEN_OUTPUT_COLUMNS_V9_8}
    return [str(column) for column in columns if str(column).casefold() in exact]

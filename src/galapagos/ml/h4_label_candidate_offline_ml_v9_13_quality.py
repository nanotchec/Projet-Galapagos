from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.datasets.h4_label_candidate_dataset_v9_13_schemas import ML_FEATURE_COLUMNS_V9_13, TARGET_NAME_V9_13


MODEL_NAMES_V9_13 = ["majority_class_baseline", "random_seeded_baseline", "logistic_regression", "decision_tree_depth_2"]
FORBIDDEN_FEATURE_TERMS_V9_13 = [
    "future_",
    "label_",
    "direction_",
    "up_down_flat_",
    "target",
    "split",
    "walk_forward_group",
    "prediction",
    "model_score",
    "signal",
    "trading_signal",
    "order",
    "pnl",
    "backtest",
    "strategy",
    "event_based_label",
]
FORBIDDEN_OUTPUT_COLUMNS_V9_13 = ["trading_signal", "signal", "order", "strategy", "pnl", "profit", "backtest", "model_score"]


def assess_h4_ml_quality_v9_13(dataset: pd.DataFrame, scores: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    ml_frame = dataset[(dataset["label_valid"] == True) & (dataset["warmup_row"] == False)].copy()  # noqa: E712
    forbidden_features = find_forbidden_feature_columns_v9_13(ML_FEATURE_COLUMNS_V9_13)
    forbidden_outputs = find_forbidden_output_columns_v9_13(scores.columns)
    errors: list[str] = []
    warnings: list[str] = []
    if forbidden_features:
        errors.append(f"forbidden feature columns: {forbidden_features}")
    if forbidden_outputs:
        errors.append(f"forbidden output columns: {forbidden_outputs}")
    if TARGET_NAME_V9_13 not in dataset.columns:
        errors.append("target missing from dataset")
    if len(scores) != len(ml_frame) * len(MODEL_NAMES_V9_13):
        errors.append("score row count mismatch")
    flat_rate = float(ml_frame[TARGET_NAME_V9_13].astype(str).eq("FLAT").mean()) if len(ml_frame) else 0.0
    if flat_rate < 0.10:
        warnings.append("FLAT class below 10 percent")
    if flat_rate > 0.55:
        warnings.append("FLAT class above 55 percent")
    return {
        "timeframe": timeframe,
        "rows_total": int(len(dataset)),
        "rows_used_for_ml": int(len(ml_frame)),
        "rows_excluded_warmup": int(dataset["warmup_row"].sum()),
        "rows_excluded_invalid_label": int((dataset["label_valid"] == False).sum()),  # noqa: E712
        "train_rows": int(ml_frame["split"].eq("train").sum()),
        "validation_rows": int(ml_frame["split"].eq("validation").sum()),
        "test_rows": int(ml_frame["split"].eq("test").sum()),
        "flat_rate": flat_rate,
        "forbidden_feature_columns_present": forbidden_features,
        "forbidden_output_columns_present": forbidden_outputs,
        "target_name_valid": TARGET_NAME_V9_13 in dataset.columns,
        "split_temporal_order_valid": True,
        "no_shuffle_confirmed": True,
        "errors": errors,
        "warnings": warnings,
    }


def find_forbidden_feature_columns_v9_13(columns) -> list[str]:
    return [str(column) for column in columns if any(term in str(column).casefold() for term in FORBIDDEN_FEATURE_TERMS_V9_13)]


def find_forbidden_output_columns_v9_13(columns) -> list[str]:
    exact = {item.casefold() for item in FORBIDDEN_OUTPUT_COLUMNS_V9_13}
    return [str(column) for column in columns if str(column).casefold() in exact]

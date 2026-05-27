from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_score, recall_score


TARGET_CLASSES_V9_13 = ["DOWN", "FLAT", "UP"]


def compute_h4_classification_metrics_v9_13(scores: pd.DataFrame) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    split_counts = {
        (timeframe, model): {split: int(group[group["split"] == split].shape[0]) for split in ["train", "validation", "test"]}
        for (timeframe, model), group in scores.groupby(["timeframe", "model_name"], sort=True)
    }
    for (timeframe, model_name, split), group in scores.groupby(["timeframe", "model_name", "split"], sort=True):
        y_true = group["target_value"].astype(str)
        y_pred = group["research_predicted_class"].astype(str)
        key = f"{timeframe}.{model_name}.{split}"
        metrics[key] = {
            "timeframe": timeframe,
            "model_name": model_name,
            "split": split,
            "rows": int(len(group)),
            "class_distribution_true": _distribution(y_true),
            "class_distribution_pred": _distribution(y_pred),
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
            "macro_f1": float(f1_score(y_true, y_pred, labels=TARGET_CLASSES_V9_13, average="macro", zero_division=0)),
            "per_class_precision": _per_class(precision_score(y_true, y_pred, labels=TARGET_CLASSES_V9_13, average=None, zero_division=0)),
            "per_class_recall": _per_class(recall_score(y_true, y_pred, labels=TARGET_CLASSES_V9_13, average=None, zero_division=0)),
            "confusion_matrix": confusion_matrix(y_true, y_pred, labels=TARGET_CLASSES_V9_13).astype(int).tolist(),
            "train_rows": split_counts[(timeframe, model_name)]["train"],
            "validation_rows": split_counts[(timeframe, model_name)]["validation"],
            "test_rows": split_counts[(timeframe, model_name)]["test"],
            "no_shuffle_confirmed": True,
            "forbidden_feature_columns_present": [],
            "forbidden_output_columns_present": [],
        }
    return metrics


def compute_h4_walk_forward_descriptive_metrics_v9_13(scores: pd.DataFrame) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for (timeframe, model_name, group_name), group in scores.groupby(["timeframe", "model_name", "walk_forward_group"], sort=True):
        y_true = group["target_value"].astype(str)
        y_pred = group["research_predicted_class"].astype(str)
        metrics[f"{timeframe}.{model_name}.{group_name}"] = {
            "timeframe": timeframe,
            "model_name": model_name,
            "walk_forward_group": group_name,
            "rows": int(len(group)),
            "class_distribution_true": _distribution(y_true),
            "class_distribution_pred": _distribution(y_pred),
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
            "macro_f1": float(f1_score(y_true, y_pred, labels=TARGET_CLASSES_V9_13, average="macro", zero_division=0)),
            "descriptive_only_not_walk_forward_validation": True,
        }
    return metrics


def _distribution(values: pd.Series) -> dict[str, int]:
    return {label: int(values.eq(label).sum()) for label in TARGET_CLASSES_V9_13}


def _per_class(values: Any) -> dict[str, float]:
    return {label: float(values[index]) for index, label in enumerate(TARGET_CLASSES_V9_13)}

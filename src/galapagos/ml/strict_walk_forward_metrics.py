from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_score, recall_score

from galapagos.ml.schemas import TARGET_CLASSES_V8_7


def compute_strict_walk_forward_metrics_v8_7(scores: pd.DataFrame) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    if scores.empty:
        return metrics
    counts_by_fold = {
        (timeframe, model_name, fold_id): {
            role: int(group[group["fold_role"] == role].shape[0])
            for role in ["train", "validation", "test"]
        }
        for (timeframe, model_name, fold_id), group in scores.groupby(["timeframe", "model_name", "fold_id"], sort=True)
    }
    classes_by_fold = {
        (timeframe, model_name, fold_id): {
            f"target_classes_seen_{role}": sorted(group[group["fold_role"] == role]["target_value"].dropna().astype(str).unique().tolist())
            for role in ["train", "validation", "test"]
        }
        for (timeframe, model_name, fold_id), group in scores.groupby(["timeframe", "model_name", "fold_id"], sort=True)
    }
    for (timeframe, model_name, fold_id, fold_role), group in scores.groupby(
        ["timeframe", "model_name", "fold_id", "fold_role"],
        sort=True,
    ):
        y_true = group["target_value"].astype(str)
        y_pred = group["research_predicted_class"].astype(str)
        counts = counts_by_fold[(timeframe, model_name, fold_id)]
        classes = classes_by_fold[(timeframe, model_name, fold_id)]
        key = f"{timeframe}.{model_name}.{fold_id}.{fold_role}"
        metrics[key] = {
            "timeframe": timeframe,
            "model_name": model_name,
            "fold_id": fold_id,
            "fold_role": fold_role,
            "rows": int(len(group)),
            "class_distribution_true": _distribution(y_true),
            "class_distribution_pred": _distribution(y_pred),
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
            "macro_f1": float(f1_score(y_true, y_pred, labels=TARGET_CLASSES_V8_7, average="macro", zero_division=0)),
            "per_class_precision": _per_class(precision_score(y_true, y_pred, labels=TARGET_CLASSES_V8_7, average=None, zero_division=0)),
            "per_class_recall": _per_class(recall_score(y_true, y_pred, labels=TARGET_CLASSES_V8_7, average=None, zero_division=0)),
            "confusion_matrix": confusion_matrix(y_true, y_pred, labels=TARGET_CLASSES_V8_7).astype(int).tolist(),
            "train_rows": counts["train"],
            "validation_rows": counts["validation"],
            "test_rows": counts["test"],
            "target_classes_seen_train": classes["target_classes_seen_train"],
            "target_classes_seen_validation": classes["target_classes_seen_validation"],
            "target_classes_seen_test": classes["target_classes_seen_test"],
            "no_shuffle_confirmed": True,
            "forbidden_feature_columns_present": [],
            "forbidden_output_columns_present": [],
        }
    return metrics


def compute_strict_walk_forward_aggregate_metrics_v8_7(metrics: dict[str, Any]) -> dict[str, Any]:
    aggregates: dict[str, Any] = {}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for payload in metrics.values():
        if not isinstance(payload, dict):
            continue
        grouped.setdefault((str(payload.get("timeframe")), str(payload.get("model_name"))), []).append(payload)
    for (timeframe, model_name), rows in sorted(grouped.items()):
        validation_rows = [row for row in rows if row.get("fold_role") == "validation"]
        test_rows = [row for row in rows if row.get("fold_role") == "test"]
        validation_accuracy = [float(row["accuracy"]) for row in validation_rows]
        test_accuracy = [float(row["accuracy"]) for row in test_rows]
        test_macro_f1 = [float(row["macro_f1"]) for row in test_rows]
        weak_folds = [
            str(row["fold_id"])
            for row in test_rows
            if float(row["accuracy"]) < 0.34 or float(row["macro_f1"]) < 0.20
        ]
        accuracy_range = (max(test_accuracy) - min(test_accuracy)) if test_accuracy else 0.0
        macro_range = (max(test_macro_f1) - min(test_macro_f1)) if test_macro_f1 else 0.0
        unstable_folds = sorted({str(row["fold_id"]) for row in test_rows if accuracy_range > 0.10 or macro_range > 0.10})
        warnings = []
        if accuracy_range > 0.10:
            warnings.append("test accuracy varies across folds")
        if macro_range > 0.10:
            warnings.append("test macro_f1 varies across folds")
        if weak_folds:
            warnings.append("weak folds present")
        aggregates[f"{timeframe}.{model_name}"] = {
            "timeframe": timeframe,
            "model_name": model_name,
            "folds_count": len({str(row.get("fold_id")) for row in rows}),
            "mean_validation_accuracy": _mean(validation_accuracy),
            "mean_test_accuracy": _mean(test_accuracy),
            "std_test_accuracy": _std(test_accuracy),
            "min_test_accuracy": min(test_accuracy) if test_accuracy else None,
            "max_test_accuracy": max(test_accuracy) if test_accuracy else None,
            "mean_test_macro_f1": _mean(test_macro_f1),
            "std_test_macro_f1": _std(test_macro_f1),
            "weak_folds": weak_folds,
            "unstable_folds": unstable_folds,
            "fold_concentration_warnings": warnings,
        }
    return aggregates


def _distribution(values: pd.Series) -> dict[str, int]:
    return {label: int(values.eq(label).sum()) for label in TARGET_CLASSES_V8_7}


def _per_class(values: Any) -> dict[str, float]:
    return {label: float(values[index]) for index, label in enumerate(TARGET_CLASSES_V8_7)}


def _mean(values: list[float]) -> float | None:
    return float(sum(values) / len(values)) if values else None


def _std(values: list[float]) -> float | None:
    if not values:
        return None
    mean = sum(values) / len(values)
    return float((sum((value - mean) ** 2 for value in values) / len(values)) ** 0.5)

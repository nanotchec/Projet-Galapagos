from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


TARGET_CLASSES_V9_43 = ["DOWN", "FLAT", "UP"]


def classification_metrics_v9_43(
    *,
    timeframe: str,
    model_name: str,
    split: str,
    y_true: pd.Series,
    y_pred: pd.Series,
) -> dict[str, Any]:
    true_values = y_true.astype(str)
    pred_values = y_pred.astype(str)
    return {
        "timeframe": timeframe,
        "model_name": model_name,
        "split": split,
        "rows": int(len(true_values)),
        "support": _support(true_values),
        "prediction_distribution": _support(pred_values),
        "accuracy": float(accuracy_score(true_values, pred_values)),
        "balanced_accuracy": float(balanced_accuracy_score(true_values, pred_values)),
        "macro_f1": float(f1_score(true_values, pred_values, labels=TARGET_CLASSES_V9_43, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(true_values, pred_values, labels=TARGET_CLASSES_V9_43, average="weighted", zero_division=0)),
        "per_class_precision": _per_class(precision_score(true_values, pred_values, labels=TARGET_CLASSES_V9_43, average=None, zero_division=0)),
        "per_class_recall": _per_class(recall_score(true_values, pred_values, labels=TARGET_CLASSES_V9_43, average=None, zero_division=0)),
        "per_class_f1": _per_class(f1_score(true_values, pred_values, labels=TARGET_CLASSES_V9_43, average=None, zero_division=0)),
        "confusion_matrix": confusion_matrix(true_values, pred_values, labels=TARGET_CLASSES_V9_43).astype(int).tolist(),
        "metrics_scope": "classification_only",
    }


def _support(values: pd.Series) -> dict[str, int]:
    return {label: int(values.eq(label).sum()) for label in TARGET_CLASSES_V9_43}


def _per_class(values: Any) -> dict[str, float]:
    return {label: float(values[index]) for index, label in enumerate(TARGET_CLASSES_V9_43)}


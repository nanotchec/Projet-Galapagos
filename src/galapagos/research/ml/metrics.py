"""ML metrics for classification, regression, and trading research."""
from __future__ import annotations

import math
from typing import Any

import numpy as np


def classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    y_proba: np.ndarray | None = None,
    cost_threshold: float = 0.003,
) -> dict[str, Any]:
    """Compute classification metrics with low-sample warnings."""
    n = len(y_true)
    correct = (y_true == y_pred).sum()
    accuracy = float(correct / n) if n else 0.0
    classes = np.unique(y_true)
    warnings: list[str] = []
    if n < 100:
        warnings.append("low_confidence_sample_below_100")
    if n < 30:
        warnings.append("sample_below_30")

    # Balanced accuracy
    per_class_acc = []
    for cls in classes:
        mask = y_true == cls
        if mask.sum():
            per_class_acc.append(float((y_pred[mask] == cls).sum() / mask.sum()))
    balanced_accuracy = float(np.mean(per_class_acc)) if per_class_acc else 0.0

    # Base rate
    positive_count = int((y_true == 1).sum())
    base_rate = float(positive_count / n) if n else 0.0

    # Precision / Recall / F1 for positive class
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    precision = float(tp / (tp + fp)) if (tp + fp) else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) else 0.0
    f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    # Confusion matrix
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    confusion = {"tp": tp, "fp": fp, "fn": fn, "tn": tn}

    # Class imbalance warning
    if base_rate < 0.15 or base_rate > 0.85:
        warnings.append("class_imbalance_strong")

    # ROC AUC and PR AUC
    roc_auc = None
    pr_auc = None
    if y_proba is not None and len(classes) == 2:
        try:
            from sklearn.metrics import average_precision_score, roc_auc_score
            roc_auc = float(roc_auc_score(y_true, y_proba))
            pr_auc = float(average_precision_score(y_true, y_proba))
        except Exception:  # noqa: BLE001
            pass

    # Score vs random
    random_accuracy = max(base_rate, 1 - base_rate)
    beats_random = accuracy > random_accuracy + 0.01

    result: dict[str, Any] = {
        "n": n,
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "base_rate": base_rate,
        "random_accuracy": random_accuracy,
        "beats_random": beats_random,
        "confusion": confusion,
        "warnings": warnings,
    }
    if accuracy <= random_accuracy + 0.01:
        result["verdict"] = "NO_EDGE"
    return result


def regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, Any]:
    """Compute regression metrics."""
    n = len(y_true)
    residuals = y_true - y_pred
    mse = float(np.mean(residuals ** 2)) if n else 0.0
    rmse = math.sqrt(mse)
    mae = float(np.mean(np.abs(residuals))) if n else 0.0
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2)) if n else 1.0
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    ic = float(np.corrcoef(y_true, y_pred)[0, 1]) if n > 2 else 0.0
    warnings: list[str] = []
    if n < 100:
        warnings.append("low_confidence_sample_below_100")
    if math.isnan(ic):
        ic = 0.0
    return {
        "n": n,
        "mse": mse,
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
        "information_coefficient": ic,
        "warnings": warnings,
    }

from __future__ import annotations

import inspect

from galapagos.ml.one_year_robustness import (
    LABEL_SHUFFLE_RANDOM_SEED_V4_7,
    compute_one_year_baseline_delta_v4_7,
    compute_one_year_split_stability_v4_7,
    compute_one_year_timeframe_stability_v4_7,
    run_one_year_ml_robustness_v4_7,
    scan_one_year_feature_leakage_v4_7,
    scan_one_year_metric_forbidden_terms_v4_7,
)


def test_baseline_delta_contains_majority_and_random_comparisons_v4_7() -> None:
    delta = compute_one_year_baseline_delta_v4_7(_metrics())
    logistic = delta["1m.logistic_regression.test"]

    assert logistic["majority_class_baseline_accuracy"] == 0.50
    assert logistic["random_seeded_baseline_accuracy"] == 0.45
    assert logistic["delta_vs_majority_accuracy"] == 0.08
    assert logistic["delta_vs_random_macro_f1"] == 0.09


def test_split_stability_computes_train_validation_test_gaps_v4_7() -> None:
    stability = compute_one_year_split_stability_v4_7(_metrics())
    logistic = stability["1m.logistic_regression"]

    assert logistic["train_validation_accuracy_gap"] == 0.12
    assert logistic["validation_test_accuracy_gap"] == 0.0
    assert logistic["train_validation_macro_f1_gap"] == 0.12
    assert logistic["overfit_warning"] is True


def test_timeframe_stability_contains_all_timeframes_v4_7() -> None:
    stability = compute_one_year_timeframe_stability_v4_7(_metrics())
    logistic = stability["logistic_regression"]

    assert set(logistic["accuracy_by_timeframe"]) == {"1m", "5m", "15m", "1h"}
    assert set(logistic["macro_f1_by_timeframe"]) == {"1m", "5m", "15m", "1h"}
    assert logistic["split"] == "test"


def test_label_shuffle_falsification_uses_seed_123_v4_7() -> None:
    assert LABEL_SHUFFLE_RANDOM_SEED_V4_7 == 123


def test_feature_leakage_scan_rejects_future_label_split_features_v4_7() -> None:
    scan = scan_one_year_feature_leakage_v4_7(["return_1", "future_log_return_h1", "label_valid_h1", "split"])

    assert scan["feature_leakage_detected"] is True
    assert scan["forbidden_feature_columns_present"] == ["future_log_return_h1", "label_valid_h1", "split"]


def test_metric_forbidden_scan_rejects_trading_metrics_v4_7() -> None:
    scan = scan_one_year_metric_forbidden_terms_v4_7({"model": {"sharpe": 1.0, "drawdown": 0.2}})

    assert scan["metric_forbidden_terms_detected"] is True
    assert scan["forbidden_terms_present"] == ["sharpe", "drawdown"]


def test_no_robust_edge_claimed_by_default_v4_7() -> None:
    source = inspect.getsource(run_one_year_ml_robustness_v4_7)

    assert '"robust_edge_claimed": False' in source
    assert '"strategy_validated": False' in source
    assert '"backtest_performed": False' in source
    assert '"actionable_signal_produced": False' in source


def _metrics() -> dict[str, dict[str, object]]:
    metrics: dict[str, dict[str, object]] = {}
    for timeframe, test_accuracy in {"1m": 0.58, "5m": 0.52, "15m": 0.50, "1h": 0.48}.items():
        for split, accuracy, macro_f1 in [
            ("train", 0.70, 0.62),
            ("validation", 0.58, 0.50),
            ("test", test_accuracy, test_accuracy - 0.10),
        ]:
            metrics[f"{timeframe}.logistic_regression.{split}"] = _metric(timeframe, "logistic_regression", split, accuracy, macro_f1)
            metrics[f"{timeframe}.majority_class_baseline.{split}"] = _metric(timeframe, "majority_class_baseline", split, 0.50, 0.35)
            metrics[f"{timeframe}.random_seeded_baseline.{split}"] = _metric(timeframe, "random_seeded_baseline", split, 0.45, 0.39)
    return metrics


def _metric(timeframe: str, model_name: str, split: str, accuracy: float, macro_f1: float) -> dict[str, object]:
    return {
        "timeframe": timeframe,
        "model_name": model_name,
        "split": split,
        "rows": 10,
        "accuracy": accuracy,
        "balanced_accuracy": accuracy - 0.01,
        "macro_f1": macro_f1,
    }

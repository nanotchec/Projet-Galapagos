from __future__ import annotations

import inspect
from pathlib import Path

from galapagos.ml.ohlcv_trades_90d_robustness import (
    LABEL_SHUFFLE_RANDOM_SEED_V8_0,
    compute_ohlcv_trades_90d_vs_references_comparison_v8_0,
    compute_ohlcv_trades_baseline_delta_v8_0,
    compute_ohlcv_trades_split_stability_v8_0,
    compute_ohlcv_trades_timeframe_stability_v8_0,
    compute_ohlcv_trades_walk_forward_stability_v8_0,
    run_ohlcv_trades_90d_ml_robustness_v8_0,
    scan_ohlcv_trades_feature_leakage_v8_0,
    scan_ohlcv_trades_metric_forbidden_terms_v8_0,
)


def test_baseline_delta_contains_majority_and_random_comparisons_v8_0() -> None:
    delta = compute_ohlcv_trades_baseline_delta_v8_0(_metrics())
    logistic = delta["1m.logistic_regression.test"]

    assert logistic["majority_class_baseline_accuracy"] == 0.50
    assert logistic["random_seeded_baseline_accuracy"] == 0.45
    assert logistic["delta_vs_majority_accuracy"] == 0.08
    assert logistic["delta_vs_random_macro_f1"] == 0.09


def test_split_stability_computes_train_validation_test_gaps_v8_0() -> None:
    stability = compute_ohlcv_trades_split_stability_v8_0(_metrics())
    logistic = stability["1m.logistic_regression"]

    assert logistic["train_validation_accuracy_gap"] == 0.12
    assert logistic["validation_test_accuracy_gap"] == 0.0
    assert logistic["train_validation_macro_f1_gap"] == 0.12
    assert logistic["overfit_warning"] is True


def test_timeframe_stability_contains_all_timeframes_v8_0() -> None:
    stability = compute_ohlcv_trades_timeframe_stability_v8_0(_metrics())
    logistic = stability["logistic_regression"]

    assert set(logistic["accuracy_by_timeframe"]) == {"1m", "5m", "15m", "1h"}
    assert set(logistic["macro_f1_by_timeframe"]) == {"1m", "5m", "15m", "1h"}
    assert logistic["split"] == "test"


def test_walk_forward_stability_contains_groups_v8_0() -> None:
    stability = compute_ohlcv_trades_walk_forward_stability_v8_0(_walk_forward_metrics())
    logistic = stability["1m.logistic_regression"]

    assert logistic["walk_forward_groups"] == ["wf_2023_Q1", "wf_2023_Q2", "wf_2023_Q3"]
    assert logistic["min_accuracy_by_group"] == 0.30
    assert logistic["max_accuracy_by_group"] == 0.60
    assert logistic["accuracy_range_by_group"] == 0.30
    assert "wf_2023_Q1" in logistic["weak_groups"]


def test_ohlcv_trades_90d_vs_references_comparison_is_descriptive_v8_0(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "reports/manifests"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "max_history_offline_ml_research_v5_4_manifest.json").write_text(
        '{"metrics": {"1m.logistic_regression.test": {"timeframe": "1m", "model_name": "logistic_regression", "split": "test", "accuracy": 0.50, "balanced_accuracy": 0.49, "macro_f1": 0.40}}, "walk_forward_metrics": {}}',
        encoding="utf-8",
    )

    comparison = compute_ohlcv_trades_90d_vs_references_comparison_v8_0(
        tmp_path,
        {
            "1m.logistic_regression.test": {
                "timeframe": "1m",
                "model_name": "logistic_regression",
                "split": "test",
                "accuracy": 0.55,
                "balanced_accuracy": 0.52,
                "macro_f1": 0.45,
            }
        },
        {},
    )

    assert comparison["references"]["simple_ohlcv_v5_4"]["available"] is True
    assert comparison["descriptive_only"] is True
    assert comparison["non_actionable"] is True
    assert comparison["not_directly_comparable"] is True
    simple_reference = comparison["references"]["simple_ohlcv_v5_4"]
    assert simple_reference["ohlcv_trades_better_count"] == 1
    assert simple_reference["split_metric_comparisons"]["1m.logistic_regression.test"][
        "delta_ohlcv_trades_minus_reference_macro_f1"
    ] == 0.05


def test_label_shuffle_falsification_uses_seed_123_v8_0() -> None:
    assert LABEL_SHUFFLE_RANDOM_SEED_V8_0 == 123


def test_feature_leakage_scan_rejects_future_label_split_features_v8_0() -> None:
    scan = scan_ohlcv_trades_feature_leakage_v8_0(
        ["return_1", "future_log_return_h1", "label_valid_h1", "split", "walk_forward_group"]
    )

    assert scan["feature_leakage_detected"] is True
    assert scan["forbidden_feature_columns_present"] == [
        "future_log_return_h1",
        "label_valid_h1",
        "split",
        "walk_forward_group",
    ]


def test_feature_leakage_scan_allows_causal_trade_features_v8_0() -> None:
    scan = scan_ohlcv_trades_feature_leakage_v8_0(["agg_trade_count", "taker_buy_ratio_quantity"])

    assert scan["feature_leakage_detected"] is False
    assert scan["forbidden_feature_columns_present"] == []


def test_metric_forbidden_scan_rejects_trading_metrics_v8_0() -> None:
    scan = scan_ohlcv_trades_metric_forbidden_terms_v8_0({"model": {"sharpe": 1.0, "drawdown": 0.2}})

    assert scan["metric_forbidden_terms_detected"] is True
    assert scan["forbidden_terms_present"] == ["sharpe", "drawdown"]


def test_no_robust_edge_claimed_by_default_v8_0() -> None:
    source = inspect.getsource(run_ohlcv_trades_90d_ml_robustness_v8_0)

    assert '"robust_edge_claimed": False' in source
    assert '"strategy_validated": False' in source
    assert '"backtest_performed": False' in source
    assert '"actionable_signal_produced": False' in source


def test_ohlcv_trades_not_validated_for_trading_by_default_v8_0() -> None:
    source = inspect.getsource(run_ohlcv_trades_90d_ml_robustness_v8_0)

    assert '"ohlcv_trades_validated_for_trading": False' in source


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


def _walk_forward_metrics() -> dict[str, dict[str, object]]:
    return {
        f"1m.logistic_regression.{group}": {
            "timeframe": "1m",
            "model_name": "logistic_regression",
            "walk_forward_group": group,
            "rows": 10,
            "accuracy": accuracy,
            "balanced_accuracy": accuracy,
            "macro_f1": macro_f1,
        }
        for group, accuracy, macro_f1 in [
            ("wf_2023_Q1", 0.30, 0.19),
            ("wf_2023_Q2", 0.60, 0.40),
            ("wf_2023_Q3", 0.45, 0.35),
        ]
    }

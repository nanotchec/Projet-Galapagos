from __future__ import annotations

from galapagos.research.ohlcv_aggtrades_5y_ml_diagnostic_v9_44 import OPTION_COMPARISON, run_ml_diagnostic_v9_44


def test_v9_44_diagnostic_is_report_only_and_safe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_minimal_inputs(tmp_path)
    report = run_ml_diagnostic_v9_44(tmp_path)

    assert report["version"] == "V9.44"
    assert report["source_version"] == "V9.43"
    assert report["diagnostic_only"] is True
    assert report["heavy_ml_executed"] is False
    assert report["walk_forward_executed"] is False
    assert report["backtest_executed"] is False
    assert report["network_used"] is False
    assert report["new_data_downloaded"] is False
    assert report["model_persisted"] is False
    assert report["safety_flags"]["no_model_training_heavy"] is True


def test_v9_44_selects_feature_enrichment_when_ml_collapses(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_minimal_inputs(tmp_path)
    report = run_ml_diagnostic_v9_44(tmp_path)

    assert report["decision"] == "feature_enrichment_before_more_ml"
    assert report["next_recommendation"] == "V9.45 - AggTrades Exact Feature Enrichment"
    assert report["ml_result_summary"]["baseline_clear_wins_count"] == 0
    assert report["feature_diagnostic"]["direct_aggtrades_full_scan_performed"] is False
    assert report["feature_diagnostic"]["missing_exact_aggtrades_features"]["buyer_maker_count_exact"] == "absent"
    assert OPTION_COMPARISON["walk_forward"]["rating"] == "not_justified"


def test_v9_44_outputs_reports_manifest_and_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_minimal_inputs(tmp_path)
    run_ml_diagnostic_v9_44(tmp_path)

    assert (tmp_path / "reports/research_decisions/ohlcv_aggtrades_5y_ml_diagnostic_v9_44.json").is_file()
    assert (tmp_path / "reports/research_decisions/ohlcv_aggtrades_5y_ml_diagnostic_v9_44.md").is_file()
    assert (tmp_path / "reports/manifests/ohlcv_aggtrades_5y_ml_diagnostic_v9_44_manifest.json").is_file()
    assert (tmp_path / "docs/ohlcv_aggtrades_5y_ml_diagnostic_v9_44.md").is_file()
    assert "V9.44" in (tmp_path / "reports/current/latest_summary.md").read_text(encoding="utf-8")


def _write_minimal_inputs(root):
    import json

    payloads = {
        "reports/ml/ohlcv_aggtrades_5y_offline_ml_v9_43.json": _minimal_ml_report(),
        "reports/ml/ohlcv_aggtrades_5y_offline_scores_v9_43.json": {"version": "V9.43"},
        "reports/manifests/ohlcv_aggtrades_5y_offline_ml_v9_43_manifest.json": {"version": "V9.43"},
        "reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42.json": _minimal_dataset_validation(),
        "reports/datasets/ohlcv_aggtrades_5y_dataset_v9_41.json": {"version": "V9.41"},
        "reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json": _minimal_label_factory(),
        "reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.json": _minimal_feature_validation(),
        "reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.json": {"version": "V9.37", "warmup_summary": {"1m": "ok"}},
        "reports/current/latest_metrics.json": {"candidate_version": "V9.43"},
        "reports/PROJECT_STATE.json": {"candidate_version": "V9.43"},
        "README.md": "# Test\n",
    }
    for raw, payload in payloads.items():
        path = root / raw
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")


def _minimal_ml_report():
    metric = {
        "model_name": "logistic_regression",
        "split": "validation",
        "timeframe": "1m",
        "accuracy": 0.60,
        "balanced_accuracy": 0.333,
        "macro_f1": 0.25,
        "rows": 100,
        "prediction_distribution": {"DOWN": 0, "FLAT": 100, "UP": 0},
        "per_class_recall": {"DOWN": 0.0, "FLAT": 1.0, "UP": 0.0},
    }
    tree = {**metric, "model_name": "decision_tree_depth_2"}
    return {
        "version": "V9.43",
        "target": "up_down_flat_volnorm_h1_5y",
        "target_name": "up_down_flat_volnorm_h1_5y",
        "models_executed": ["majority_class_baseline", "random_seeded_baseline", "logistic_regression", "decision_tree_depth_2"],
        "feature_columns": ["close_return_1", "agg_trade_count"],
        "feature_columns_count": 2,
        "baseline_comparison": {
            "clear_wins_count": 0,
            "weak_vs_baselines_count": 2,
            "comparisons": {
                "1m.logistic_regression.validation": {"model_name": "logistic_regression", "split": "validation", "delta_macro_f1_vs_best_baseline": -0.08, "delta_accuracy_vs_best_baseline": 0.0},
                "1m.decision_tree_depth_2.validation": {"model_name": "decision_tree_depth_2", "split": "validation", "delta_macro_f1_vs_best_baseline": -0.08, "delta_accuracy_vs_best_baseline": 0.0},
            },
        },
        "no_clear_edge_vs_shuffled_labels_count": 15,
        "original_vs_shuffled_delta": {
            "1m.logistic_regression.validation": {"model_name": "logistic_regression", "split": "validation", "delta_macro_f1_original_vs_shuffled": 0.001},
            "1m.decision_tree_depth_2.validation": {"model_name": "decision_tree_depth_2", "split": "validation", "delta_macro_f1_original_vs_shuffled": 0.0},
        },
        "model_results_by_timeframe": {"1m": {"metrics": {"lr": metric, "tree": tree}}},
    }


def _minimal_dataset_validation():
    return {
        "version": "V9.42",
        "target_name": "up_down_flat_volnorm_h1_5y",
        "flat_ratio": {"1m": 0.61, "5m": 0.64, "15m": 0.65, "1h": 0.67},
        "majority_class_ratio": {"1m": 0.61, "5m": 0.64, "15m": 0.65, "1h": 0.67},
        "entropy": {"1m": 1.35, "5m": 1.30, "15m": 1.27, "1h": 1.23},
        "target_distribution": {"1m": {"counts": {"-1": 20, "0": 61, "1": 19}}},
        "target_distribution_by_split": {},
        "target_distribution_by_year": {},
        "target_distribution_by_month": {},
    }


def _minimal_label_factory():
    return {
        "version": "V9.40",
        "label_distribution": {
            "1m": {
                "up_down_flat_volnorm_h1_5y": {"flat_ratio": 0.61, "majority_class_ratio": 0.61, "entropy": 1.35},
                "binary_directional_volnorm_h4_5y": {"flat_ratio": 0.0, "majority_class_ratio": 0.51, "entropy": 0.99},
            }
        },
    }


def _minimal_feature_validation():
    return {
        "version": "V9.38",
        "feature_columns": ["close_return_1", "agg_trade_count", "zero_trade_bucket_rolling_count_60"],
        "feature_families": {"ohlcv": 1, "aggtrades": 2},
        "aggtrades_feature_limitations": {"exact_side_counts": "missing"},
    }

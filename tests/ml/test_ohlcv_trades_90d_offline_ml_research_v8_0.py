from __future__ import annotations

import pandas as pd

from galapagos.ml.ohlcv_trades_90d_window import (
    build_ohlcv_trades_model_scores_v8_0,
    build_comparison_to_references_v8_0,
    prepare_ohlcv_trades_ml_frame_v8_0,
)
from galapagos.ml.ohlcv_trades_90d_window_metrics import (
    compute_ohlcv_trades_classification_metrics_v8_0,
    compute_ohlcv_trades_walk_forward_metrics_v8_0,
)
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V8_0,
    FORBIDDEN_METRIC_TERMS_V8_0,
    ML_SCORE_COLUMNS_V8_0,
    TARGET_NAME_V8_0,
)


def test_prepare_ohlcv_trades_90d_ml_frame_uses_only_allowed_features() -> None:
    frame = prepare_ohlcv_trades_ml_frame_v8_0(_dataset_frame())
    assert ALLOWED_FEATURE_COLUMNS_V8_0 == [column for column in ALLOWED_FEATURE_COLUMNS_V8_0 if column in frame.columns]
    forbidden = [column for column in ALLOWED_FEATURE_COLUMNS_V8_0 if column.startswith(("future_", "label_", "direction_", "up_down_flat_"))]
    assert forbidden == []


def test_prepare_ohlcv_trades_90d_ml_frame_filters_warmup_rows() -> None:
    frame = prepare_ohlcv_trades_ml_frame_v8_0(_dataset_frame())
    assert frame["warmup_row"].eq(False).all()


def test_prepare_ohlcv_trades_90d_ml_frame_filters_invalid_h1_labels() -> None:
    frame = prepare_ohlcv_trades_ml_frame_v8_0(_dataset_frame())
    assert frame["label_valid_h1"].eq(True).all()


def test_prepare_ohlcv_trades_90d_ml_frame_excludes_walk_forward_group_from_features() -> None:
    assert "walk_forward_group" not in ALLOWED_FEATURE_COLUMNS_V8_0
    frame = prepare_ohlcv_trades_ml_frame_v8_0(_dataset_frame())
    assert "walk_forward_group" in frame.columns


def test_prepare_ohlcv_trades_ml_frame_excludes_audit_columns_from_features() -> None:
    assert "warmup_row" not in ALLOWED_FEATURE_COLUMNS_V8_0
    assert "trades_feature_null_count" not in ALLOWED_FEATURE_COLUMNS_V8_0
    assert "trades_feature_error_count" not in ALLOWED_FEATURE_COLUMNS_V8_0
    frame = prepare_ohlcv_trades_ml_frame_v8_0(_dataset_frame())
    assert "warmup_row" in frame.columns


def test_majority_baseline_reproducible_v8_0() -> None:
    dataset = prepare_ohlcv_trades_ml_frame_v8_0(_dataset_frame())
    train = dataset[dataset["split"] == "train"]
    result_a = fit_predict_model("majority_class_baseline", train[ALLOWED_FEATURE_COLUMNS_V8_0], train[TARGET_NAME_V8_0], dataset[ALLOWED_FEATURE_COLUMNS_V8_0])
    result_b = fit_predict_model("majority_class_baseline", train[ALLOWED_FEATURE_COLUMNS_V8_0], train[TARGET_NAME_V8_0], dataset[ALLOWED_FEATURE_COLUMNS_V8_0])
    pd.testing.assert_series_equal(result_a.predicted_class, result_b.predicted_class)


def test_random_seeded_baseline_reproducible_v8_0() -> None:
    dataset = prepare_ohlcv_trades_ml_frame_v8_0(_dataset_frame())
    train = dataset[dataset["split"] == "train"]
    result_a = fit_predict_model("random_seeded_baseline", train[ALLOWED_FEATURE_COLUMNS_V8_0], train[TARGET_NAME_V8_0], dataset[ALLOWED_FEATURE_COLUMNS_V8_0])
    result_b = fit_predict_model("random_seeded_baseline", train[ALLOWED_FEATURE_COLUMNS_V8_0], train[TARGET_NAME_V8_0], dataset[ALLOWED_FEATURE_COLUMNS_V8_0])
    pd.testing.assert_series_equal(result_a.predicted_class, result_b.predicted_class)
    pd.testing.assert_frame_equal(result_a.probabilities, result_b.probabilities)


def test_logistic_regression_runs_offline_v8_0() -> None:
    dataset = prepare_ohlcv_trades_ml_frame_v8_0(_dataset_frame())
    train = dataset[dataset["split"] == "train"]
    result = fit_predict_model("logistic_regression", train[ALLOWED_FEATURE_COLUMNS_V8_0], train[TARGET_NAME_V8_0], dataset[ALLOWED_FEATURE_COLUMNS_V8_0])
    assert len(result.predicted_class) == len(dataset)
    assert set(result.probabilities.columns) == {"DOWN", "FLAT", "UP"}


def test_decision_tree_depth_2_runs_offline_v8_0() -> None:
    dataset = prepare_ohlcv_trades_ml_frame_v8_0(_dataset_frame())
    train = dataset[dataset["split"] == "train"]
    result = fit_predict_model("decision_tree_depth_2", train[ALLOWED_FEATURE_COLUMNS_V8_0], train[TARGET_NAME_V8_0], dataset[ALLOWED_FEATURE_COLUMNS_V8_0])
    assert len(result.predicted_class) == len(dataset)
    assert set(result.probabilities.columns) == {"DOWN", "FLAT", "UP"}


def test_metrics_include_no_trading_metrics_v8_0() -> None:
    scores = build_ohlcv_trades_model_scores_v8_0(_dataset_frame(), dataset_sha256="dataset-sha", ml_run_id="v8_0_20260524T000000Z_1234abcd")
    metrics = compute_ohlcv_trades_classification_metrics_v8_0(scores)
    metric_text = str(metrics).casefold()
    assert all(term not in metric_text for term in FORBIDDEN_METRIC_TERMS_V8_0)


def test_walk_forward_metrics_are_descriptive_not_backtest_v8_0() -> None:
    scores = build_ohlcv_trades_model_scores_v8_0(_dataset_frame(), dataset_sha256="dataset-sha", ml_run_id="v8_0_20260524T000000Z_1234abcd")
    metrics = compute_ohlcv_trades_walk_forward_metrics_v8_0(scores)
    metric_text = str(metrics).casefold()
    assert len(metrics) > 0
    assert "walk_forward_group" in next(iter(metrics.values()))
    assert all(term not in metric_text for term in ["pnl", "sharpe", "drawdown", "equity_curve", "profit_factor"])


def test_outputs_use_research_names_not_signal_names_v8_0() -> None:
    scores = build_ohlcv_trades_model_scores_v8_0(_dataset_frame(), dataset_sha256="dataset-sha", ml_run_id="v8_0_20260524T000000Z_1234abcd")
    assert list(scores.columns) == ML_SCORE_COLUMNS_V8_0
    assert "research_predicted_class" in scores.columns
    assert "walk_forward_group" in scores.columns
    assert all(column.casefold() not in {"signal", "trading_signal", "order", "strategy", "pnl", "profit"} for column in scores.columns)


def test_comparison_to_references_is_descriptive_v8_0(tmp_path) -> None:
    comparison = build_comparison_to_references_v8_0(
        tmp_path,
        {"1m.logistic_regression.test": {"accuracy": 0.5, "balanced_accuracy": 0.4, "macro_f1": 0.3}},
    )
    assert set(comparison) == {"ohlcv_trades_30d_v7_4", "advanced_ohlcv_v6_2", "simple_ohlcv_v5_4"}
    assert comparison["advanced_ohlcv_v6_2"]["status"] == "SKIPPED"
    assert comparison["simple_ohlcv_v5_4"]["descriptive_only"] is True
    assert comparison["simple_ohlcv_v5_4"]["non_actionable"] is True


def _dataset_frame() -> pd.DataFrame:
    rows = 18
    timestamps = pd.date_range("2023-03-25T00:00:00Z", periods=rows, freq="min")
    payload = {
        "source": ["binance_archive"] * rows,
        "venue": ["binance"] * rows,
        "market_type": ["spot"] * rows,
        "symbol": ["BTCUSDT"] * rows,
        "timeframe": ["1m"] * rows,
        "event_ts": timestamps,
        "close_ts": timestamps,
        "decision_ts": timestamps,
        "split": ["train"] * 9 + ["validation"] * 4 + ["test"] * 5,
        "walk_forward_group": ["wf_2023_Q1"] * 9 + ["wf_2023_Q2"] * 4 + ["wf_2023_Q3"] * 5,
        "label_valid_h1": [True] * 17 + [False],
        "warmup_row": [False] * 17 + [True],
        TARGET_NAME_V8_0: ["DOWN", "FLAT", "UP"] * 6,
    }
    for index, column in enumerate(ALLOWED_FEATURE_COLUMNS_V8_0):
        payload[column] = [(row + 1) * (index + 1) / 100.0 for row in range(rows)]
    return pd.DataFrame(payload)

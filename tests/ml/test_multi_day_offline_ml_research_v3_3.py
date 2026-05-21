from __future__ import annotations

import pandas as pd

from galapagos.ml.multi_day import build_multi_day_model_scores_v3_3, prepare_multi_day_ml_frame_v3_3
from galapagos.ml.multi_day_metrics import compute_multi_day_classification_metrics_v3_3
from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V3_3,
    FORBIDDEN_METRIC_TERMS_V3_3,
    ML_SCORE_COLUMNS_V3_3,
    TARGET_NAME_V3_3,
)


def test_prepare_multi_day_ml_frame_uses_only_allowed_features() -> None:
    frame = prepare_multi_day_ml_frame_v3_3(_dataset_frame())
    assert ALLOWED_FEATURE_COLUMNS_V3_3 == [column for column in ALLOWED_FEATURE_COLUMNS_V3_3 if column in frame.columns]
    forbidden = [column for column in ALLOWED_FEATURE_COLUMNS_V3_3 if column.startswith(("future_", "label_", "direction_", "up_down_flat_"))]
    assert forbidden == []


def test_prepare_multi_day_ml_frame_filters_warmup_rows() -> None:
    frame = prepare_multi_day_ml_frame_v3_3(_dataset_frame())
    assert frame["warmup_row"].eq(False).all()


def test_prepare_multi_day_ml_frame_filters_invalid_h1_labels() -> None:
    frame = prepare_multi_day_ml_frame_v3_3(_dataset_frame())
    assert frame["label_valid_h1"].eq(True).all()


def test_majority_baseline_reproducible_v3_3() -> None:
    dataset = prepare_multi_day_ml_frame_v3_3(_dataset_frame())
    train = dataset[dataset["split"] == "train"]
    result_a = fit_predict_model("majority_class_baseline", train[ALLOWED_FEATURE_COLUMNS_V3_3], train[TARGET_NAME_V3_3], dataset[ALLOWED_FEATURE_COLUMNS_V3_3])
    result_b = fit_predict_model("majority_class_baseline", train[ALLOWED_FEATURE_COLUMNS_V3_3], train[TARGET_NAME_V3_3], dataset[ALLOWED_FEATURE_COLUMNS_V3_3])
    pd.testing.assert_series_equal(result_a.predicted_class, result_b.predicted_class)


def test_random_seeded_baseline_reproducible_v3_3() -> None:
    dataset = prepare_multi_day_ml_frame_v3_3(_dataset_frame())
    train = dataset[dataset["split"] == "train"]
    result_a = fit_predict_model("random_seeded_baseline", train[ALLOWED_FEATURE_COLUMNS_V3_3], train[TARGET_NAME_V3_3], dataset[ALLOWED_FEATURE_COLUMNS_V3_3])
    result_b = fit_predict_model("random_seeded_baseline", train[ALLOWED_FEATURE_COLUMNS_V3_3], train[TARGET_NAME_V3_3], dataset[ALLOWED_FEATURE_COLUMNS_V3_3])
    pd.testing.assert_series_equal(result_a.predicted_class, result_b.predicted_class)
    pd.testing.assert_frame_equal(result_a.probabilities, result_b.probabilities)


def test_logistic_regression_runs_offline_v3_3() -> None:
    dataset = prepare_multi_day_ml_frame_v3_3(_dataset_frame())
    train = dataset[dataset["split"] == "train"]
    result = fit_predict_model("logistic_regression", train[ALLOWED_FEATURE_COLUMNS_V3_3], train[TARGET_NAME_V3_3], dataset[ALLOWED_FEATURE_COLUMNS_V3_3])
    assert len(result.predicted_class) == len(dataset)
    assert set(result.probabilities.columns) == {"DOWN", "FLAT", "UP"}


def test_decision_tree_depth_2_runs_offline_v3_3() -> None:
    dataset = prepare_multi_day_ml_frame_v3_3(_dataset_frame())
    train = dataset[dataset["split"] == "train"]
    result = fit_predict_model("decision_tree_depth_2", train[ALLOWED_FEATURE_COLUMNS_V3_3], train[TARGET_NAME_V3_3], dataset[ALLOWED_FEATURE_COLUMNS_V3_3])
    assert len(result.predicted_class) == len(dataset)
    assert set(result.probabilities.columns) == {"DOWN", "FLAT", "UP"}


def test_metrics_include_no_trading_metrics_v3_3() -> None:
    scores = build_multi_day_model_scores_v3_3(_dataset_frame(), dataset_sha256="dataset-sha", ml_run_id="v3_3_20260521T000000Z_1234abcd")
    metrics = compute_multi_day_classification_metrics_v3_3(scores)
    metric_text = str(metrics).casefold()
    assert all(term not in metric_text for term in FORBIDDEN_METRIC_TERMS_V3_3)


def test_outputs_use_research_names_not_signal_names_v3_3() -> None:
    scores = build_multi_day_model_scores_v3_3(_dataset_frame(), dataset_sha256="dataset-sha", ml_run_id="v3_3_20260521T000000Z_1234abcd")
    assert list(scores.columns) == ML_SCORE_COLUMNS_V3_3
    assert "research_predicted_class" in scores.columns
    assert all("signal" not in column.casefold() and "order" not in column.casefold() for column in scores.columns)


def _dataset_frame() -> pd.DataFrame:
    rows = 18
    timestamps = pd.date_range("2024-01-15T00:00:00Z", periods=rows, freq="min")
    frame = pd.DataFrame(
        {
            "source": ["binance_archive"] * rows,
            "venue": ["binance"] * rows,
            "market_type": ["spot"] * rows,
            "symbol": ["BTCUSDT"] * rows,
            "timeframe": ["1m"] * rows,
            "event_ts": timestamps,
            "close_ts": timestamps,
            "decision_ts": timestamps,
            "split": ["train"] * 9 + ["validation"] * 4 + ["test"] * 5,
            "label_valid_h1": [True] * 17 + [False],
            "warmup_row": [False] * 17 + [True],
            TARGET_NAME_V3_3: ["DOWN", "FLAT", "UP"] * 6,
        }
    )
    for index, column in enumerate(ALLOWED_FEATURE_COLUMNS_V3_3):
        frame[column] = [(row + 1) * (index + 1) / 100.0 for row in range(rows)]
    return frame

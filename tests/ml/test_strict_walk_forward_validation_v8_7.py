from __future__ import annotations

import pandas as pd

from galapagos.ml.offline_baselines import fit_predict_model
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V8_7,
    FORBIDDEN_METRIC_TERMS_V8_7,
    ML_SCORE_COLUMNS_V8_7,
    TARGET_NAME_V8_7,
)
from galapagos.ml.strict_walk_forward import (
    LABEL_SHUFFLE_RANDOM_SEED_V8_7,
    WALK_FORWARD_POLICY_V8_7,
    build_strict_walk_forward_folds_v8_7,
    build_strict_walk_forward_scores_v8_7,
    compute_label_shuffle_falsification_v8_7,
    prepare_walk_forward_ml_frame_v8_7,
    scan_strict_walk_forward_feature_leakage_v8_7,
)
from galapagos.ml.strict_walk_forward_metrics import compute_strict_walk_forward_metrics_v8_7


def test_walk_forward_policy_has_expected_fields_v8_7() -> None:
    assert WALK_FORWARD_POLICY_V8_7 == {
        "grouping": "calendar_month",
        "initial_train_months": 6,
        "validation_months": 1,
        "test_months": 1,
        "step_months": 1,
        "purge_bars": 5,
        "embargo_bars": 5,
        "expanding_train": True,
        "shuffle": False,
    }


def test_walk_forward_folds_temporal_order_v8_7() -> None:
    folds = build_strict_walk_forward_folds_v8_7(_dataset_frame(), "2023-03-25", "2023-11-24")
    train_max = pd.to_datetime(folds[folds["fold_role"] == "train"]["event_ts"], utc=True).max()
    validation_min = pd.to_datetime(folds[folds["fold_role"] == "validation"]["event_ts"], utc=True).min()
    validation_max = pd.to_datetime(folds[folds["fold_role"] == "validation"]["event_ts"], utc=True).max()
    test_min = pd.to_datetime(folds[folds["fold_role"] == "test"]["event_ts"], utc=True).min()

    assert train_max < validation_min
    assert validation_max < test_min


def test_walk_forward_folds_have_purge_and_embargo_v8_7() -> None:
    folds = build_strict_walk_forward_folds_v8_7(_dataset_frame(), "2023-03-25", "2023-11-24")

    assert folds["is_purged"].sum() == 10
    assert folds["is_embargoed"].sum() == 10


def test_prepare_walk_forward_ml_frame_uses_only_allowed_features_v8_7() -> None:
    frame = _merged_frame()
    ml_frame = prepare_walk_forward_ml_frame_v8_7(frame)
    scan = scan_strict_walk_forward_feature_leakage_v8_7(ALLOWED_FEATURE_COLUMNS_V8_7)

    assert len(ml_frame) < len(frame)
    assert scan["forbidden_feature_columns_present"] == []


def test_prepare_walk_forward_ml_frame_excludes_fold_columns_from_features_v8_7() -> None:
    assert "fold_id" not in ALLOWED_FEATURE_COLUMNS_V8_7
    assert "fold_role" not in ALLOWED_FEATURE_COLUMNS_V8_7
    assert "is_embargoed" not in ALLOWED_FEATURE_COLUMNS_V8_7
    assert "is_purged" not in ALLOWED_FEATURE_COLUMNS_V8_7


def test_majority_baseline_reproducible_v8_7() -> None:
    ml_frame = prepare_walk_forward_ml_frame_v8_7(_merged_frame())
    train = ml_frame[ml_frame["fold_role"] == "train"]
    result_a = fit_predict_model("majority_class_baseline", train[ALLOWED_FEATURE_COLUMNS_V8_7], train[TARGET_NAME_V8_7], ml_frame[ALLOWED_FEATURE_COLUMNS_V8_7])
    result_b = fit_predict_model("majority_class_baseline", train[ALLOWED_FEATURE_COLUMNS_V8_7], train[TARGET_NAME_V8_7], ml_frame[ALLOWED_FEATURE_COLUMNS_V8_7])

    pd.testing.assert_series_equal(result_a.predicted_class, result_b.predicted_class)


def test_random_seeded_baseline_reproducible_v8_7() -> None:
    ml_frame = prepare_walk_forward_ml_frame_v8_7(_merged_frame())
    train = ml_frame[ml_frame["fold_role"] == "train"]
    result_a = fit_predict_model("random_seeded_baseline", train[ALLOWED_FEATURE_COLUMNS_V8_7], train[TARGET_NAME_V8_7], ml_frame[ALLOWED_FEATURE_COLUMNS_V8_7])
    result_b = fit_predict_model("random_seeded_baseline", train[ALLOWED_FEATURE_COLUMNS_V8_7], train[TARGET_NAME_V8_7], ml_frame[ALLOWED_FEATURE_COLUMNS_V8_7])

    pd.testing.assert_series_equal(result_a.predicted_class, result_b.predicted_class)
    pd.testing.assert_frame_equal(result_a.probabilities, result_b.probabilities)


def test_logistic_regression_runs_offline_v8_7() -> None:
    ml_frame = prepare_walk_forward_ml_frame_v8_7(_merged_frame())
    train = ml_frame[ml_frame["fold_role"] == "train"]
    result = fit_predict_model("logistic_regression", train[ALLOWED_FEATURE_COLUMNS_V8_7], train[TARGET_NAME_V8_7], ml_frame[ALLOWED_FEATURE_COLUMNS_V8_7])

    assert len(result.predicted_class) == len(ml_frame)
    assert set(result.probabilities.columns) == {"DOWN", "FLAT", "UP"}


def test_decision_tree_depth_2_runs_offline_v8_7() -> None:
    ml_frame = prepare_walk_forward_ml_frame_v8_7(_merged_frame())
    train = ml_frame[ml_frame["fold_role"] == "train"]
    result = fit_predict_model("decision_tree_depth_2", train[ALLOWED_FEATURE_COLUMNS_V8_7], train[TARGET_NAME_V8_7], ml_frame[ALLOWED_FEATURE_COLUMNS_V8_7])

    assert len(result.predicted_class) == len(ml_frame)
    assert set(result.probabilities.columns) == {"DOWN", "FLAT", "UP"}


def test_metrics_include_no_trading_metrics_v8_7() -> None:
    dataset = _dataset_frame()
    folds = build_strict_walk_forward_folds_v8_7(dataset, "2023-03-25", "2023-11-24")
    scores = build_strict_walk_forward_scores_v8_7(dataset, folds, dataset_sha256="dataset-sha", ml_run_id="v8_7_20260526T000000Z_1234abcd")
    metrics = compute_strict_walk_forward_metrics_v8_7(scores)
    metric_text = str(metrics).casefold()

    assert len(metrics) > 0
    assert all(term not in metric_text for term in FORBIDDEN_METRIC_TERMS_V8_7)


def test_label_shuffle_falsification_uses_fold_seed_v8_7() -> None:
    dataset = _dataset_frame()
    folds = build_strict_walk_forward_folds_v8_7(dataset, "2023-03-25", "2023-11-24")
    scores = build_strict_walk_forward_scores_v8_7(dataset, folds, dataset_sha256="dataset-sha", ml_run_id="v8_7_20260526T000000Z_1234abcd")
    metrics = compute_strict_walk_forward_metrics_v8_7(scores)
    falsification = compute_label_shuffle_falsification_v8_7(dataset, folds, metrics)

    assert set(payload["random_seed"] for payload in falsification.values()) == {LABEL_SHUFFLE_RANDOM_SEED_V8_7 + 1}
    assert all(payload["shuffle_scope"] == "train_labels_only" for payload in falsification.values())


def test_outputs_use_research_names_not_signal_names_v8_7() -> None:
    dataset = _dataset_frame()
    folds = build_strict_walk_forward_folds_v8_7(dataset, "2023-03-25", "2023-11-24")
    scores = build_strict_walk_forward_scores_v8_7(dataset, folds, dataset_sha256="dataset-sha", ml_run_id="v8_7_20260526T000000Z_1234abcd")

    assert list(scores.columns) == ML_SCORE_COLUMNS_V8_7
    assert "research_predicted_class" in scores.columns
    assert all(column.casefold() not in {"signal", "trading_signal", "order", "strategy", "pnl", "profit"} for column in scores.columns)


def _merged_frame() -> pd.DataFrame:
    dataset = _dataset_frame()
    folds = build_strict_walk_forward_folds_v8_7(dataset, "2023-03-25", "2023-11-24")
    return folds.merge(dataset, on=["source", "venue", "market_type", "symbol", "timeframe", "event_ts"], how="left", validate="many_to_one")


def _dataset_frame() -> pd.DataFrame:
    rows = 245
    timestamps = pd.date_range("2023-03-25T00:00:00Z", periods=rows, freq="D")
    payload = {
        "source": ["binance_archive"] * rows,
        "venue": ["binance"] * rows,
        "market_type": ["spot"] * rows,
        "symbol": ["BTCUSDT"] * rows,
        "timeframe": ["1d_test"] * rows,
        "event_ts": timestamps,
        "close_ts": timestamps + pd.Timedelta(hours=23),
        "decision_ts": timestamps + pd.Timedelta(days=1),
        "label_valid_h1": [True] * (rows - 1) + [False],
        "warmup_row": [False] * (rows - 2) + [True, False],
        TARGET_NAME_V8_7: (["DOWN", "FLAT", "UP"] * ((rows // 3) + 1))[:rows],
    }
    for index, column in enumerate(ALLOWED_FEATURE_COLUMNS_V8_7):
        payload[column] = [((row % 17) + 1) * (index + 1) / 100.0 for row in range(rows)]
    return pd.DataFrame(payload)

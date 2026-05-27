from __future__ import annotations

import pandas as pd

from galapagos.datasets.h4_label_candidate_dataset_v9_13_schemas import ML_FEATURE_COLUMNS_V9_13, TARGET_NAME_V9_13
from galapagos.ml.h4_label_candidate_offline_ml_v9_13 import (
    ML_SCORE_COLUMNS_V9_13,
    baseline_comparison_v9_13,
    build_h4_model_scores_v9_13,
    compute_label_shuffle_falsification_v9_13,
    decide_ml_v9_13,
    feature_leakage_scan_v9_13,
    prepare_h4_ml_frame_v9_13,
)
from galapagos.ml.h4_label_candidate_offline_ml_v9_13_metrics import compute_h4_classification_metrics_v9_13


def _dataset(rows: int = 90) -> pd.DataFrame:
    ts = pd.date_range("2023-03-25", periods=rows, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "source": "binance_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "event_ts": ts,
            "close_ts": ts,
            "decision_ts": ts,
            "split": ["train"] * 54 + ["validation"] * 18 + ["test"] * 18,
            "walk_forward_group": ts.strftime("wf_%Y_%m"),
            TARGET_NAME_V9_13: (["DOWN", "FLAT", "UP"] * 30)[:rows],
            "label_valid": True,
            "warmup_row": False,
        }
    )
    for index, column in enumerate(ML_FEATURE_COLUMNS_V9_13):
        frame[column] = [(row % (index + 3)) / (index + 3) for row in range(rows)]
    return frame


def test_prepare_h4_ml_frame_filters_valid_rows_v9_13() -> None:
    dataset = _dataset()
    dataset.loc[0, "label_valid"] = False
    dataset.loc[1, "warmup_row"] = True

    ml_frame = prepare_h4_ml_frame_v9_13(dataset)

    assert len(ml_frame) == len(dataset) - 2
    assert ml_frame["label_valid"].all()
    assert not ml_frame["warmup_row"].any()


def test_h4_scores_use_research_columns_v9_13() -> None:
    scores = build_h4_model_scores_v9_13(_dataset(), dataset_path="dataset.parquet", ml_run_id="test")

    assert list(scores.columns) == ML_SCORE_COLUMNS_V9_13
    assert set(scores["model_name"].unique()) == {"majority_class_baseline", "random_seeded_baseline", "logistic_regression", "decision_tree_depth_2"}
    assert "signal" not in scores.columns
    assert "order" not in scores.columns
    assert scores["target_name"].unique().tolist() == [TARGET_NAME_V9_13]


def test_h4_metrics_and_baseline_comparison_v9_13() -> None:
    scores = build_h4_model_scores_v9_13(_dataset(), dataset_path="dataset.parquet", ml_run_id="test")
    metrics = compute_h4_classification_metrics_v9_13(scores)
    comparison = baseline_comparison_v9_13(metrics)

    assert metrics
    assert comparison["comparisons"]
    assert "clear_wins_count" in comparison


def test_h4_label_shuffle_uses_seed_123_v9_13() -> None:
    dataset = _dataset()
    scores = build_h4_model_scores_v9_13(dataset, dataset_path="dataset.parquet", ml_run_id="test")
    shuffle = compute_label_shuffle_falsification_v9_13(dataset, scores)

    assert shuffle
    assert {item["random_seed"] for item in shuffle.values()} == {123}


def test_h4_feature_leakage_scan_rejects_label_columns_v9_13() -> None:
    clean = feature_leakage_scan_v9_13(ML_FEATURE_COLUMNS_V9_13)
    dirty = feature_leakage_scan_v9_13([*ML_FEATURE_COLUMNS_V9_13, "up_down_flat_volnorm_h4"])

    assert clean["passed"] is True
    assert dirty["passed"] is False


def test_h4_ml_decision_is_conservative_when_close_to_shuffle_v9_13() -> None:
    decision = decide_ml_v9_13(
        "PASS",
        {"clear_wins_count": 0},
        {"1m.logistic_regression.test": {"no_clear_edge_vs_shuffled_labels": True}},
    )

    assert decision == "h4_offline_ml_completed_but_close_to_shuffled_labels"

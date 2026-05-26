from __future__ import annotations

from pathlib import Path

import pandas as pd

from galapagos.ml.refined_ohlcv_trades_window_validation import (
    validate_feature_columns_v9_2,
    validate_refined_ohlcv_trades_offline_ml_research_v9_2,
    validate_score_schema_v9_2,
    validate_scores_against_dataset_v9_2,
)
from galapagos.ml.schemas import ML_SCORE_COLUMNS_V9_2, MODEL_NAMES_V9_2


ROOT = Path(__file__).resolve().parents[2]


def test_validator_v9_2_accepts_valid_offline_ml_research() -> None:
    result = validate_refined_ohlcv_trades_offline_ml_research_v9_2(ROOT)

    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v9_2_rejects_forbidden_future_feature() -> None:
    errors = validate_feature_columns_v9_2(["future_log_return_h1"])

    assert any("forbidden" in error for error in errors)


def test_validator_v9_2_rejects_forbidden_label_feature() -> None:
    errors = validate_feature_columns_v9_2(["label_valid_h1"])

    assert any("forbidden" in error for error in errors)


def test_validator_v9_2_rejects_forbidden_split_feature() -> None:
    errors = validate_feature_columns_v9_2(["split"])

    assert any("forbidden" in error for error in errors)


def test_validator_v9_2_rejects_forbidden_walk_forward_group_feature() -> None:
    errors = validate_feature_columns_v9_2(["walk_forward_group"])

    assert any("forbidden" in error for error in errors)


def test_validator_v9_2_rejects_unknown_model() -> None:
    scores = _score_frame()
    scores["model_name"] = "random_forest"

    errors = validate_score_schema_v9_2(scores, "1m")

    assert any("unknown model" in error for error in errors)


def test_validator_v9_2_rejects_output_trading_signal_column() -> None:
    scores = _score_frame()
    scores["trading_signal"] = "hold"

    errors = validate_score_schema_v9_2(scores, "1m")

    assert any("schema" in error or "forbidden" in error for error in errors)


def test_validator_v9_2_rejects_output_order_column() -> None:
    scores = _score_frame()
    scores["order"] = "none"

    errors = validate_score_schema_v9_2(scores, "1m")

    assert any("schema" in error or "forbidden" in error for error in errors)


def test_validator_v9_2_rejects_output_pnl_column() -> None:
    scores = _score_frame()
    scores["pnl"] = 0.0

    errors = validate_score_schema_v9_2(scores, "1m")

    assert any("schema" in error or "forbidden" in error for error in errors)


def test_validator_v9_2_rejects_missing_walk_forward_group_in_scores() -> None:
    scores = _score_frame().drop(columns=["walk_forward_group"])

    errors = validate_score_schema_v9_2(scores, "1m")

    assert any("schema" in error for error in errors)


def test_validator_v9_2_rejects_wrong_dataset_sha() -> None:
    scores = _score_frame()
    dataset = _dataset_frame()
    scores["dataset_sha256"] = "bad"

    errors = validate_scores_against_dataset_v9_2(scores, dataset, "dataset-sha", "1m", "v9_2_20260526T000000Z_1234abcd")

    assert any("dataset_sha256" in error for error in errors)


def test_validator_v9_2_rejects_prediction_available_before_decision() -> None:
    scores = _score_frame()
    dataset = _dataset_frame()
    scores["prediction_available_ts"] = "2023-03-24T23:59:00Z"

    errors = validate_scores_against_dataset_v9_2(scores, dataset, "dataset-sha", "1m", "v9_2_20260526T000000Z_1234abcd")

    assert any("prediction_available_ts" in error for error in errors)


def _score_frame() -> pd.DataFrame:
    payload = {column: [_score_value(column)] for column in ML_SCORE_COLUMNS_V9_2}
    return pd.DataFrame(payload)


def _dataset_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "label_valid_h1": [True],
            "warmup_row": [False],
            "split": ["train"],
            "event_ts": ["2023-03-25T00:00:00Z"],
            "decision_ts": ["2023-03-25T00:01:00Z"],
        }
    )


def _score_value(column: str) -> object:
    if column in {"event_ts", "close_ts"}:
        return "2023-03-25T00:00:00Z"
    if column in {"decision_ts", "prediction_available_ts"}:
        return "2023-03-25T00:01:00Z"
    if column in {"source", "venue", "market_type", "symbol", "timeframe"}:
        return {
            "source": "binance_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "timeframe": "1m",
        }[column]
    if column == "split":
        return "train"
    if column == "walk_forward_group":
        return "wf_2023_03_partial"
    if column == "ml_run_id":
        return "v9_2_20260526T000000Z_1234abcd"
    if column == "model_name":
        return MODEL_NAMES_V9_2[0]
    if column == "target_name":
        return "up_down_flat_h1"
    if column == "dataset_sha256":
        return "dataset-sha"
    if column == "feature_columns_sha256":
        from galapagos.ml.schemas import get_feature_columns_sha256_v9_2

        return get_feature_columns_sha256_v9_2()
    if column == "ml_schema_version":
        return "V9.2"
    if column in {"target_value", "research_predicted_class"}:
        return "UP"
    if column in {"research_probability_down", "research_probability_flat"}:
        return 0.0
    if column == "research_probability_up":
        return 1.0
    if column == "row_valid_for_ml":
        return True
    if column in {"ml_null_count", "ml_error_count"}:
        return 0
    return ""

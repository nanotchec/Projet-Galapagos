from __future__ import annotations

from pathlib import Path

import pandas as pd

from galapagos.ml.refined_strict_walk_forward_validation import (
    validate_feature_columns_v9_3,
    validate_fold_temporal_order_v9_3,
    validate_folds_schema_v9_3,
    validate_refined_strict_walk_forward_validation_v9_3,
    validate_score_schema_v9_3,
    validate_scores_against_inputs_v9_3,
)
from galapagos.ml.schemas import ML_SCORE_COLUMNS_V9_3, MODEL_NAMES_V9_3, WALK_FORWARD_FOLD_COLUMNS_V9_3, get_feature_columns_sha256_v9_3


ROOT = Path(__file__).resolve().parents[2]


def test_validator_v9_3_accepts_valid_walk_forward_report() -> None:
    result = validate_refined_strict_walk_forward_validation_v9_3(ROOT)

    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v9_3_rejects_forbidden_future_feature() -> None:
    errors = validate_feature_columns_v9_3(["future_log_return_h1"])

    assert any("forbidden" in error for error in errors)


def test_validator_v9_3_rejects_forbidden_label_feature() -> None:
    errors = validate_feature_columns_v9_3(["label_valid_h1"])

    assert any("forbidden" in error for error in errors)


def test_validator_v9_3_rejects_forbidden_fold_feature() -> None:
    errors = validate_feature_columns_v9_3(["fold_id"])

    assert any("forbidden" in error for error in errors)


def test_validator_v9_3_rejects_unknown_model() -> None:
    scores = _score_frame()
    scores["model_name"] = "random_forest"

    errors = validate_score_schema_v9_3(scores, "1m")

    assert any("unknown model" in error for error in errors)


def test_validator_v9_3_rejects_output_trading_signal_column() -> None:
    scores = _score_frame()
    scores["trading_signal"] = "hold"

    errors = validate_score_schema_v9_3(scores, "1m")

    assert any("schema" in error or "forbidden" in error for error in errors)


def test_validator_v9_3_rejects_output_order_column() -> None:
    scores = _score_frame()
    scores["order"] = "none"

    errors = validate_score_schema_v9_3(scores, "1m")

    assert any("schema" in error or "forbidden" in error for error in errors)


def test_validator_v9_3_rejects_output_pnl_column() -> None:
    scores = _score_frame()
    scores["pnl"] = 0.0

    errors = validate_score_schema_v9_3(scores, "1m")

    assert any("schema" in error or "forbidden" in error for error in errors)


def test_validator_v9_3_rejects_overlapping_folds() -> None:
    folds = _folds_frame()
    folds.loc[folds["fold_role"] == "validation", "event_ts"] = "2023-03-25T00:00:00Z"

    errors = validate_fold_temporal_order_v9_3(folds, "1m")

    assert any("temporal order" in error for error in errors)


def test_validator_v9_3_rejects_validation_before_train() -> None:
    folds = _folds_frame()
    folds.loc[folds["fold_role"] == "validation", "event_ts"] = "2023-03-24T00:00:00Z"

    errors = validate_fold_temporal_order_v9_3(folds, "1m")

    assert any("temporal order" in error for error in errors)


def test_validator_v9_3_rejects_test_before_validation() -> None:
    folds = _folds_frame()
    folds.loc[folds["fold_role"] == "test", "event_ts"] = "2023-03-25T00:00:00Z"

    errors = validate_fold_temporal_order_v9_3(folds, "1m")

    assert any("temporal order" in error for error in errors)


def test_validator_v9_3_rejects_folds_schema_mismatch() -> None:
    folds = _folds_frame().drop(columns=["is_purged"])

    errors = validate_folds_schema_v9_3(folds, "1m")

    assert any("schema" in error for error in errors)


def test_validator_v9_3_rejects_wrong_dataset_sha() -> None:
    scores = _score_frame()
    dataset = pd.DataFrame({"event_ts": ["2023-03-25T00:00:00Z"]})
    scores["dataset_sha256"] = "bad"

    errors = validate_scores_against_inputs_v9_3(scores, dataset, "dataset-sha", "v9_3_20260526T000000Z_1234abcd", "1m")

    assert any("dataset_sha256" in error for error in errors)


def _score_frame() -> pd.DataFrame:
    payload = {column: [_score_value(column)] for column in ML_SCORE_COLUMNS_V9_3}
    return pd.DataFrame(payload)


def _folds_frame() -> pd.DataFrame:
    rows = [
        ("train", "2023-03-25T00:00:00Z"),
        ("validation", "2023-03-26T00:00:00Z"),
        ("test", "2023-03-27T00:00:00Z"),
    ]
    payload = []
    for index, (role, event_ts) in enumerate(rows):
        record = {
            "source": "binance_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "timeframe": "1m",
            "event_ts": event_ts,
            "fold_id": "fold_01",
            "fold_role": role,
            "fold_order": 1,
            "is_embargoed": False,
            "is_purged": False,
            "walk_forward_policy_version": "refined_strict_walk_forward_v9_3_calendar_month_v1",
        }
        payload.append(record)
    return pd.DataFrame(payload)[WALK_FORWARD_FOLD_COLUMNS_V9_3]


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
    if column == "fold_id":
        return "fold_01"
    if column == "fold_role":
        return "train"
    if column == "fold_order":
        return 1
    if column == "ml_run_id":
        return "v9_3_20260526T000000Z_1234abcd"
    if column == "model_name":
        return MODEL_NAMES_V9_3[0]
    if column == "target_name":
        return "up_down_flat_h1"
    if column == "dataset_sha256":
        return "dataset-sha"
    if column == "feature_columns_sha256":
        return get_feature_columns_sha256_v9_3()
    if column == "ml_schema_version":
        return "V9.3"
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

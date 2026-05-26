from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.storage import read_parquet
from galapagos.ml.strict_walk_forward import folds_output_path, load_v8_4_dataset_manifest, score_output_path
from galapagos.ml.strict_walk_forward_validation import (
    _find_forbidden_v8_7_artifacts,
    _scan_metrics_for_forbidden_terms,
    _validate_feature_columns,
    _validate_findings,
    _validate_folds_temporal_order,
    _validate_markdown,
    _validate_manifest_structure,
    _validate_report,
    _validate_safety,
    _validate_score_frame_schema_only,
    validate_strict_walk_forward_validation_v8_7,
)
from galapagos.ml.schemas import MANIFEST_PATH_V8_7, REPORT_JSON_PATH_V8_7
from galapagos.validation.safety import validate_markdown_forbidden_claims


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def valid_v8_7_validation_result() -> dict[str, Any]:
    result = validate_strict_walk_forward_validation_v8_7(ROOT)
    assert result["passed"], result["errors"]
    return deepcopy(result)


@pytest.fixture()
def valid_v8_7_manifest_report() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    dataset_manifest = load_v8_4_dataset_manifest(ROOT)
    return deepcopy(_load(ROOT / MANIFEST_PATH_V8_7)), deepcopy(_load(ROOT / REPORT_JSON_PATH_V8_7)), deepcopy(dataset_manifest)


@pytest.fixture()
def valid_score_frame_v8_7() -> pd.DataFrame:
    dataset_manifest = load_v8_4_dataset_manifest(ROOT)
    window = dataset_manifest["input_features_manifest"]
    return read_parquet(score_output_path(ROOT, "1h", window["window_start"], window["window_end"])).copy()


@pytest.fixture()
def valid_folds_frame_v8_7() -> pd.DataFrame:
    dataset_manifest = load_v8_4_dataset_manifest(ROOT)
    window = dataset_manifest["input_features_manifest"]
    return read_parquet(folds_output_path(ROOT, "1h", window["window_start"], window["window_end"])).copy()


def test_validator_v8_7_accepts_valid_walk_forward_report(valid_v8_7_validation_result: dict[str, Any]) -> None:
    assert valid_v8_7_validation_result["passed"] is True
    assert valid_v8_7_validation_result["errors"] == []


def test_validator_v8_7_rejects_forbidden_future_feature() -> None:
    errors = _validate_feature_columns(["agg_trade_count", "future_log_return_h1"])
    assert _errors_contain(errors, "V8.7 forbidden feature columns")


def test_validator_v8_7_rejects_forbidden_label_feature() -> None:
    errors = _validate_feature_columns(["agg_trade_count", "label_valid_h1"])
    assert _errors_contain(errors, "V8.7 forbidden feature columns")


def test_validator_v8_7_rejects_forbidden_fold_feature() -> None:
    errors = _validate_feature_columns(["agg_trade_count", "fold_id", "fold_role", "is_embargoed"])
    assert _errors_contain(errors, "V8.7 forbidden feature columns")


def test_validator_v8_7_rejects_unknown_model(valid_v8_7_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, dataset_manifest = valid_v8_7_manifest_report
    manifest["models"] = [*manifest["models"], "random_forest"]
    errors = _validate_manifest_structure(ROOT, manifest, dataset_manifest)
    assert _errors_contain(errors, "V8.7 models mismatch")


def test_validator_v8_7_rejects_output_trading_signal_column(valid_score_frame_v8_7: pd.DataFrame) -> None:
    valid_score_frame_v8_7["trading_signal"] = "none"
    errors = _validate_score_frame_schema_only(valid_score_frame_v8_7, "1h")
    assert _errors_contain(errors, "V8.7 score schema mismatch for 1h")
    assert _errors_contain(errors, "V8.7 score forbidden columns for 1h")


def test_validator_v8_7_rejects_output_order_column(valid_score_frame_v8_7: pd.DataFrame) -> None:
    valid_score_frame_v8_7["order"] = "none"
    errors = _validate_score_frame_schema_only(valid_score_frame_v8_7, "1h")
    assert _errors_contain(errors, "V8.7 score schema mismatch for 1h")
    assert _errors_contain(errors, "V8.7 score forbidden columns for 1h")


def test_validator_v8_7_rejects_output_pnl_column(valid_score_frame_v8_7: pd.DataFrame) -> None:
    valid_score_frame_v8_7["pnl"] = 0.0
    errors = _validate_score_frame_schema_only(valid_score_frame_v8_7, "1h")
    assert _errors_contain(errors, "V8.7 score schema mismatch for 1h")
    assert _errors_contain(errors, "V8.7 score forbidden columns for 1h")


def test_validator_v8_7_rejects_overlapping_folds(valid_folds_frame_v8_7: pd.DataFrame) -> None:
    fold_id = valid_folds_frame_v8_7["fold_id"].iloc[0]
    train_index = valid_folds_frame_v8_7[(valid_folds_frame_v8_7["fold_id"] == fold_id) & (valid_folds_frame_v8_7["fold_role"] == "train")].tail(1).index
    valid_folds_frame_v8_7.loc[train_index, "event_ts"] = valid_folds_frame_v8_7[
        (valid_folds_frame_v8_7["fold_id"] == fold_id) & (valid_folds_frame_v8_7["fold_role"] == "validation")
    ]["event_ts"].iloc[0]
    errors = _validate_folds_temporal_order(valid_folds_frame_v8_7, "1h")
    assert _errors_contain(errors, "V8.7 fold validation before train")


def test_validator_v8_7_rejects_validation_before_train(valid_folds_frame_v8_7: pd.DataFrame) -> None:
    fold_id = valid_folds_frame_v8_7["fold_id"].iloc[0]
    validation_index = valid_folds_frame_v8_7[
        (valid_folds_frame_v8_7["fold_id"] == fold_id) & (valid_folds_frame_v8_7["fold_role"] == "validation")
    ].head(1).index
    valid_folds_frame_v8_7.loc[validation_index, "event_ts"] = "2023-03-25T00:00:00Z"
    errors = _validate_folds_temporal_order(valid_folds_frame_v8_7, "1h")
    assert _errors_contain(errors, "V8.7 fold validation before train")


def test_validator_v8_7_rejects_test_before_validation(valid_folds_frame_v8_7: pd.DataFrame) -> None:
    fold_id = valid_folds_frame_v8_7["fold_id"].iloc[0]
    test_index = valid_folds_frame_v8_7[(valid_folds_frame_v8_7["fold_id"] == fold_id) & (valid_folds_frame_v8_7["fold_role"] == "test")].head(1).index
    valid_folds_frame_v8_7.loc[test_index, "event_ts"] = "2023-09-26T00:00:00Z"
    errors = _validate_folds_temporal_order(valid_folds_frame_v8_7, "1h")
    assert _errors_contain(errors, "V8.7 fold test before validation")


def test_validator_v8_7_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v8_7_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V8.7 artifact detected")


def test_validator_v8_7_rejects_strategy_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/strategies/strategy.json")
    errors = _find_forbidden_v8_7_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V8.7 artifact detected")


def test_validator_v8_7_rejects_orders_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "orders/order.json")
    errors = _find_forbidden_v8_7_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V8.7 artifact detected")


def test_validator_v8_7_rejects_model_pickle_created(tmp_path: Path) -> None:
    path = tmp_path / "models/model.pkl"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"not-a-model")
    errors = _find_forbidden_v8_7_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V8.7 artifact detected")


def test_validator_v8_7_rejects_markdown_strategy_validated_claim() -> None:
    errors = validate_markdown_forbidden_claims("Rapport V8.7.\nStrategy validated.\n", "V8.7 Markdown report")
    assert _errors_contain(errors, "V8.7 Markdown report contains forbidden claim")


def test_validator_v8_7_rejects_markdown_tradable_edge_confirmed_claim(tmp_path: Path) -> None:
    errors = _validate_markdown(_write_v8_7_markdown_pair(tmp_path, "Rapport V8.7.\nTradable edge confirmed.\n"))
    assert _errors_contain(errors, "tradable edge confirmed")


def test_validator_v8_7_rejects_safety_flag_trading_true(valid_v8_7_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v8_7_manifest_report, "trading_enabled", True))
    assert _errors_contain(errors, "V8.7 safety flag trading_enabled must be False")


def test_validator_v8_7_rejects_safety_flag_backtest_true(valid_v8_7_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v8_7_manifest_report, "backtest_enabled", True))
    assert _errors_contain(errors, "V8.7 safety flag backtest_enabled must be False")


def test_validator_v8_7_rejects_walk_forward_validated_for_trading_true(valid_v8_7_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, _dataset_manifest = valid_v8_7_manifest_report
    manifest["findings"]["walk_forward_validated_for_trading"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V8.7 finding walk_forward_validated_for_trading must be False")


def test_validator_v8_7_rejects_trading_metric_in_metrics() -> None:
    errors = _scan_metrics_for_forbidden_terms({"model": {"sharpe": 1.0}}, "metrics")
    assert _errors_contain(errors, "V8.7 metrics contain forbidden trading metric")


def test_validator_v8_7_rejects_report_json_lie(valid_v8_7_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, report, _dataset_manifest = valid_v8_7_manifest_report
    report["metrics"] = {}
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V8.7 report mismatch")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mutated_safety(bundle: tuple[dict[str, Any], dict[str, Any], dict[str, Any]], key: str, value: Any) -> dict[str, Any]:
    manifest, _report, _dataset_manifest = bundle
    safety = deepcopy(manifest["safety"])
    safety[key] = value
    return safety


def _touch_forbidden(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")


def _write_v8_7_markdown_pair(root: Path, text: str) -> Path:
    for relative in ["reports/ml/strict_walk_forward_validation_v8_7.md", "reports/ml/strict_walk_forward_scores_v8_7.md", "docs/strict_walk_forward_validation_v8_7.md"]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)

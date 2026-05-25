from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.storage import read_parquet
from galapagos.ml.ohlcv_trades_90d_window import load_v7_9_dataset_manifest, score_output_path
from galapagos.ml.ohlcv_trades_90d_window_validation import (
    _find_forbidden_v8_0_artifacts,
    _scan_metrics_for_forbidden_terms,
    _validate_manifest_structure,
    _validate_report,
    _validate_safety,
    _validate_score_frame_schema_only,
    validate_ohlcv_trades_90d_offline_ml_research_v8_0,
)
from galapagos.ml.schemas import MANIFEST_PATH_V8_0, REPORT_JSON_PATH_V8_0
from galapagos.validation.safety import validate_markdown_forbidden_claims


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def valid_v8_0_validation_result() -> dict[str, Any]:
    result = validate_ohlcv_trades_90d_offline_ml_research_v8_0(ROOT)
    assert result["passed"], result["errors"]
    return deepcopy(result)


@pytest.fixture()
def valid_v8_0_manifest_report() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    dataset_manifest = load_v7_9_dataset_manifest(ROOT)
    return deepcopy(_load(ROOT / MANIFEST_PATH_V8_0)), deepcopy(_load(ROOT / REPORT_JSON_PATH_V8_0)), deepcopy(dataset_manifest)


@pytest.fixture()
def valid_score_frame_v8_0() -> pd.DataFrame:
    dataset_manifest = load_v7_9_dataset_manifest(ROOT)
    window = dataset_manifest["input_features_manifest"]
    return read_parquet(score_output_path(ROOT, "1h", window["window_start"], window["window_end"])).copy()


def test_validator_v8_0_accepts_valid_offline_ml_research(valid_v8_0_validation_result: dict[str, Any]) -> None:
    assert valid_v8_0_validation_result["passed"] is True
    assert valid_v8_0_validation_result["errors"] == []


def test_validator_v8_0_accepts_allowed_ohlcv_trades_features(valid_v8_0_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, dataset_manifest = valid_v8_0_manifest_report
    assert "agg_trade_count" in manifest["feature_columns"]
    assert "taker_buy_ratio_quantity" in manifest["feature_columns"]
    assert "warmup_row" not in manifest["feature_columns"]
    errors = _validate_manifest_structure(ROOT, manifest, dataset_manifest)
    assert not _errors_contain(errors, "forbidden feature columns")


def test_validator_v8_0_rejects_forbidden_future_feature(valid_v8_0_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, dataset_manifest = valid_v8_0_manifest_report
    manifest["feature_columns"] = [*manifest["feature_columns"], "future_log_return_h1"]
    errors = _validate_manifest_structure(ROOT, manifest, dataset_manifest)
    assert _errors_contain(errors, "V8.0 feature_columns mismatch")
    assert _errors_contain(errors, "V8.0 forbidden feature columns")


def test_validator_v8_0_rejects_forbidden_label_feature(valid_v8_0_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, dataset_manifest = valid_v8_0_manifest_report
    manifest["feature_columns"] = [*manifest["feature_columns"], "label_valid_h1"]
    errors = _validate_manifest_structure(ROOT, manifest, dataset_manifest)
    assert _errors_contain(errors, "V8.0 feature_columns mismatch")
    assert _errors_contain(errors, "V8.0 forbidden feature columns")


def test_validator_v8_0_rejects_forbidden_split_feature(valid_v8_0_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, dataset_manifest = valid_v8_0_manifest_report
    manifest["feature_columns"] = [*manifest["feature_columns"], "split"]
    errors = _validate_manifest_structure(ROOT, manifest, dataset_manifest)
    assert _errors_contain(errors, "V8.0 feature_columns mismatch")
    assert _errors_contain(errors, "V8.0 forbidden feature columns")


def test_validator_v8_0_rejects_forbidden_walk_forward_group_feature(valid_v8_0_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, dataset_manifest = valid_v8_0_manifest_report
    manifest["feature_columns"] = [*manifest["feature_columns"], "walk_forward_group"]
    errors = _validate_manifest_structure(ROOT, manifest, dataset_manifest)
    assert _errors_contain(errors, "V8.0 feature_columns mismatch")
    assert _errors_contain(errors, "V8.0 forbidden feature columns")


def test_validator_v8_0_rejects_unknown_model(valid_v8_0_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, dataset_manifest = valid_v8_0_manifest_report
    manifest["models"] = [*manifest["models"], "random_forest"]
    errors = _validate_manifest_structure(ROOT, manifest, dataset_manifest)
    assert _errors_contain(errors, "V8.0 models mismatch")


def test_validator_v8_0_rejects_output_trading_signal_column(valid_score_frame_v8_0: pd.DataFrame) -> None:
    valid_score_frame_v8_0["trading_signal"] = "none"
    errors = _validate_score_frame_schema_only(valid_score_frame_v8_0, "1h")
    assert _errors_contain(errors, "V8.0 score schema mismatch for 1h")
    assert _errors_contain(errors, "V8.0 score forbidden columns for 1h")


def test_validator_v8_0_rejects_output_order_column(valid_score_frame_v8_0: pd.DataFrame) -> None:
    valid_score_frame_v8_0["order"] = "none"
    errors = _validate_score_frame_schema_only(valid_score_frame_v8_0, "1h")
    assert _errors_contain(errors, "V8.0 score schema mismatch for 1h")
    assert _errors_contain(errors, "V8.0 score forbidden columns for 1h")


def test_validator_v8_0_rejects_output_pnl_column(valid_score_frame_v8_0: pd.DataFrame) -> None:
    valid_score_frame_v8_0["pnl"] = 0.0
    errors = _validate_score_frame_schema_only(valid_score_frame_v8_0, "1h")
    assert _errors_contain(errors, "V8.0 score schema mismatch for 1h")
    assert _errors_contain(errors, "V8.0 score forbidden columns for 1h")


def test_validator_v8_0_rejects_missing_walk_forward_group_in_scores(valid_score_frame_v8_0: pd.DataFrame) -> None:
    errors = _validate_score_frame_schema_only(valid_score_frame_v8_0.drop(columns=["walk_forward_group"]), "1h")
    assert _errors_contain(errors, "V8.0 score schema mismatch for 1h")
    assert _errors_contain(errors, "V8.0 score walk_forward_group missing for 1h")


def test_validator_v8_0_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v8_0_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V8.0 artifact detected")


def test_validator_v8_0_rejects_strategy_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/strategies/strategy.json")
    errors = _find_forbidden_v8_0_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V8.0 artifact detected")


def test_validator_v8_0_rejects_orders_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "orders/order.json")
    errors = _find_forbidden_v8_0_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V8.0 artifact detected")


def test_validator_v8_0_rejects_model_pickle_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v8_0/ml/offline_research_ohlcv_trades/model.pkl")
    errors = _find_forbidden_v8_0_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V8.0 artifact detected")


def test_validator_v8_0_rejects_report_json_lie(valid_v8_0_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, report, _dataset_manifest = valid_v8_0_manifest_report
    report["metrics"] = {}
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V8.0 quality report mismatch")


def test_validator_v8_0_rejects_manifest_unexpected_key(valid_v8_0_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, dataset_manifest = valid_v8_0_manifest_report
    manifest["strategy_validated"] = True
    errors = _validate_manifest_structure(ROOT, manifest, dataset_manifest)
    assert _errors_contain(errors, "V8.0 manifest unexpected keys")


def test_validator_v8_0_rejects_report_unexpected_key(valid_v8_0_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, report, _dataset_manifest = valid_v8_0_manifest_report
    report["claim"] = "strategy validated"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V8.0 quality report unexpected keys")


def test_validator_v8_0_rejects_markdown_strategy_validated_claim() -> None:
    errors = validate_markdown_forbidden_claims("Rapport V8.0.\nStrategy validated.\n", "V8.0 Markdown report")
    assert _errors_contain(errors, "V8.0 Markdown report contains forbidden claim")


def test_validator_v8_0_rejects_safety_flag_trading_true(valid_v8_0_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v8_0_manifest_report, "trading_enabled", True))
    assert _errors_contain(errors, "V8.0 safety flag trading_enabled must be False")


def test_validator_v8_0_rejects_safety_flag_backtest_true(valid_v8_0_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v8_0_manifest_report, "backtest_enabled", True))
    assert _errors_contain(errors, "V8.0 safety flag backtest_enabled must be False")


def test_validator_v8_0_rejects_safety_flag_strategy_true(valid_v8_0_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v8_0_manifest_report, "strategy_enabled", True))
    assert _errors_contain(errors, "V8.0 safety flag strategy_enabled must be False")


def test_validator_v8_0_rejects_safety_flag_execution_true(valid_v8_0_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v8_0_manifest_report, "execution_enabled", True))
    assert _errors_contain(errors, "V8.0 safety flag execution_enabled must be False")


def test_validator_v8_0_rejects_trading_metric_in_metrics() -> None:
    errors = _scan_metrics_for_forbidden_terms({"1m.model.test": {"sharpe": 1.0}}, "metrics")
    assert _errors_contain(errors, "V8.0 metrics contain forbidden trading metric")


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


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.storage import read_parquet
from galapagos.ml.one_year_window_validation import (
    _find_forbidden_v4_6_artifacts,
    _scan_metrics_for_forbidden_terms,
    _validate_manifest_structure,
    _validate_report,
    _validate_safety,
    _validate_score_frame_schema_only,
    _validate_scores_report,
    validate_one_year_offline_ml_research_v4_6,
)
from galapagos.ml.schemas import (
    MANIFEST_PATH_V4_6,
    REPORT_JSON_PATH_V4_6,
    SCORES_JSON_PATH_V4_6,
    get_one_year_ml_score_path_v4_6,
)
from galapagos.validation.safety import validate_markdown_forbidden_claims


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def valid_v4_6_validation_result() -> dict[str, Any]:
    result = validate_one_year_offline_ml_research_v4_6(ROOT)
    assert result["passed"], result["errors"]
    return deepcopy(result)


@pytest.fixture()
def valid_v4_6_manifest_report() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(ROOT / MANIFEST_PATH_V4_6)), deepcopy(_load(ROOT / REPORT_JSON_PATH_V4_6)), deepcopy(_load(ROOT / SCORES_JSON_PATH_V4_6))


@pytest.fixture()
def valid_score_frame_v4_6() -> pd.DataFrame:
    return read_parquet(get_one_year_ml_score_path_v4_6(ROOT, "5m")).copy()


def test_validator_v4_6_accepts_valid_offline_ml_research(valid_v4_6_validation_result: dict[str, Any]) -> None:
    assert valid_v4_6_validation_result["passed"] is True
    assert valid_v4_6_validation_result["errors"] == []


def test_validator_v4_6_rejects_forbidden_future_feature(valid_v4_6_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, _scores_report = valid_v4_6_manifest_report
    manifest["feature_columns"] = [*manifest["feature_columns"], "future_log_return_h1"]
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V4.6 feature_columns mismatch")
    assert _errors_contain(errors, "V4.6 forbidden feature columns")


def test_validator_v4_6_rejects_forbidden_label_feature(valid_v4_6_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, _scores_report = valid_v4_6_manifest_report
    manifest["feature_columns"] = [*manifest["feature_columns"], "label_valid_h1"]
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V4.6 feature_columns mismatch")


def test_validator_v4_6_rejects_forbidden_split_feature(valid_v4_6_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, _scores_report = valid_v4_6_manifest_report
    manifest["feature_columns"] = [*manifest["feature_columns"], "split"]
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V4.6 feature_columns mismatch")


def test_validator_v4_6_rejects_unknown_model(valid_v4_6_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, _scores_report = valid_v4_6_manifest_report
    manifest["models"] = [*manifest["models"], "random_forest"]
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V4.6 models mismatch")


def test_validator_v4_6_rejects_output_trading_signal_column(valid_score_frame_v4_6: pd.DataFrame) -> None:
    valid_score_frame_v4_6["trading_signal"] = "none"
    errors = _validate_score_frame_schema_only(valid_score_frame_v4_6, "5m")
    assert _errors_contain(errors, "V4.6 score schema mismatch for 5m")


def test_validator_v4_6_rejects_output_order_column(valid_score_frame_v4_6: pd.DataFrame) -> None:
    valid_score_frame_v4_6["order"] = "none"
    errors = _validate_score_frame_schema_only(valid_score_frame_v4_6, "5m")
    assert _errors_contain(errors, "V4.6 score schema mismatch for 5m")


def test_validator_v4_6_rejects_output_pnl_column(valid_score_frame_v4_6: pd.DataFrame) -> None:
    valid_score_frame_v4_6["pnl"] = 0.0
    errors = _validate_score_frame_schema_only(valid_score_frame_v4_6, "5m")
    assert _errors_contain(errors, "V4.6 score schema mismatch for 5m")


def test_validator_v4_6_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v4_6_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V4.6 artifact detected")


def test_validator_v4_6_rejects_strategy_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/strategies/strategy.json")
    errors = _find_forbidden_v4_6_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V4.6 artifact detected")


def test_validator_v4_6_rejects_orders_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "orders/order.json")
    errors = _find_forbidden_v4_6_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V4.6 artifact detected")


def test_validator_v4_6_rejects_model_pickle_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v4_6/ml/offline_research/model.pkl")
    errors = _find_forbidden_v4_6_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V4.6 artifact detected")


def test_validator_v4_6_rejects_report_json_lie(valid_v4_6_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, report, _scores_report = valid_v4_6_manifest_report
    report["metrics"] = {}
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V4.6 quality report mismatch")


def test_validator_v4_6_rejects_manifest_unexpected_key(valid_v4_6_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, _scores_report = valid_v4_6_manifest_report
    manifest["strategy_validated"] = True
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V4.6 manifest unexpected keys")


def test_validator_v4_6_rejects_report_unexpected_key(valid_v4_6_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, report, _scores_report = valid_v4_6_manifest_report
    report["claim"] = "strategy validated"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V4.6 quality report unexpected keys")


def test_validator_v4_6_rejects_scores_report_lie(valid_v4_6_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, scores_report = valid_v4_6_manifest_report
    scores_report["metrics"] = {}
    errors = _validate_scores_report(manifest, scores_report)
    assert _errors_contain(errors, "V4.6 scores report mismatch")


def test_validator_v4_6_rejects_markdown_strategy_validated_claim() -> None:
    errors = validate_markdown_forbidden_claims("Rapport V4.6.\nStrategy validated.\n", "V4.6 Markdown report")
    assert _errors_contain(errors, "V4.6 Markdown report contains forbidden claim")


def test_validator_v4_6_rejects_safety_flag_trading_true(valid_v4_6_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v4_6_manifest_report, "trading_enabled", True))
    assert _errors_contain(errors, "V4.6 safety flag trading_enabled must be False")


def test_validator_v4_6_rejects_safety_flag_backtest_true(valid_v4_6_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v4_6_manifest_report, "backtest_enabled", True))
    assert _errors_contain(errors, "V4.6 safety flag backtest_enabled must be False")


def test_validator_v4_6_rejects_safety_flag_strategy_true(valid_v4_6_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v4_6_manifest_report, "strategy_enabled", True))
    assert _errors_contain(errors, "V4.6 safety flag strategy_enabled must be False")


def test_validator_v4_6_rejects_safety_flag_execution_true(valid_v4_6_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v4_6_manifest_report, "execution_enabled", True))
    assert _errors_contain(errors, "V4.6 safety flag execution_enabled must be False")


def test_validator_v4_6_rejects_trading_metric_in_metrics() -> None:
    errors = _scan_metrics_for_forbidden_terms({"1m.model.test": {"sharpe": 1.0}})
    assert _errors_contain(errors, "V4.6 metrics contain forbidden trading metric")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mutated_safety(bundle: tuple[dict[str, Any], dict[str, Any], dict[str, Any]], key: str, value: Any) -> dict[str, Any]:
    manifest, _report, _scores_report = bundle
    safety = deepcopy(manifest["safety"])
    safety[key] = value
    return safety


def _touch_forbidden(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)

from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.ml.multi_day import run_multi_day_offline_ml_research_v3_3
from galapagos.ml.multi_day_validation import (
    _find_forbidden_v3_3_artifacts,
    _scan_metrics_for_forbidden_terms,
    _validate_manifest_structure,
    _validate_report,
    _validate_safety,
    _validate_score_frame_schema_only,
    _validate_scores_report,
    validate_multi_day_offline_ml_research_v3_3,
)
from galapagos.ml.schemas import (
    MANIFEST_PATH_V3_3,
    REPORT_JSON_PATH_V3_3,
    SCORES_JSON_PATH_V3_3,
    get_multi_day_ml_score_path_v3_3,
)
from galapagos.validation.safety import validate_markdown_forbidden_claims


@pytest.fixture(scope="session")
def valid_v3_3_template_bundle(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    root = tmp_path_factory.mktemp("valid_v3_3_template")
    workspace = Path(__file__).resolve().parents[2]
    for relative in [
        "data/research/v3_0",
        "data/research/v3_1",
        "data/research/v3_2",
        "reports/manifests",
        "reports/datasets",
        "docs",
    ]:
        _copy_tree(workspace / relative, root / relative)
    run_multi_day_offline_ml_research_v3_3(root, validate_dataset=True)
    result = validate_multi_day_offline_ml_research_v3_3(root)
    assert result["passed"], result["errors"]
    return {"root": root, "validation_result": result}


@pytest.fixture(scope="session")
def valid_v3_3_template(valid_v3_3_template_bundle: dict[str, Any]) -> Path:
    return valid_v3_3_template_bundle["root"]


@pytest.fixture(scope="session")
def valid_v3_3_template_validation_result(valid_v3_3_template_bundle: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(valid_v3_3_template_bundle["validation_result"])


@pytest.fixture()
def valid_v3_3_project(tmp_path: Path, valid_v3_3_template: Path) -> Path:
    destination = tmp_path / "project"
    shutil.copytree(valid_v3_3_template, destination)
    return destination


@pytest.fixture()
def valid_v3_3_manifest_report(valid_v3_3_template: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        deepcopy(_load(valid_v3_3_template / MANIFEST_PATH_V3_3)),
        deepcopy(_load(valid_v3_3_template / REPORT_JSON_PATH_V3_3)),
        deepcopy(_load(valid_v3_3_template / SCORES_JSON_PATH_V3_3)),
    )


@pytest.fixture()
def valid_score_frame_v3_3(valid_v3_3_template: Path) -> pd.DataFrame:
    return pd.read_parquet(get_multi_day_ml_score_path_v3_3(valid_v3_3_template, "5m")).copy()


def test_validator_v3_3_accepts_valid_offline_ml_research(valid_v3_3_template_validation_result: dict[str, Any]) -> None:
    result = valid_v3_3_template_validation_result
    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v3_3_rejects_forbidden_future_feature(valid_v3_3_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, _scores_report = valid_v3_3_manifest_report
    manifest["feature_columns"] = [*manifest["feature_columns"], "future_log_return_h1"]
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V3.3 feature_columns mismatch")
    assert _errors_contain(errors, "V3.3 forbidden feature columns")


def test_validator_v3_3_rejects_forbidden_label_feature(valid_v3_3_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, _scores_report = valid_v3_3_manifest_report
    manifest["feature_columns"] = [*manifest["feature_columns"], "label_valid_h1"]
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V3.3 feature_columns mismatch")


def test_validator_v3_3_rejects_forbidden_split_feature(valid_v3_3_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, _scores_report = valid_v3_3_manifest_report
    manifest["feature_columns"] = [*manifest["feature_columns"], "split"]
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V3.3 feature_columns mismatch")


def test_validator_v3_3_rejects_unknown_model(valid_v3_3_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, _scores_report = valid_v3_3_manifest_report
    manifest["models"] = [*manifest["models"], "random_forest"]
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V3.3 models mismatch")


def test_validator_v3_3_rejects_output_trading_signal_column(valid_score_frame_v3_3: pd.DataFrame) -> None:
    valid_score_frame_v3_3["trading_signal"] = "none"
    errors = _validate_score_frame_schema_only(valid_score_frame_v3_3, "5m")
    assert _errors_contain(errors, "V3.3 score schema mismatch for 5m")


def test_validator_v3_3_rejects_output_order_column(valid_score_frame_v3_3: pd.DataFrame) -> None:
    valid_score_frame_v3_3["order"] = "none"
    errors = _validate_score_frame_schema_only(valid_score_frame_v3_3, "5m")
    assert _errors_contain(errors, "V3.3 score schema mismatch for 5m")


def test_validator_v3_3_rejects_output_pnl_column(valid_score_frame_v3_3: pd.DataFrame) -> None:
    valid_score_frame_v3_3["pnl"] = 0.0
    errors = _validate_score_frame_schema_only(valid_score_frame_v3_3, "5m")
    assert _errors_contain(errors, "V3.3 score schema mismatch for 5m")


def test_validator_v3_3_rejects_backtest_report_created(valid_v3_3_project: Path) -> None:
    path = valid_v3_3_project / "reports/backtests/not_named_backtest_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    errors = _find_forbidden_v3_3_artifacts(valid_v3_3_project)
    assert _errors_contain(errors, "Forbidden V3.3 artifact detected")


def test_validator_v3_3_rejects_strategy_report_created(valid_v3_3_project: Path) -> None:
    path = valid_v3_3_project / "reports/strategies/strategy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    errors = _find_forbidden_v3_3_artifacts(valid_v3_3_project)
    assert _errors_contain(errors, "Forbidden V3.3 artifact detected")


def test_validator_v3_3_rejects_orders_directory_created(valid_v3_3_project: Path) -> None:
    path = valid_v3_3_project / "orders/order.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    errors = _find_forbidden_v3_3_artifacts(valid_v3_3_project)
    assert _errors_contain(errors, "Forbidden V3.3 artifact detected")


def test_validator_v3_3_rejects_model_pickle_created(valid_v3_3_project: Path) -> None:
    path = valid_v3_3_project / "data/research/v3_3/ml/offline_research/model.pkl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"not-a-model")
    errors = _find_forbidden_v3_3_artifacts(valid_v3_3_project)
    assert _errors_contain(errors, "Forbidden V3.3 artifact detected")


def test_validator_v3_3_rejects_report_json_lie(valid_v3_3_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, report, _scores_report = valid_v3_3_manifest_report
    report["metrics"] = {}
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V3.3 quality report mismatch")


def test_validator_v3_3_rejects_manifest_unexpected_key(valid_v3_3_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, _scores_report = valid_v3_3_manifest_report
    manifest["strategy_validated"] = True
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V3.3 manifest unexpected keys")


def test_validator_v3_3_rejects_report_unexpected_key(valid_v3_3_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, report, _scores_report = valid_v3_3_manifest_report
    report["claim"] = "strategy validated"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V3.3 quality report unexpected keys")


def test_validator_v3_3_rejects_scores_report_lie(valid_v3_3_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report, scores_report = valid_v3_3_manifest_report
    scores_report["metrics"] = {}
    errors = _validate_scores_report(manifest, scores_report)
    assert _errors_contain(errors, "V3.3 scores report mismatch")


def test_validator_v3_3_rejects_markdown_strategy_validated_claim() -> None:
    errors = validate_markdown_forbidden_claims("Rapport V3.3.\nStrategy validated.\n", "V3.3 Markdown report")
    assert _errors_contain(errors, "V3.3 Markdown report contains forbidden claim")


def test_validator_v3_3_rejects_safety_flag_trading_true(valid_v3_3_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v3_3_manifest_report, "trading_enabled", True))
    assert _errors_contain(errors, "V3.3 safety flag trading_enabled must be False")


def test_validator_v3_3_rejects_safety_flag_backtest_true(valid_v3_3_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v3_3_manifest_report, "backtest_enabled", True))
    assert _errors_contain(errors, "V3.3 safety flag backtest_enabled must be False")


def test_validator_v3_3_rejects_safety_flag_strategy_true(valid_v3_3_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v3_3_manifest_report, "strategy_enabled", True))
    assert _errors_contain(errors, "V3.3 safety flag strategy_enabled must be False")


def test_validator_v3_3_rejects_safety_flag_execution_true(valid_v3_3_manifest_report: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v3_3_manifest_report, "execution_enabled", True))
    assert _errors_contain(errors, "V3.3 safety flag execution_enabled must be False")


def test_validator_v3_3_rejects_trading_metric_in_metrics() -> None:
    errors = _scan_metrics_for_forbidden_terms({"1m.model.test": {"sharpe": 1.0}})
    assert _errors_contain(errors, "V3.3 metrics contain forbidden trading metric")


def _copy_tree(src: Path, dest: Path) -> None:
    if not src.exists():
        return
    for item in src.rglob("*"):
        if item.is_file() and "__pycache__" not in item.parts and ".pytest_cache" not in item.parts:
            target = dest / item.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mutated_safety(bundle: tuple[dict[str, Any], dict[str, Any], dict[str, Any]], key: str, value: Any) -> dict[str, Any]:
    manifest, _report, _scores_report = bundle
    safety = deepcopy(manifest["safety"])
    safety[key] = value
    return safety


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)

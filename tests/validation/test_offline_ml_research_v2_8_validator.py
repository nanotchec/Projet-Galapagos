from __future__ import annotations

import json
import shutil
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.ml.schemas import MANIFEST_PATH, REPORT_JSON_PATH, REPORT_MD_PATH, TARGET_TIMEFRAMES, get_ml_score_path
from galapagos.ml.validation import (
    _find_forbidden_artifacts,
    _scan_metrics_for_forbidden_terms,
    _validate_manifest_structure,
    _validate_report,
    _validate_safety,
    _validate_timeframe,
    validate_offline_ml_research_v2_8,
)
from galapagos.validation.safety import validate_markdown_forbidden_claims

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from run_offline_ml_research_v2_8 import run_offline_ml_research_v2_8


@pytest.fixture(scope="session")
def valid_v2_8_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("valid_v2_8_template")
    workspace = Path(__file__).resolve().parents[2]
    for relative in [
        "data/raw/public_market",
        "data/silver/market_data/ohlcv",
        "data/gold/features",
        "data/gold/labels",
        "data/gold/datasets/offline_supervised",
        "reports/manifests",
        "reports/data_quality",
        "reports/features",
        "reports/labels",
        "reports/datasets",
    ]:
        _copy_tree(workspace / relative, root / relative)
    run_offline_ml_research_v2_8(root)
    result = validate_offline_ml_research_v2_8(root)
    assert result["passed"], result["errors"]
    return root


@pytest.fixture()
def valid_v2_8_project(tmp_path: Path, valid_v2_8_template: Path) -> Path:
    destination = tmp_path / "project"
    shutil.copytree(valid_v2_8_template, destination)
    return destination


@pytest.fixture()
def valid_v2_8_manifest_report(valid_v2_8_template: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(valid_v2_8_template / MANIFEST_PATH)), deepcopy(_load(valid_v2_8_template / REPORT_JSON_PATH))


def test_validator_v2_8_accepts_valid_offline_ml_research(valid_v2_8_project: Path) -> None:
    result = validate_offline_ml_research_v2_8(valid_v2_8_project)
    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v2_8_rejects_forbidden_future_feature(valid_v2_8_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v2_8_manifest_report
    manifest["feature_columns"] = [*manifest["feature_columns"], "future_log_return_h1"]
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V2.8 feature_columns mismatch")


def test_validator_v2_8_rejects_forbidden_label_feature(valid_v2_8_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v2_8_manifest_report
    manifest["feature_columns"] = [*manifest["feature_columns"], "label_valid_h1"]
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V2.8 feature_columns mismatch")


def test_validator_v2_8_rejects_forbidden_split_feature(valid_v2_8_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v2_8_manifest_report
    manifest["feature_columns"] = [*manifest["feature_columns"], "split"]
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V2.8 feature_columns mismatch")


def test_validator_v2_8_rejects_unknown_model(valid_v2_8_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v2_8_manifest_report
    manifest["models"] = [*manifest["models"], "random_forest"]
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V2.8 models mismatch")


def test_validator_v2_8_rejects_output_trading_signal_column(valid_v2_8_project: Path) -> None:
    errors = _mutate_score_column_and_validate(valid_v2_8_project, "5m", "trading_signal", 0.0)
    assert _errors_contain(errors, "V2.8 score schema mismatch for 5m")


def test_validator_v2_8_rejects_output_order_column(valid_v2_8_project: Path) -> None:
    errors = _mutate_score_column_and_validate(valid_v2_8_project, "5m", "order", "none")
    assert _errors_contain(errors, "V2.8 score schema mismatch for 5m")


def test_validator_v2_8_rejects_output_pnl_column(valid_v2_8_project: Path) -> None:
    errors = _mutate_score_column_and_validate(valid_v2_8_project, "5m", "pnl", 0.0)
    assert _errors_contain(errors, "V2.8 score schema mismatch for 5m")


def test_validator_v2_8_rejects_backtest_report_created(valid_v2_8_project: Path) -> None:
    path = valid_v2_8_project / "reports/backtests/backtest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    errors = _find_forbidden_artifacts(valid_v2_8_project)
    assert _errors_contain(errors, "Forbidden V2.8 artifact detected")


def test_validator_v2_8_rejects_strategy_report_created(valid_v2_8_project: Path) -> None:
    path = valid_v2_8_project / "reports/strategies/strategy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    errors = _find_forbidden_artifacts(valid_v2_8_project)
    assert _errors_contain(errors, "Forbidden V2.8 artifact detected")


def test_validator_v2_8_rejects_orders_directory_created(valid_v2_8_project: Path) -> None:
    path = valid_v2_8_project / "orders/order.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    errors = _find_forbidden_artifacts(valid_v2_8_project)
    assert _errors_contain(errors, "Forbidden V2.8 artifact detected")


def test_validator_v2_8_rejects_report_json_lie(valid_v2_8_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v2_8_manifest_report
    report["metrics"] = {}
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V2.8 quality report mismatch")


def test_validator_v2_8_rejects_manifest_unexpected_key(valid_v2_8_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v2_8_manifest_report
    manifest["strategy_validated"] = True
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V2.8 manifest unexpected keys")


def test_validator_v2_8_rejects_report_unexpected_key(valid_v2_8_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v2_8_manifest_report
    report["claim"] = "strategy validated"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V2.8 quality report unexpected keys")


def test_validator_v2_8_rejects_markdown_strategy_validated_claim() -> None:
    errors = validate_markdown_forbidden_claims("Rapport V2.8.\nStrategy validated.\n", "V2.8 Markdown report")
    assert _errors_contain(errors, "V2.8 Markdown report contains forbidden claim")


def test_validator_v2_8_rejects_safety_flag_trading_true(valid_v2_8_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v2_8_manifest_report, "trading_enabled", True))
    assert _errors_contain(errors, "V2.8 safety flag trading_enabled must be False")


def test_validator_v2_8_rejects_safety_flag_backtest_true(valid_v2_8_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v2_8_manifest_report, "backtest_enabled", True))
    assert _errors_contain(errors, "V2.8 safety flag backtest_enabled must be False")


def test_validator_v2_8_rejects_safety_flag_strategy_true(valid_v2_8_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v2_8_manifest_report, "strategy_enabled", True))
    assert _errors_contain(errors, "V2.8 safety flag strategy_enabled must be False")


def test_validator_v2_8_rejects_safety_flag_execution_true(valid_v2_8_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v2_8_manifest_report, "execution_enabled", True))
    assert _errors_contain(errors, "V2.8 safety flag execution_enabled must be False")


def test_validator_v2_8_rejects_trading_metric_in_metrics() -> None:
    errors = _scan_metrics_for_forbidden_terms({"1m.model.test": {"sharpe": 1.0}})
    assert _errors_contain(errors, "V2.8 metrics contain forbidden trading metric")


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


def _dump(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _mutated_safety(manifest_report: tuple[dict[str, Any], dict[str, Any]], key: str, value: bool) -> dict[str, Any]:
    manifest, _report = manifest_report
    safety = deepcopy(manifest["safety"])
    safety[key] = value
    return safety


def _mutate_score_column_and_validate(root: Path, timeframe: str, column: str, value: Any) -> list[str]:
    path = get_ml_score_path(root, timeframe)
    frame = pd.read_parquet(path)
    frame[column] = value
    frame.to_parquet(path, index=False)
    _sync_score_output(root, timeframe)
    return _validate_single_timeframe(root, timeframe)


def _sync_score_output(root: Path, timeframe: str) -> None:
    manifest = _load(root / MANIFEST_PATH)
    path = get_ml_score_path(root, timeframe)
    manifest["outputs"][timeframe]["sha256"] = sha256_file(path)
    manifest["outputs"][timeframe]["bytes"] = path.stat().st_size
    manifest["outputs"][timeframe]["rows"] = len(pd.read_parquet(path))
    _dump(root / MANIFEST_PATH, manifest)
    _dump(root / REPORT_JSON_PATH, manifest)


def _validate_single_timeframe(root: Path, timeframe: str) -> list[str]:
    manifest = _load(root / MANIFEST_PATH)
    physical_quality: dict[str, dict[str, Any]] = {}
    all_scores: list[pd.DataFrame] = []
    return _validate_timeframe(root, manifest, timeframe, physical_quality, all_scores)


def _errors_contain(errors: list[str], text: str) -> bool:
    return any(text in error for error in errors)

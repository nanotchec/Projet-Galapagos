from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from galapagos.ml.robustness import MANIFEST_PATH_V3_4, REPORT_JSON_PATH_V3_4
from galapagos.ml.robustness_validation import (
    _find_forbidden_v3_4_artifacts,
    _scan_metrics_for_forbidden_terms,
    _validate_findings,
    _validate_manifest_structure,
    _validate_report,
    _validate_safety,
    validate_multi_day_ml_robustness_v3_4,
)
from galapagos.validation.safety import validate_markdown_forbidden_claims


@pytest.fixture()
def valid_v3_4_manifest_report() -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(__file__).resolve().parents[2]
    return (
        deepcopy(_load(root / MANIFEST_PATH_V3_4)),
        deepcopy(_load(root / REPORT_JSON_PATH_V3_4)),
    )


def test_validator_v3_4_accepts_valid_robustness_report() -> None:
    root = Path(__file__).resolve().parents[2]
    result = validate_multi_day_ml_robustness_v3_4(root)

    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v3_4_rejects_strategy_validated_true(valid_v3_4_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v3_4_manifest_report
    manifest["findings"]["strategy_validated"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V3.4 finding strategy_validated must be False")


def test_validator_v3_4_rejects_robust_edge_claimed_true(valid_v3_4_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v3_4_manifest_report
    manifest["findings"]["robust_edge_claimed"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V3.4 finding robust_edge_claimed must be False")


def test_validator_v3_4_rejects_backtest_performed_true(valid_v3_4_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v3_4_manifest_report
    manifest["findings"]["backtest_performed"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V3.4 finding backtest_performed must be False")


def test_validator_v3_4_rejects_actionable_signal_produced_true(valid_v3_4_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v3_4_manifest_report
    manifest["findings"]["actionable_signal_produced"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V3.4 finding actionable_signal_produced must be False")


def test_validator_v3_4_rejects_backtest_report_created(tmp_path: Path) -> None:
    path = tmp_path / "reports/backtests/not_named_report.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")
    errors = _find_forbidden_v3_4_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.4 artifact detected")


def test_validator_v3_4_rejects_strategy_report_created(tmp_path: Path) -> None:
    path = tmp_path / "reports/strategies/strategy.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")
    errors = _find_forbidden_v3_4_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.4 artifact detected")


def test_validator_v3_4_rejects_orders_directory_created(tmp_path: Path) -> None:
    path = tmp_path / "orders/order.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")
    errors = _find_forbidden_v3_4_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.4 artifact detected")


def test_validator_v3_4_rejects_model_pickle_created(tmp_path: Path) -> None:
    path = tmp_path / "models/model.pkl"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"not-a-model")
    errors = _find_forbidden_v3_4_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.4 artifact detected")


def test_validator_v3_4_rejects_sharpe_metric() -> None:
    errors = _scan_metrics_for_forbidden_terms({"model": {"sharpe": 1.0}})
    assert _errors_contain(errors, "V3.4 metrics contain forbidden trading metric: sharpe")


def test_validator_v3_4_rejects_markdown_strategy_validated_claim() -> None:
    errors = validate_markdown_forbidden_claims("Rapport V3.4.\nStrategy validated.\n", "V3.4 Markdown report")
    assert _errors_contain(errors, "V3.4 Markdown report contains forbidden claim")


def test_validator_v3_4_rejects_safety_flag_trading_true(valid_v3_4_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v3_4_manifest_report, "trading_enabled", True))
    assert _errors_contain(errors, "V3.4 safety flag trading_enabled must be False")


def test_validator_v3_4_rejects_safety_flag_backtest_true(valid_v3_4_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v3_4_manifest_report, "backtest_enabled", True))
    assert _errors_contain(errors, "V3.4 safety flag backtest_enabled must be False")


def test_validator_v3_4_rejects_safety_flag_strategy_true(valid_v3_4_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v3_4_manifest_report, "strategy_enabled", True))
    assert _errors_contain(errors, "V3.4 safety flag strategy_enabled must be False")


def test_validator_v3_4_rejects_safety_flag_execution_true(valid_v3_4_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v3_4_manifest_report, "execution_enabled", True))
    assert _errors_contain(errors, "V3.4 safety flag execution_enabled must be False")


def test_validator_v3_4_rejects_manifest_unexpected_key(valid_v3_4_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v3_4_manifest_report
    manifest["extra_claim"] = "not allowed"
    errors = _validate_manifest_structure(manifest)
    assert _errors_contain(errors, "V3.4 manifest unexpected keys")


def test_validator_v3_4_rejects_report_json_lie(valid_v3_4_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v3_4_manifest_report
    report["findings"]["robust_edge_claimed"] = True
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V3.4 report JSON mismatch")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mutated_safety(bundle: tuple[dict[str, Any], dict[str, Any]], key: str, value: Any) -> dict[str, Any]:
    manifest, _report = bundle
    safety = deepcopy(manifest["safety"])
    safety[key] = value
    return safety


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)

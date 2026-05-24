from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from galapagos.ml.max_history_robustness import MANIFEST_PATH_V5_5, REPORT_JSON_PATH_V5_5
from galapagos.ml.max_history_robustness_validation import (
    _find_forbidden_v5_5_artifacts,
    _scan_metrics_for_forbidden_terms,
    _validate_findings,
    _validate_metric_value_bounds,
    _validate_safety,
    validate_max_history_ml_robustness_v5_5,
)
from galapagos.validation.safety import validate_markdown_forbidden_claims


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def valid_v5_5_manifest_report() -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(ROOT / MANIFEST_PATH_V5_5)), deepcopy(_load(ROOT / REPORT_JSON_PATH_V5_5))


def test_validator_v5_5_accepts_valid_robustness_report() -> None:
    result = validate_max_history_ml_robustness_v5_5(ROOT)

    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v5_5_rejects_strategy_validated_true(valid_v5_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v5_5_manifest_report
    manifest["findings"]["strategy_validated"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V5.5 finding strategy_validated must be False")


def test_validator_v5_5_rejects_robust_edge_claimed_true(valid_v5_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v5_5_manifest_report
    manifest["findings"]["robust_edge_claimed"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V5.5 finding robust_edge_claimed must be False")


def test_validator_v5_5_rejects_backtest_performed_true(valid_v5_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v5_5_manifest_report
    manifest["findings"]["backtest_performed"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V5.5 finding backtest_performed must be False")


def test_validator_v5_5_rejects_actionable_signal_produced_true(valid_v5_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v5_5_manifest_report
    manifest["findings"]["actionable_signal_produced"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V5.5 finding actionable_signal_produced must be False")


def test_validator_v5_5_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v5_5_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.5 artifact detected")


def test_validator_v5_5_rejects_strategy_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/strategies/strategy.json")
    errors = _find_forbidden_v5_5_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.5 artifact detected")


def test_validator_v5_5_rejects_orders_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "orders/order.json")
    errors = _find_forbidden_v5_5_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.5 artifact detected")


def test_validator_v5_5_rejects_model_pickle_created(tmp_path: Path) -> None:
    path = tmp_path / "models/model.pkl"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"not-a-model")
    errors = _find_forbidden_v5_5_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.5 artifact detected")


def test_validator_v5_5_rejects_sharpe_metric() -> None:
    errors = _scan_metrics_for_forbidden_terms({"model": {"sharpe": 1.0}})
    assert _errors_contain(errors, "V5.5 metrics contain forbidden trading metric: sharpe")


def test_validator_v5_5_rejects_accuracy_out_of_bounds(valid_v5_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v5_5_manifest_report
    first_key = next(iter(manifest["analyses"]["baseline_delta"]))
    manifest["analyses"]["baseline_delta"][first_key]["accuracy"] = 999
    errors = _validate_metric_value_bounds(manifest["analyses"])
    assert _errors_contain(errors, "V5.5 metric bound violation")


def test_validator_v5_5_rejects_gap_out_of_bounds(valid_v5_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v5_5_manifest_report
    first_key = next(iter(manifest["analyses"]["split_stability"]))
    manifest["analyses"]["split_stability"][first_key]["validation_test_accuracy_gap"] = 9
    errors = _validate_metric_value_bounds(manifest["analyses"])
    assert _errors_contain(errors, "V5.5 metric bound violation")


def test_validator_v5_5_rejects_markdown_strategy_validated_claim() -> None:
    errors = validate_markdown_forbidden_claims("Rapport V5.5.\nStrategy validated.\n", "V5.5 Markdown report")
    assert _errors_contain(errors, "V5.5 Markdown report contains forbidden claim")


def test_validator_v5_5_rejects_safety_flag_trading_true(valid_v5_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v5_5_manifest_report, "trading_enabled", True))
    assert _errors_contain(errors, "V5.5 safety flag trading_enabled must be False")


def test_validator_v5_5_rejects_safety_flag_backtest_true(valid_v5_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v5_5_manifest_report, "backtest_enabled", True))
    assert _errors_contain(errors, "V5.5 safety flag backtest_enabled must be False")


def test_validator_v5_5_rejects_safety_flag_strategy_true(valid_v5_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v5_5_manifest_report, "strategy_enabled", True))
    assert _errors_contain(errors, "V5.5 safety flag strategy_enabled must be False")


def test_validator_v5_5_rejects_safety_flag_execution_true(valid_v5_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v5_5_manifest_report, "execution_enabled", True))
    assert _errors_contain(errors, "V5.5 safety flag execution_enabled must be False")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _touch_forbidden(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")


def _mutated_safety(bundle: tuple[dict[str, Any], dict[str, Any]], key: str, value: Any) -> dict[str, Any]:
    manifest, _report = bundle
    safety = deepcopy(manifest["safety"])
    safety[key] = value
    return safety


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)

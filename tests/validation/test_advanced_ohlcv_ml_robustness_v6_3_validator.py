from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from galapagos.ml.advanced_ohlcv_robustness import MANIFEST_PATH_V6_3, REPORT_JSON_PATH_V6_3
from galapagos.ml.advanced_ohlcv_robustness_validation import (
    DOC_PATH_V6_3,
    REPORT_MD_PATH_V6_3,
    _find_forbidden_v6_3_artifacts,
    _scan_metrics_for_forbidden_terms,
    _validate_findings,
    _validate_markdown,
    _validate_metric_value_bounds,
    _validate_safety,
    validate_advanced_ohlcv_ml_robustness_v6_3,
)
from galapagos.validation.safety import validate_markdown_forbidden_claims


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def valid_v6_3_manifest_report() -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(ROOT / MANIFEST_PATH_V6_3)), deepcopy(_load(ROOT / REPORT_JSON_PATH_V6_3))


def test_validator_v6_3_accepts_valid_robustness_report() -> None:
    result = validate_advanced_ohlcv_ml_robustness_v6_3(ROOT)

    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v6_3_rejects_strategy_validated_true(valid_v6_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v6_3_manifest_report
    manifest["findings"]["strategy_validated"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V6.3 finding strategy_validated must be False")


def test_validator_v6_3_rejects_robust_edge_claimed_true(valid_v6_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v6_3_manifest_report
    manifest["findings"]["robust_edge_claimed"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V6.3 finding robust_edge_claimed must be False")


def test_validator_v6_3_rejects_advanced_features_validated_for_trading_true(
    valid_v6_3_manifest_report: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    manifest, _report = valid_v6_3_manifest_report
    manifest["findings"]["advanced_features_validated_for_trading"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V6.3 finding advanced_features_validated_for_trading must be False")


def test_validator_v6_3_rejects_backtest_performed_true(valid_v6_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v6_3_manifest_report
    manifest["findings"]["backtest_performed"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V6.3 finding backtest_performed must be False")


def test_validator_v6_3_rejects_actionable_signal_produced_true(valid_v6_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v6_3_manifest_report
    manifest["findings"]["actionable_signal_produced"] = True
    errors = _validate_findings(manifest["findings"])
    assert _errors_contain(errors, "V6.3 finding actionable_signal_produced must be False")


def test_validator_v6_3_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v6_3_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V6.3 artifact detected")


def test_validator_v6_3_rejects_strategy_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/strategies/strategy.json")
    errors = _find_forbidden_v6_3_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V6.3 artifact detected")


def test_validator_v6_3_rejects_orders_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "orders/order.json")
    errors = _find_forbidden_v6_3_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V6.3 artifact detected")


def test_validator_v6_3_rejects_model_pickle_created(tmp_path: Path) -> None:
    path = tmp_path / "models/model.pkl"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"not-a-model")
    errors = _find_forbidden_v6_3_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V6.3 artifact detected")


def test_validator_v6_3_rejects_sharpe_metric() -> None:
    errors = _scan_metrics_for_forbidden_terms({"model": {"sharpe": 1.0}})
    assert _errors_contain(errors, "V6.3 metrics contain forbidden trading metric: sharpe")


def test_validator_v6_3_rejects_accuracy_out_of_bounds(valid_v6_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v6_3_manifest_report
    first_key = next(iter(manifest["analyses"]["baseline_delta"]))
    manifest["analyses"]["baseline_delta"][first_key]["accuracy"] = 999
    errors = _validate_metric_value_bounds(manifest["analyses"])
    assert _errors_contain(errors, "V6.3 metric bound violation")


def test_validator_v6_3_rejects_gap_out_of_bounds(valid_v6_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v6_3_manifest_report
    first_key = next(iter(manifest["analyses"]["split_stability"]))
    manifest["analyses"]["split_stability"][first_key]["validation_test_accuracy_gap"] = 9
    errors = _validate_metric_value_bounds(manifest["analyses"])
    assert _errors_contain(errors, "V6.3 metric bound violation")


def test_validator_v6_3_rejects_markdown_strategy_validated_claim() -> None:
    errors = validate_markdown_forbidden_claims("Rapport V6.3.\nStrategy validated.\n", "V6.3 Markdown report")
    assert _errors_contain(errors, "V6.3 Markdown report contains forbidden claim")


def test_validator_v6_3_rejects_markdown_tradable_edge_confirmed_claim(tmp_path: Path) -> None:
    _write_v6_3_markdown_pair(tmp_path, "Rapport V6.3.\nTradable edge confirmed.\n")
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "tradable edge confirmed")


def test_validator_v6_3_rejects_safety_flag_trading_true(valid_v6_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v6_3_manifest_report, "trading_enabled", True))
    assert _errors_contain(errors, "V6.3 safety flag trading_enabled must be False")


def test_validator_v6_3_rejects_safety_flag_backtest_true(valid_v6_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v6_3_manifest_report, "backtest_enabled", True))
    assert _errors_contain(errors, "V6.3 safety flag backtest_enabled must be False")


def test_validator_v6_3_rejects_safety_flag_strategy_true(valid_v6_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v6_3_manifest_report, "strategy_enabled", True))
    assert _errors_contain(errors, "V6.3 safety flag strategy_enabled must be False")


def test_validator_v6_3_rejects_safety_flag_execution_true(valid_v6_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    errors = _validate_safety(_mutated_safety(valid_v6_3_manifest_report, "execution_enabled", True))
    assert _errors_contain(errors, "V6.3 safety flag execution_enabled must be False")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _touch_forbidden(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")


def _write_v6_3_markdown_pair(root: Path, text: str) -> None:
    for relative in [REPORT_MD_PATH_V6_3, DOC_PATH_V6_3]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _mutated_safety(bundle: tuple[dict[str, Any], dict[str, Any]], key: str, value: Any) -> dict[str, Any]:
    manifest, _report = bundle
    safety = deepcopy(manifest["safety"])
    safety[key] = value
    return safety


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)

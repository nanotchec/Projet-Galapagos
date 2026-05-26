from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from galapagos.features.ohlcv_trades_feature_audit_validation import (
    find_forbidden_v8_9_artifacts,
    validate_candidate_refined_feature_set_v8_9,
    validate_feature_audit_manifest_payload_v8_9,
    validate_feature_audit_markdown_v8_9,
    validate_ohlcv_trades_feature_audit_v8_9,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json"


def test_validator_v8_9_accepts_valid_feature_audit() -> None:
    result = validate_ohlcv_trades_feature_audit_v8_9(ROOT)

    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v8_9_rejects_forbidden_future_feature_selected() -> None:
    candidate = _candidate_with_selected("future_log_return_h1")

    errors = validate_candidate_refined_feature_set_v8_9(candidate)

    assert any("forbidden" in error or "outside allowed" in error for error in errors)


def test_validator_v8_9_rejects_forbidden_label_feature_selected() -> None:
    candidate = _candidate_with_selected("label_valid_h1")

    errors = validate_candidate_refined_feature_set_v8_9(candidate)

    assert any("forbidden" in error or "outside allowed" in error for error in errors)


def test_validator_v8_9_rejects_forbidden_signal_feature_selected() -> None:
    candidate = _candidate_with_selected("trading_signal")

    errors = validate_candidate_refined_feature_set_v8_9(candidate)

    assert any("forbidden" in error or "outside allowed" in error for error in errors)


def test_validator_v8_9_rejects_feature_set_validated_for_trading_true() -> None:
    payload = deepcopy(_load_manifest())
    payload["findings"]["feature_set_validated_for_trading"] = True

    errors = validate_feature_audit_manifest_payload_v8_9(payload)

    assert any("feature_set_validated_for_trading" in error for error in errors)


def test_validator_v8_9_rejects_strategy_validated_true() -> None:
    payload = deepcopy(_load_manifest())
    payload["findings"]["strategy_validated"] = True

    errors = validate_feature_audit_manifest_payload_v8_9(payload)

    assert any("strategy_validated" in error for error in errors)


def test_validator_v8_9_rejects_backtest_performed_true() -> None:
    payload = deepcopy(_load_manifest())
    payload["findings"]["backtest_performed"] = True

    errors = validate_feature_audit_manifest_payload_v8_9(payload)

    assert any("backtest_performed" in error for error in errors)


def test_validator_v8_9_rejects_actionable_signal_produced_true() -> None:
    payload = deepcopy(_load_manifest())
    payload["findings"]["actionable_signal_produced"] = True

    errors = validate_feature_audit_manifest_payload_v8_9(payload)

    assert any("actionable_signal_produced" in error for error in errors)


def test_validator_v8_9_rejects_dataset_created(tmp_path: Path) -> None:
    (tmp_path / "data/research/v8_9/datasets").mkdir(parents=True)

    errors = find_forbidden_v8_9_artifacts(tmp_path)

    assert any("data/research/v8_9/datasets" in error for error in errors)


def test_validator_v8_9_rejects_ml_created(tmp_path: Path) -> None:
    (tmp_path / "data/research/v8_9/ml").mkdir(parents=True)

    errors = find_forbidden_v8_9_artifacts(tmp_path)

    assert any("data/research/v8_9/ml" in error for error in errors)


def test_validator_v8_9_rejects_backtest_report_created(tmp_path: Path) -> None:
    (tmp_path / "reports/backtests").mkdir(parents=True)

    errors = find_forbidden_v8_9_artifacts(tmp_path)

    assert any("reports/backtests" in error for error in errors)


def test_validator_v8_9_rejects_orders_directory_created(tmp_path: Path) -> None:
    (tmp_path / "orders").mkdir()

    errors = find_forbidden_v8_9_artifacts(tmp_path)

    assert any("orders" in error for error in errors)


def test_validator_v8_9_rejects_model_pickle_created(tmp_path: Path) -> None:
    model_path = tmp_path / "models/model.pkl"
    model_path.parent.mkdir()
    model_path.write_bytes(b"not-a-model")

    errors = find_forbidden_v8_9_artifacts(tmp_path)

    assert any("model.pkl" in error for error in errors)


def test_validator_v8_9_rejects_markdown_strategy_validated_claim() -> None:
    text = "V8.9 ne produit aucun backtest. V8.9 ne produit aucun signal de trading. V8.9 ne produit aucun ordre. strategy validated."

    errors = validate_feature_audit_markdown_v8_9(text, "markdown")

    assert any("strategy validated" in error for error in errors)


def test_validator_v8_9_rejects_markdown_tradable_edge_confirmed_claim() -> None:
    text = "V8.9 ne valide aucune strategie. V8.9 ne produit aucun backtest. V8.9 ne produit aucun signal de trading. V8.9 ne produit aucun ordre. tradable edge confirmed."

    errors = validate_feature_audit_markdown_v8_9(text, "markdown")

    assert any("tradable edge confirmed" in error for error in errors)


def _candidate_with_selected(feature: str) -> dict[str, Any]:
    candidate = deepcopy(_load_manifest()["candidate_refined_feature_set"])
    candidate["selected_features"] = [*candidate["selected_features"], feature]
    candidate["selected_features_count"] = len(candidate["selected_features"])
    return candidate


def _load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

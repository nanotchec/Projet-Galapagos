from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from galapagos.features.refined_ohlcv_trades_validation import (
    validate_refined_feature_manifest_payload_v9_0,
    validate_refined_ohlcv_trades_feature_store_v9_0,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json"
SELECTION_PATH = ROOT / "reports/features/ohlcv_trades_feature_selection_v8_9.json"


def test_validator_v9_0_accepts_valid_refined_feature_store() -> None:
    result = validate_refined_ohlcv_trades_feature_store_v9_0(ROOT)

    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v9_0_rejects_wrong_selected_count() -> None:
    manifest = _manifest()
    selection = _selection()
    manifest["selected_features_count"] = 999

    errors = validate_refined_feature_manifest_payload_v9_0(manifest, selection)

    assert any("selected_features_count" in error for error in errors)


def test_validator_v9_0_rejects_forbidden_selected_feature() -> None:
    manifest = _manifest()
    selection = _selection()
    manifest["selected_features"] = [*manifest["selected_features"], "future_log_return_h1"]

    errors = validate_refined_feature_manifest_payload_v9_0(manifest, selection)

    assert any("selected_features" in error or "forbidden" in error for error in errors)


def test_validator_v9_0_rejects_safety_flag_trading_true() -> None:
    manifest = _manifest()
    selection = _selection()
    manifest["safety"]["trading_enabled"] = True

    errors = validate_refined_feature_manifest_payload_v9_0(manifest, selection)

    assert any("safety" in error for error in errors)


def test_validator_v9_0_rejects_dropped_features_absent_false() -> None:
    manifest = _manifest()
    selection = _selection()
    manifest["dropped_features_absent"] = False

    errors = validate_refined_feature_manifest_payload_v9_0(manifest, selection)

    assert any("dropped_features_absent" in error for error in errors)


def _manifest() -> dict:
    return deepcopy(json.loads(MANIFEST_PATH.read_text(encoding="utf-8")))


def _selection() -> dict:
    return json.loads(SELECTION_PATH.read_text(encoding="utf-8"))

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.features.ohlcv_trades_feature_selection import is_forbidden_feature_v8_9
from galapagos.features.ohlcv_trades_feature_selection_schemas import FEATURE_FAMILIES_V8_9


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json"


def test_feature_inventory_non_empty_v8_9() -> None:
    manifest = _load_manifest()

    assert manifest["feature_inventory"]
    assert manifest["feature_inventory"][0]["feature_name"]
    assert all("feature_family" in item for item in manifest["feature_inventory"])


def test_feature_inventory_has_expected_families_v8_9() -> None:
    manifest = _load_manifest()
    families = {item["feature_family"] for item in manifest["feature_inventory"]}

    assert {"ohlcv_base", "trade_aggregation", "taker_flow", "trade_intensity", "rolling_trade", "microstructure_proxy", "temporal", "audit"}.issubset(families)
    assert families.issubset(set(FEATURE_FAMILIES_V8_9))


def test_missingness_summary_contains_all_timeframes_v8_9() -> None:
    manifest = _load_manifest()

    assert set(manifest["missingness_summary"]["by_timeframe"]) == {"1m", "5m", "15m", "1h"}
    for timeframe, payload in manifest["missingness_summary"]["by_timeframe"].items():
        assert "agg_trade_count" in payload
        assert payload["agg_trade_count"]["null_count"] >= 0
        assert 0.0 <= payload["agg_trade_count"]["null_rate"] <= 1.0


def test_collinearity_clusters_have_representatives_v8_9() -> None:
    manifest = _load_manifest()
    clusters = manifest["collinearity_summary"]["feature_clusters"]

    assert clusters
    assert all(cluster["representative_feature"] in cluster["features"] for cluster in clusters)
    assert all(isinstance(cluster["redundant_features"], list) for cluster in clusters)


def test_candidate_refined_feature_set_non_empty_v8_9() -> None:
    manifest = _load_manifest()
    candidate = manifest["candidate_refined_feature_set"]

    assert candidate["selected_features_count"] == len(candidate["selected_features"])
    assert candidate["selected_features"]
    assert "close" in candidate["selected_features"]


def test_candidate_refined_feature_set_excludes_forbidden_columns_v8_9() -> None:
    manifest = _load_manifest()
    selected = manifest["candidate_refined_feature_set"]["selected_features"]

    assert not [feature for feature in selected if is_forbidden_feature_v8_9(feature)]
    assert "future_log_return_h1" not in selected
    assert "trading_signal" not in selected


def test_leakage_guard_passes_v8_9() -> None:
    manifest = _load_manifest()

    assert manifest["leakage_guard"]["passed"] is True
    assert manifest["leakage_guard"]["forbidden_features_present"] == []


def test_feature_set_not_validated_for_trading_v8_9() -> None:
    manifest = _load_manifest()
    findings = manifest["findings"]

    assert findings["feature_set_validated_for_trading"] is False
    assert findings["strategy_validated"] is False
    assert findings["backtest_performed"] is False
    assert findings["actionable_signal_produced"] is False


def _load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

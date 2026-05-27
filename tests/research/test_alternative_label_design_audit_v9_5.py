from __future__ import annotations

from pathlib import Path

from galapagos.research.alternative_label_design_audit_v9_5 import (
    ALLOWED_DECISIONS,
    build_alternative_label_design_audit_v9_5,
)
from galapagos.research.alternative_label_design_audit_v9_5_validation import validate_report_payload_v9_5


ROOT = Path(__file__).resolve().parents[2]


def test_alternative_label_design_audit_v9_5_builds_valid_payload() -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)

    assert payload["version"] == "V9.5"
    assert payload["decision_type"] == "alternative_label_design_audit"
    assert payload["v9_5_decision"]["decision"] in ALLOWED_DECISIONS
    assert validate_report_payload_v9_5(payload) == []


def test_alternative_label_design_audit_v9_5_preserves_v9_4_conservative_decision() -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)

    assert payload["source_decision"]["research_decision"] == "backtest_not_justified_refine_labels"
    assert payload["no_backtest_justified"] is True
    assert payload["v9_5_decision"]["must_not_run_backtest"] is True


def test_alternative_label_design_audit_v9_5_analyzes_current_target_and_shuffle_issue() -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)

    current = payload["current_label_analysis"]
    assert current["target_name"] == "up_down_flat_h1"
    assert current["label_shuffle_link"]["no_clear_edge_vs_shuffled_labels_count"] == 21
    assert set(current["timeframes"]) == {"1m", "5m", "15m", "1h"}


def test_alternative_label_design_audit_v9_5_catalog_contains_required_design_families() -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)

    families = {item["family_id"] for item in payload["alternative_label_design_catalog"]}

    assert "fixed_stricter_thresholds" in families
    assert "volatility_normalized_thresholds" in families
    assert "rolling_quantile_or_tertile_labels" in families
    assert "causal_multi_horizon_labels" in families


def test_alternative_label_design_audit_v9_5_recommends_future_label_factory_not_backtest() -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)

    assert payload["v9_5_decision"]["next_step"] == "V9.6 - Refined Label Factory Candidate"
    assert payload["v9_5_decision"]["decision"] != "limited_research_backtest_candidate"
    assert "backtest" not in payload["v9_5_decision"]["decision"]


def test_alternative_label_design_audit_v9_5_keeps_safety_findings_false() -> None:
    payload = build_alternative_label_design_audit_v9_5(ROOT)

    assert all(value is False for value in payload["findings"].values())
    assert payload["safety"]["trading_enabled"] is False
    assert payload["safety"]["paper_live_enabled"] is False
    assert payload["safety"]["orders_enabled"] is False
    assert payload["safety"]["backtest_enabled"] is False

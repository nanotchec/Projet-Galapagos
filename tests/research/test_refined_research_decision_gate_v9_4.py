from __future__ import annotations

from pathlib import Path

from galapagos.research.refined_research_decision_gate_v9_4 import (
    ALLOWED_RESEARCH_DECISIONS,
    build_refined_research_decision_gate_v9_4,
)
from galapagos.research.refined_research_decision_gate_v9_4_validation import validate_decision_payload_v9_4


ROOT = Path(__file__).resolve().parents[2]


def test_refined_decision_gate_v9_4_builds_research_only_payload() -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)

    assert payload["version"] == "V9.4"
    assert payload["decision_gate_type"] == "research_only"
    assert payload["research_decision"] in ALLOWED_RESEARCH_DECISIONS
    assert validate_decision_payload_v9_4(payload) == []


def test_refined_decision_gate_v9_4_is_conservative_with_current_evidence() -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)

    assert payload["research_decision"] == "backtest_not_justified_refine_labels"
    assert payload["baseline_assessment"]["backtest_not_justified"] is True
    assert payload["research_decision"] != "limited_research_backtest_candidate"


def test_refined_decision_gate_v9_4_preserves_label_shuffle_warning() -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)

    assert payload["label_shuffle_assessment"]["no_clear_edge_vs_shuffled_labels_count"] == 21
    assert payload["label_shuffle_assessment"]["falsification_clean"] is False
    assert payload["label_shuffle_assessment"]["backtest_not_justified_due_to_shuffle"] is True


def test_refined_decision_gate_v9_4_tracks_fold_concentration() -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)

    assert payload["fold_stability_assessment"]["fold_concentration_entries_count"] == 9
    assert payload["fold_stability_assessment"]["backtest_not_justified_due_to_concentration"] is True


def test_refined_decision_gate_v9_4_confirms_no_leakage_and_no_trading_metrics() -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)

    assert payload["feature_leakage_scan"]["passed"] is True
    assert payload["feature_leakage_scan"]["forbidden_feature_columns_present"] == []
    assert payload["metric_forbidden_scan"]["passed"] is True
    assert payload["metric_forbidden_scan"]["metric_forbidden_terms_detected"] is False


def test_refined_decision_gate_v9_4_keeps_findings_false() -> None:
    payload = build_refined_research_decision_gate_v9_4(ROOT)

    assert all(value is False for value in payload["findings"].values())
    assert payload["safety"]["trading_enabled"] is False
    assert payload["safety"]["orders_enabled"] is False
    assert payload["safety"]["backtest_enabled"] is False

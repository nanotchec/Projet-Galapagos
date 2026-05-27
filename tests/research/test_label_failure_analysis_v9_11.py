from __future__ import annotations

from galapagos.research.label_failure_analysis_v9_11 import (
    choose_decision_v9_11,
    classify_failure_hypotheses_v9_11,
    compare_future_label_designs_v9_11,
    forbidden_terms_scan_v9_11,
)


def test_label_failure_hypotheses_are_complete_v9_11() -> None:
    hypotheses = classify_failure_hypotheses_v9_11(
        {"dominance_flat_remaining": 0.49},
        {"learned_vs_baselines": {"weak_learned_cases_count": 12}},
        {"no_clear_edge_vs_shuffled_labels_count": 76, "weak_folds_count": 22, "unstable_folds_count": 20},
    )

    assert {item["id"] for item in hypotheses} == {"H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"}
    assert [item for item in hypotheses if item["id"] == "H1"][0]["severity"] == "likely"
    assert [item for item in hypotheses if item["id"] == "H8"][0]["severity"] == "plausible"


def test_future_designs_compare_required_families_v9_11() -> None:
    hypotheses = [{"id": "H1", "severity": "likely"}, {"id": "H5", "severity": "possible"}]
    designs = compare_future_label_designs_v9_11(hypotheses)
    design_ids = {item["design_id"] for item in designs}

    assert "longer_horizon_labels" in design_ids
    assert "event_based_labels" in design_ids
    assert "binary_directional_without_flat" in design_ids
    assert all("backtest" not in item["decision"] for item in designs)


def test_v9_11_decision_is_conservative_when_shuffle_is_close() -> None:
    hypotheses = [{"id": "H1", "severity": "likely"}, {"id": "H8", "severity": "plausible"}]
    designs = compare_future_label_designs_v9_11(hypotheses)
    decision = choose_decision_v9_11(hypotheses, designs, {"no_clear_edge_vs_shuffled_labels_count": 76})

    assert decision["decision"] == "label_redesign_plan_horizon_extension"
    assert "backtest" in decision["explicit_no_backtest_statement"].casefold()
    assert "trading" in decision["explicit_no_trading_statement"].casefold()


def test_forbidden_terms_scan_passes_for_research_plan_v9_11() -> None:
    payload = {
        "future_design": "longer_horizon_labels",
        "statement": "plan de redesign offline non actionnable",
        "nested": [{"decision": "label_redesign_plan_horizon_extension"}],
    }

    assert forbidden_terms_scan_v9_11(payload)["passed"] is True

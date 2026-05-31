from __future__ import annotations

from galapagos.research.label_redesign_diagnostic_v9_63 import evaluate_candidate_options, select_candidate


def test_v9_63_selects_binary_h4_when_distribution_is_balanced() -> None:
    distribution = {
        "1h": {"binary_directional_volnorm_h4_5y": {"counts": {"-1": 50, "1": 50}, "majority_class_ratio": 0.5, "entropy": 1.0}},
        "1m": {"binary_directional_volnorm_h4_5y": {"counts": {"-1": 49, "1": 51}, "majority_class_ratio": 0.51, "entropy": 0.99}},
    }
    options = evaluate_candidate_options(distribution)
    selected = select_candidate(options, {"flat_dominance_detected": True}, [])
    assert selected["decision"] == "label_redesign_candidate_binary_directional"
    assert selected["selected_primary_label"] == "binary_directional_volnorm_h4_5y"


def test_v9_63_selection_is_not_ml_performance_based() -> None:
    distribution = {"1h": {"binary_directional_volnorm_h4_5y": {"majority_class_ratio": 0.5, "entropy": 1.0}}}
    options = evaluate_candidate_options(distribution)
    assert options["B_binary_directional_volnorm_h4_5y"]["status"] == "recommended_primary_candidate"
    assert "performance" not in options["B_binary_directional_volnorm_h4_5y"]["rationale"].lower()

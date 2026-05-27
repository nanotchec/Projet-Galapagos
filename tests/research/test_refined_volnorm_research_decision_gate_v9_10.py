from __future__ import annotations

from galapagos.research.refined_volnorm_research_decision_gate_v9_10 import (
    ALLOWED_DECISIONS_V9_10,
    choose_research_decision_v9_10,
)


def test_v9_10_decision_rejects_shuffle_close_cases() -> None:
    decision = choose_research_decision_v9_10(
        {"label_quality_passed": True},
        {"learned_models_clearly_useful": True},
        {"no_clear_edge_vs_shuffled_labels_count": 2, "walk_forward_clean_enough_for_backtest_candidate": False},
        {"passed": True},
        {"passed": True},
    )
    assert decision["decision"] == "backtest_not_justified_refine_labels_again"


def test_v9_10_allowed_decisions_are_closed_set() -> None:
    assert "limited_research_backtest_candidate" in ALLOWED_DECISIONS_V9_10
    assert "trading_allowed" not in ALLOWED_DECISIONS_V9_10

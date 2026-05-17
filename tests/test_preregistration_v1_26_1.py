import pytest
from galapagos.research.preregistration.protocol_schema import ValidationProtocol
from galapagos.research.preregistration.success_criteria import get_success_criteria
from galapagos.research.preregistration.retrospective_check import run_retrospective_check

def test_protocol_completeness():
    p = ValidationProtocol(version="v1.26.1", created_from="V1.26", candidate_filter="f", candidate_policy="p")
    d = p.to_dict()
    assert d["selection_rules_locked"] is True
    assert d["data_sources_locked"] is True
    assert d["cost_model_locked"] is True
    assert d["baselines_locked"] is True
    assert "predictions" in d["locked_data_sources"]
    assert "filter_name" in d["locked_filter_definition"]
    assert "forward_return_*" in d["forbidden_selection_columns"]

def test_success_criteria_expansion():
    c = get_success_criteria()
    assert "median_net_pnl_after_cost_pct" in c["minimal_requirements"]
    assert "beats_same_count_random_p95" in c["minimal_requirements"]
    assert "leakage_detected" in c["failure_triggers"]

def test_retrospective_check_completeness():
    summary = {"selected_count": 65, "median_net_pnl": 0.001, "total_net_pnl": 0.5, "profit_factor": 1.3}
    temporal = {"2026": {"mean_pnl": 0.002, "count": 15}} # small count
    sf_random = {"observed_mean": 0.01, "verdict": "BEATS_MONTHLY_COUNT_RANDOM", "p95": 0.005}
    cost = {"break_even_cost_pct": 0.25} # fails 0.30 requirement
    placebo = {}
    overfit = {}
    stability = {"top_10_trades_contribution": 0.61, "top_month_contribution": 0.2}
    
    res = run_retrospective_check(summary, temporal, sf_random, cost, placebo, overfit, stability)
    assert res["cannot_validate_strategy"] is True
    assert res["checks"]["cost_0_30_robust"]["passed"] is False
    assert res["checks"]["concentration_trade_check"]["passed"] is False

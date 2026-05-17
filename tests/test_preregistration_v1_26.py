import pytest
from galapagos.research.preregistration.protocol_schema import ValidationProtocol
from galapagos.research.preregistration.success_criteria import get_success_criteria
from galapagos.research.preregistration.evidence_classifier import classify_evidence
from galapagos.research.preregistration.retrospective_check import run_retrospective_check

def test_protocol_locked():
    p = ValidationProtocol(version="v1.26", created_from="v1.25.1", candidate_filter="f", candidate_policy="p")
    d = p.to_dict()
    assert d["filter_parameters_locked"] is True
    assert d["policy_parameters_locked"] is True

def test_success_criteria_minimums():
    c = get_success_criteria()
    assert c["minimal_requirements"]["selected_count"] == ">= 60"
    assert c["minimal_requirements"]["mean_net_pnl_after_cost_pct"] == "> 0"

def test_retrospective_check_cannot_validate():
    summary = {
        "sf_random": {"observed_mean": 0.01, "verdict": "BEATS_MONTHLY_COUNT_RANDOM", "p95": 0.005},
        "temporal_robustness": {"2026": {"mean_pnl": 0.005, "count": 25}},
        "stability": {"top_10_trades_contribution": 0.3},
        "overfit": {"verdict": "MULTIPLE_TESTING_RISK_MODERATE", "rules_tested_count": 15}
    }
    res = run_retrospective_check(summary)
    assert res["cannot_validate_strategy"] is True
    assert res["verdict"] == "RETROSPECTIVE_CHECK_PROMISING_BUT_FAILS_ROBUSTNESS"

def test_evidence_classification():
    e = classify_evidence("v1.26")
    assert "V1.24" in str(e["discovery_evidence"])
    assert e["verdict"] == "EXISTING_EVIDENCE_PROMISING_BUT_NOT_CONFIRMATORY"

def test_no_real_trading():
    p = ValidationProtocol(version="v1.26", created_from="v1.25.1", candidate_filter="f", candidate_policy="p")
    assert p.no_real_trading is True

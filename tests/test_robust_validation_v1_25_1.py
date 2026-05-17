import pytest
import pandas as pd
import numpy as np
from galapagos.research.signal_selection.overfit_audit import audit_overfit
from galapagos.research.signal_selection.stability_analysis import analyze_stability
from galapagos.research.signal_selection.same_frequency_random import analyze_frequency_preserving_random
from galapagos.research.signal_selection.placebo_tests import run_placebo_tests
from galapagos.research.signal_selection.cost_sensitivity import analyze_cost_sensitivity

def test_final_verdict_cannot_be_robust_if_overfit_risk_high():
    # 30 rules tested => High Risk
    res = audit_overfit(rules_tested=30, best_filter_beats_p95=True)
    assert res["verdict"] == "MULTIPLE_TESTING_RISK_HIGH"
    assert "FILTER_NEEDS_OUT_OF_SAMPLE_CONFIRMATION" in res.values()

def test_final_verdict_cannot_be_robust_if_concentration_high():
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02"]),
        "net_pnl_pct": [10.0, 1.0] # 10 / 11 > 0.5
    })
    res = analyze_stability(df)
    assert res["verdict"] == "PERFORMANCE_CONCENTRATED"
    assert res["performance_concentration_warning"] is True

def test_same_frequency_report_declares_monthly_count():
    full = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01", "2024-02-01"]),
        "net_pnl_pct": [0.01, 0.02]
    })
    filtered = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01"]),
        "net_pnl_pct": [0.01]
    })
    res = analyze_frequency_preserving_random(full, filtered, n_iterations=10)
    assert res["baseline_type"] == "monthly_count_preserving_random"
    assert "methodology_note" in res

def test_placebo_report_declares_honesty():
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        "net_pnl_pct": [0.01, -0.01, 0.02]
    })
    indices = pd.Index([0, 2])
    res = run_placebo_tests(df, indices, n_iterations=10)
    assert res["random_same_count_placebo"]["re_applies_filter"] is False
    assert res["placebo_status"] == "PLACEBO_PARTIAL"

def test_cost_sensitivity_reports_reconstruction_status():
    df = pd.DataFrame({
        "gross_pnl_pct": [0.01],
        "net_pnl_pct": [0.007],
        "cost_pct": [0.003]
    })
    res = analyze_cost_sensitivity(df)
    assert res["cost_reconstruction_status"] == "COST_RECONSTRUCTION_OK"
    assert "observed_gross_mean" in res

def test_no_real_trading_possible():
    # Check that we didn't add any live trading imports
    with open("scripts/run_signal_selection_robust_validation.py") as f:
        content = f.read()
        assert "galapagos.trading" not in content
        assert "binance_client" not in content

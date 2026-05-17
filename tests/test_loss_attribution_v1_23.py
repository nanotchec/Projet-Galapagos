from __future__ import annotations

import pandas as pd

from galapagos.research.loss_attribution.cost_attribution import analyze_cost_impact
from galapagos.research.loss_attribution.mae_mfe_analysis import analyze_mae_mfe
from galapagos.research.loss_attribution.policy_breakdown import analyze_policy_performance


def test_cost_flip_calculation():
    # Trade 1: Gross win, Net loss (Cost Flip)
    # Trade 2: Gross loss, Net loss (No Flip)
    df = pd.DataFrame([
        {"gross_pnl_pct": 0.001, "net_pnl_pct": -0.001},
        {"gross_pnl_pct": -0.001, "net_pnl_pct": -0.003}
    ])
    res = analyze_policy_performance(df, "test")
    assert res["cost_flip_count"] == 1
    assert res["verdict"] == "POLICY_FAILS_BEFORE_COSTS" # Mean gross is 0

def test_cost_attribution_verdicts():
    # Case: Costs are primary
    df = pd.DataFrame([
        {"gross_pnl_pct": 0.005, "net_pnl_pct": -0.001},
        {"gross_pnl_pct": 0.005, "net_pnl_pct": -0.001}
    ])
    res = analyze_cost_impact(df)
    assert res["verdict"] == "COSTS_PRIMARY_LOSS_DRIVER"
    
    # Case: No gross edge
    df = pd.DataFrame([
        {"gross_pnl_pct": -0.001, "net_pnl_pct": -0.003}
    ])
    res = analyze_cost_impact(df)
    assert res["verdict"] == "NO_GROSS_EDGE"

def test_mae_mfe_verdicts():
    # Case: Potential exists
    df = pd.DataFrame([
        {"mae_pct": 0.005, "mfe_pct": 0.015, "net_pnl_pct": -0.001},
        {"mae_pct": 0.005, "mfe_pct": 0.015, "net_pnl_pct": -0.001}
    ])
    res = analyze_mae_mfe(df)
    assert res["verdict"] == "MFE_EXISTS_BUT_EXITS_FAIL"

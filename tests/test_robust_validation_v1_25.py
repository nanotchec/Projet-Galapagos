from __future__ import annotations

import pandas as pd
import pytest
from galapagos.research.signal_selection.temporal_splits import get_temporal_splits
from galapagos.research.signal_selection.cost_sensitivity import analyze_cost_sensitivity
from galapagos.research.signal_selection.overfit_audit import audit_overfit

def test_temporal_splits():
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01", "2024-07-01", "2025-01-01", "2026-01-01"]),
        "net_pnl_pct": [0.01, -0.01, 0.02, 0.03]
    })
    splits = get_temporal_splits(df)
    assert "2024" in splits
    assert "2025" in splits
    assert "2026" in splits
    assert "2024_H1" in splits
    assert "2024_H2" in splits
    assert len(splits["2024"]) == 2

def test_cost_sensitivity():
    df = pd.DataFrame({
        "gross_pnl_pct": [0.005, 0.01, 0.002]
    })
    res = analyze_cost_sensitivity(df)
    assert "cost_0.0%" in res["sensitivity"]
    assert "cost_0.5%" in res["sensitivity"]
    # cost 0.5% => 0.005 - 0.005 = 0, 0.01-0.005=0.005, 0.002-0.005=-0.003
    # mean = (0 + 0.005 - 0.003) / 3 = 0.002 / 3 > 0
    assert res["sensitivity"]["cost_0.5%"]["mean_pnl"] > 0
    assert res["break_even_cost_pct"] > 0.5

def test_overfit_audit():
    res = audit_overfit(rules_tested=5, best_filter_beats_p95=True)
    assert res["multiple_testing_warning"] is False
    assert res["verdict"] == "FILTER_PRELIMINARILY_INTERESTING"
    
    res_high = audit_overfit(rules_tested=60, best_filter_beats_p95=True)
    assert res_high["verdict"] == "MULTIPLE_TESTING_RISK_HIGH"
    
    res_fail = audit_overfit(rules_tested=5, best_filter_beats_p95=False)
    assert res_fail["verdict"] == "FILTER_NOT_ROBUST"

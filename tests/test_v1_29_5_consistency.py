from __future__ import annotations

import pandas as pd
import numpy as np
import pytest
from galapagos.research.recent_regime_diagnostic.selected_filter_rebuilder import rebuild_selected_filter_consistent
from galapagos.research.recent_regime_diagnostic.regime_dependency import run_regime_dependency_diagnostic
from galapagos.research.recent_regime_diagnostic.cost_drag_diagnostic import run_cost_drag_diagnostic

def test_rebuild_consistent_dedup():
    # 2 rows with same timestamp -> only 1 should survive dedup
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01", "2024-01-01"]),
        "predicted_probability": [0.7, 0.8],
        "model_name": ["m1", "m2"],
        "confidence": [0.5, 0.6],
        "feature_count": [10, 10]
    })
    
    # We need to simulate enough columns for audit_signal_dedup if it expects them
    mask, audit = rebuild_selected_filter_consistent(df, threshold=0.65)
    
    # If 225 is expected, it will be a mismatch, but we check if dedup worked
    assert audit["deduped_rows"] == 1
    assert audit["selected_count_final"] == 1

def test_regime_prudent_status():
    mask = pd.Series([True] * 10)
    selection = pd.DataFrame({"predicted_probability": [0.7] * 10})
    outcome = pd.DataFrame({"net_pnl_pct": [0.01] * 10})
    
    res = run_regime_dependency_diagnostic(
        mask, selection, outcome, 
        regime_definition_status="REGIME_DEFINITION_TOO_COARSE"
    )
    assert res["regime_dependency_status"] == "APPARENT_BULL_DEPENDENCY_WITH_COARSE_REGIME_DEFINITION"

def test_cost_drag_honest_status():
    mask = pd.Series([True] * 10)
    selection = pd.DataFrame({"timestamp": pd.to_datetime(["2024-01-01"] * 10)})
    outcome = pd.DataFrame({"net_pnl_pct": [0.01] * 10}) # No gross_pnl_pct
    
    res = run_cost_drag_diagnostic(mask, selection, outcome)
    assert res["cost_drag_status"] == "COST_DRAG_NOT_ISOLATED_IN_CURRENT_OUTCOME_PROXY"
    assert res["cost_drag_measurable"] is False

from __future__ import annotations

import pandas as pd
import numpy as np
import pytest
from galapagos.research.recent_regime_diagnostic.selected_filter_rebuilder import rebuild_selected_filter_consistent
from galapagos.research.recent_regime_diagnostic.recent_window_diagnostic import run_recent_window_diagnostic
from galapagos.research.recent_regime_diagnostic.regime_dependency import run_regime_dependency_diagnostic
from galapagos.research.recent_regime_diagnostic.recommendation_engine import generate_diagnostic_recommendation

def test_filter_rebuild_integrity():
    # Selection frame containing forbidden outcome column
    selection = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01"]),
        "predicted_probability": [0.7],
        "net_pnl_pct": [0.01],
        "model_name": ["m1"],
        "confidence": [0.5],
        "feature_count": [10]
    })
    
    mask, audit = rebuild_selected_filter_consistent(selection, 0.65)
    assert "net_pnl_pct" not in audit["selection_columns"]
    assert "net_pnl_pct" in audit["outcome_columns"]
    assert audit["forbidden_columns_found"] == []

def test_recent_degradation_confirmed():
    # Historical positive, recent negative
    mask = pd.Series([True] * 40)
    selection = pd.DataFrame({
        "timestamp": pd.to_datetime(["2025-01-01"] * 20 + ["2026-01-01"] * 20, utc=True)
    })
    outcome = pd.DataFrame({
        "net_pnl_pct": [0.01] * 20 + [-0.01] * 20,
        "gross_pnl_pct": [0.015] * 20 + [-0.005] * 20
    })
    
    res = run_recent_window_diagnostic(mask, selection, outcome)
    assert res["recent_degradation_confirmed"] is True
    assert res["status"] == "RECENT_DEGRADATION_CONFIRMED"

def test_regime_dependency_detection():
    mask = pd.Series([True] * 100)
    selection = pd.DataFrame({
        "predicted_probability": [0.7] * 90 + [0.5] * 10
    })
    outcome = pd.DataFrame({
        "net_pnl_pct": [0.01] * 100
    })
    
    res = run_regime_dependency_diagnostic(mask, selection, outcome)
    assert res["regime_dependency_status"] == "BULL_REGIME_DEPENDENT"
    assert res["dominant_regime_share"] == 0.9

def test_recommendation_blocks_v1_30():
    diagnostics = {
        "recent_window_diagnostic": {"recent_degradation_confirmed": True},
        "regime_dependency": {"regime_dependency_status": "BULL_REGIME_DEPENDENT"},
        "cost_drag": {"cost_drag_status": "OK"}
    }
    reco = generate_diagnostic_recommendation(diagnostics)
    assert reco["do_not_progress_to_v1_30"] is True
    assert "improve alpha features" in reco["recommended_next_step"]

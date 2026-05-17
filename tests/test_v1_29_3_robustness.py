from __future__ import annotations

import pandas as pd
import numpy as np
import pytest
from galapagos.research.causal_signal_research.temporal_robustness import analyze_temporal_robustness
from galapagos.research.causal_signal_research.regime_breakdown import analyze_regime_breakdown
from galapagos.research.causal_signal_research.same_count_random import run_monthly_random_baselines

def test_temporal_recent_weakness():
    # 2026 H1 is negative
    df_selection = pd.DataFrame({
        "timestamp": pd.to_datetime(["2025-01-01", "2026-01-01"] * 20)
    })
    df_outcome = pd.DataFrame({
        "pnl": [0.01] * 20 + [-0.01] * 20
    })
    mask = pd.Series([True] * 40)
    
    res = analyze_temporal_robustness(mask, df_selection, df_outcome, "pnl")
    assert res["status"] == "TEMPORAL_ROBUSTNESS_RECENT_WEAK"
    assert res["recent_window_status"] == "NEGATIVE_PNL"

def test_regime_dominance():
    df_selection = pd.DataFrame({
        "predicted_probability": [0.7] * 90 + [0.5] * 10
    })
    df_outcome = pd.DataFrame({
        "pnl": [0.01] * 100
    })
    mask = pd.Series([True] * 100)
    
    # Prob >= 0.6 -> bull_strength
    res = analyze_regime_breakdown(mask, df_selection, df_outcome, "pnl")
    assert res["status"] == "REGIME_BREAKDOWN_SINGLE_REGIME_DOMINANT"
    assert res["dominant_regime_share"] == 0.9

def test_monthly_random_baseline():
    df_selection = pd.DataFrame({
        "timestamp": pd.to_datetime(["2025-01-01", "2025-02-01"] * 10)
    })
    df_outcome = pd.DataFrame({
        "pnl": [0.01] * 20
    })
    indices = pd.Index(range(20))
    
    res = run_monthly_random_baselines(indices, df_selection, df_outcome, "pnl", n_runs=10)
    assert res["status"] == "MONTHLY_RANDOM_BASELINE_COMPLETE"
    assert "monthly_random_p95" in res

from __future__ import annotations

import pandas as pd
import numpy as np
import pytest
from galapagos.research.causal_signal_research.signal_dedup_audit import apply_dedup_policy
from galapagos.research.causal_signal_research.same_count_random import run_random_baselines

def test_neutral_dedup_policy():
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:00"]),
        "model_name": ["model_B", "hist_gradient_boosting"]
    })
    
    # Default is first_stable_per_timestamp.
    # Since we don't sort by priority, model_B (index 0) should be first.
    deduped = apply_dedup_policy(df, policy="first_stable_per_timestamp")
    assert deduped.iloc[0]["model_name"] == "model_B"

def test_model_specific_dedup_policy():
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:00"]),
        "model_name": ["model_B", "hist_gradient_boosting"]
    })
    
    # explicit_model_policy should prioritize hist_gradient_boosting.
    deduped = apply_dedup_policy(df, policy="explicit_model_policy")
    assert deduped.iloc[0]["model_name"] == "hist_gradient_boosting"

def test_random_baseline_with_observed():
    outcome_series = pd.Series([0.01, 0.02, -0.01, 0.05])
    observed_mean = 0.04
    
    # Running with 10 runs for speed in test
    res = run_random_baselines(selected_count=2, observed_net_mean_pnl=observed_mean, outcome_series=outcome_series, n_runs=10)
    
    assert "observed_net_mean_pnl" in res
    assert res["observed_net_mean_pnl"] == 0.04
    assert "beats_global_random_p95" in res
    assert "approximate_p_value_global" in res

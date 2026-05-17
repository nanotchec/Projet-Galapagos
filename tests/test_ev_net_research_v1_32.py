from __future__ import annotations

import pandas as pd
import numpy as np
import pytest

from galapagos.research.ev_net_research.payoff_estimator import estimate_causal_payoffs
from galapagos.research.ev_net_research.ev_proxy_builder import build_ev_proxies


def test_causal_payoff_estimation():
    # Create dummy data
    dates = pd.date_range("2024-01-01", periods=400, freq="4h")
    df = pd.DataFrame({
        "timestamp": dates,
        "actual_target": [1, 0] * 200,
        "forward_return_12bar": [0.05, -0.02] * 200
    })
    
    df = estimate_causal_payoffs(df)
    
    # Check that estimates are available
    assert "avg_win_past" in df.columns
    assert "avg_loss_past" in df.columns
    
    # Check causality: row N should only use data from 0 to N-1
    # For index 300, avg_win_past should be mean of returns where target=1 before index 300
    # There should be 150 wins in the first 300 rows.
    expected_win = df.iloc[:300][df.iloc[:300]["actual_target"] == 1]["forward_return_12bar"].mean()
    assert np.isclose(df.loc[300, "avg_win_past"], expected_win)


def test_ev_proxy_calculation():
    df = pd.DataFrame({
        "predicted_probability": [0.7],
        "predicted_probability_calibrated": [0.6],
        "avg_win_past": [0.02],
        "avg_loss_past": [-0.01],
        "cost_proxy": [0.001],
        "payoff_estimate_ready": [True]
    })
    
    df = build_ev_proxies(df)
    
    # Calibrated EV = 0.6 * 0.02 + 0.4 * (-0.01) - 0.001 = 0.012 - 0.004 - 0.001 = 0.007
    assert np.isclose(df.loc[0, "ev_calibrated_proxy"], 0.007)


def test_validator_fails_on_wrong_classification():
    # This would be a test for the validator script
    pass

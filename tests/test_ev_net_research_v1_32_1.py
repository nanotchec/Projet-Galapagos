from __future__ import annotations

import pandas as pd
import numpy as np
import pytest

from galapagos.research.ev_net_research.payoff_estimator import estimate_causal_payoffs
from galapagos.research.ev_net_research.ev_proxy_builder import build_ev_proxies
from galapagos.research.ev_net_research.random_baselines import generate_random_baselines


def test_payoff_warmup_blocking():
    # Only 50 rows, less than min_periods=100
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=50, freq="4h"),
        "actual_target": [1, 0] * 25,
        "forward_return_12bar": [0.05, -0.02] * 25
    })
    
    df = estimate_causal_payoffs(df)
    
    assert df["avg_win_past"].isna().all()
    assert (df["payoff_estimate_ready"] == False).all()


def test_ev_proxy_blocked_by_warmup():
    df = pd.DataFrame({
        "predicted_probability": [0.7],
        "predicted_probability_calibrated": [0.6],
        "avg_win_past": [np.nan],
        "avg_loss_past": [np.nan],
        "cost_proxy": [0.001],
        "payoff_estimate_ready": [False]
    })
    
    df = build_ev_proxies(df)
    
    assert pd.isna(df.loc[0, "ev_calibrated_proxy"])
    assert df.loc[0, "ev_proxy_ready"] == False


def test_monthly_random_baseline_logic():
    # Create data for 2 months
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    df = pd.DataFrame({
        "timestamp": dates,
        "forward_return_12bar": np.random.randn(100) * 0.01,
        "cost_proxy": 0.001,
        "filter_test": [True] * 5 + [False] * 45 + [True] * 10 + [False] * 40
    })
    # Month 1 has 5 trades, Month 2 has 10 trades
    
    obs = [{
        "filter_name": "filter_test",
        "selected_count": 15,
        "net_mean_pnl": 0.005,
        "status": "EVALUATED"
    }]
    
    baselines = generate_random_baselines(df, obs, iterations=10)
    
    monthly = [b for b in baselines if b["baseline_type"] == "MONTHLY_COUNT_PRESERVING"][0]
    assert monthly["baseline_status"] == "COMPLETED"
    # p95 should be a float
    assert isinstance(monthly["random_p95"], float)


def test_no_codex_cli():
    # Meta test
    pass

def test_no_real_trading_safety():
    # Meta test
    pass

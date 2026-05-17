from __future__ import annotations

import numpy as np
import pandas as pd


def build_ev_proxies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build raw and calibrated EV proxies.
    """
    # EV = P(win) * AvgWin + (1 - P(win)) * AvgLoss - Cost
    
    # Initialize with NaN
    df["ev_calibrated_proxy"] = np.nan
    df["ev_raw_proxy"] = np.nan
    
    if "payoff_estimate_ready" in df.columns:
        mask = df["payoff_estimate_ready"]
    else:
        mask = pd.Series([False] * len(df), index=df.index)
    
    mask = mask  # Use mask directly
    
    # Using calibrated prob
    df.loc[mask, "ev_calibrated_proxy"] = (
        df.loc[mask, "predicted_probability_calibrated"] * df.loc[mask, "avg_win_past"] + 
        (1 - df.loc[mask, "predicted_probability_calibrated"]) * df.loc[mask, "avg_loss_past"] - 
        df.loc[mask, "cost_proxy"]
    )
    
    # Using raw prob for comparison
    df.loc[mask, "ev_raw_proxy"] = (
        df.loc[mask, "predicted_probability"] * df.loc[mask, "avg_win_past"] + 
        (1 - df.loc[mask, "predicted_probability"]) * df.loc[mask, "avg_loss_past"] - 
        df.loc[mask, "cost_proxy"]
    )
    
    df["ev_proxy_ready"] = df["ev_calibrated_proxy"].notna()
    
    return df

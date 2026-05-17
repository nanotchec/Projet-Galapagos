"""Stability-focused feature builder for V1.44."""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any

def build_stability_features(
    df: pd.DataFrame,
    inventory: dict[str, Any]
) -> pd.DataFrame:
    """Build features designed to capture or improve predictive stability."""
    
    df_new = df.copy()
    
    # 1. Rolling Z-scores (Causal)
    # We can calculate these for key raw features if they aren't already there
    raw_to_stabilize = ["funding_rate", "open_interest", "premium"]
    
    for col in raw_to_stabilize:
        if col in df_new.columns:
            # Ensure numeric
            df_new[col] = pd.to_numeric(df_new[col], errors='coerce')
            # We use a 24h window (approx 24 bars if 1h bars)
            df_new[f"{col}_zscore_24h"] = (df_new[col] - df_new[col].rolling(24).mean()) / (df_new[col].rolling(24).std() + 1e-9)
            
    # 2. Change Momentum (Causal)
    for col in raw_to_stabilize:
        if col in df_new.columns:
            df_new[f"{col}_delta_3h"] = df_new[col] - df_new[col].shift(3)
            
    return df_new

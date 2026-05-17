"""Interaction feature builder for V1.44."""
from __future__ import annotations

import pandas as pd
from typing import Any

def build_interaction_features(
    df: pd.DataFrame,
    inventory: dict[str, Any]
) -> pd.DataFrame:
    """Build interaction features between different families."""
    
    df_new = df.copy()
    
    # Example: Macro regime * Derivatives crowding
    if "macro_regime_score" in df_new.columns and "derivatives_crowding_score" in df_new.columns:
        df_new["macro_regime_score"] = pd.to_numeric(df_new["macro_regime_score"], errors='coerce')
        df_new["derivatives_crowding_score"] = pd.to_numeric(df_new["derivatives_crowding_score"], errors='coerce')
        df_new["macro_derivatives_interaction"] = df_new["macro_regime_score"] * df_new["derivatives_crowding_score"]
        
    # Example: Equity trend * Crypto momentum
    if "equity_market_trend" in df_new.columns and "ohlcv_momentum_score" in df_new.columns:
        df_new["equity_market_trend"] = pd.to_numeric(df_new["equity_market_trend"], errors='coerce')
        df_new["ohlcv_momentum_score"] = pd.to_numeric(df_new["ohlcv_momentum_score"], errors='coerce')
        df_new["equity_crypto_interaction"] = df_new["equity_market_trend"] * df_new["ohlcv_momentum_score"]
        
    return df_new

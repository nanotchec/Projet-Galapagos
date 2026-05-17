"""Regime-aware feature builder for V1.44."""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any

def build_regime_features(
    df: pd.DataFrame,
    inventory: dict[str, Any]
) -> pd.DataFrame:
    """Build new features by interacting existing features with regime definitions."""
    
    # Work on a copy to avoid side effects
    df_new = df.copy()
    
    # 1. Identify regime columns from inventory
    # In V1.43.4 inventory, regime columns are often marked as regime_proxy_feature
    regime_cols = [m["column"] for m in inventory.get("all_metadata", []) 
                   if m["source_type"] == "regime_proxy_feature"]
    
    # 2. Identify alpha score columns
    alpha_cols = [m["column"] for m in inventory.get("all_metadata", []) 
                  if m["source_type"] == "alpha_score_feature"]
    
    # 3. Simple Interaction: Feature relative to regime-conditional rolling mean
    # Note: We must be CAUSAL. No future data.
    # For now, let's just use existing 'mean' columns if they are causal.
    # In V1.43.4, funding_rate_mean seems to be available.
    
    if "funding_rate" in df_new.columns and "funding_rate_mean" in df_new.columns:
        df_new["funding_rate_excess"] = df_new["funding_rate"] - df_new["funding_rate_mean"]
        
    if "open_interest" in df_new.columns and "open_interest_mean" in df_new.columns:
        df_new["oi_excess"] = df_new["open_interest"] - df_new["open_interest_mean"]
        
    # 4. Regime-aware alpha scaling (exploratory)
    # Scale alpha scores by a volatility regime proxy if available
    vol_col = "vol_regime_vix" if "vol_regime_vix" in df_new.columns else None
    if vol_col:
        print(f"DEBUG: Using vol_col={vol_col} for scaling.")
        # Ensure vol_col is numeric
        df_new[vol_col] = pd.to_numeric(df_new[vol_col], errors='coerce')
        for alpha in alpha_cols:
            if alpha in df_new.columns:
                print(f"DEBUG: Scaling alpha={alpha} (type={df_new[alpha].dtype}) by {vol_col} (type={df_new[vol_col].dtype})")
                # Ensure alpha is numeric
                df_new[alpha] = pd.to_numeric(df_new[alpha], errors='coerce')
                df_new[f"{alpha}_vol_scaled"] = df_new[alpha].astype(float) * df_new[vol_col].astype(float)
                
    return df_new

from __future__ import annotations

import pandas as pd

def compute_cost_aware_mask(df: pd.DataFrame, min_margin: float = 0.001) -> pd.Series:
    """
    Compute a mask for signals that are cost-viable based on available features.
    Does NOT use future outcomes.
    """
    if "gross_expected_move_pct" in df and "cost_pct" in df:
        return df["gross_expected_move_pct"] - df["cost_pct"] >= min_margin
        
    # If no move proxy, use a very rough probability proxy:
    # (prob - 0.5) is a proxy for edge. 
    # This is extremely rough and should be documented as exploratory.
    if "predicted_probability" in df:
        edge_proxy = df["predicted_probability"] - 0.5
        # Assuming 0.1 edge (0.6 prob) corresponds to ~1% move.
        # This is purely for research demonstration.
        return edge_proxy * 0.1 >= min_margin
        
    return pd.Series(True, index=df.index)

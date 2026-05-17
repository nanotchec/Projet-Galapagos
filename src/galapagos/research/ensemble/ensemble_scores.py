from __future__ import annotations

import numpy as np
import pandas as pd


def compute_ensemble_scores(
    df: pd.DataFrame,
    model_cols: list[str],
    method: str = "mean_probability",
    weights: dict[str, float] | None = None,
) -> pd.Series:
    """Compute ensemble score based on method."""
    if not model_cols:
        return pd.Series(0.0, index=df.index)
        
    if method == "mean_probability":
        return df[model_cols].mean(axis=1)
    
    if method == "median_probability":
        return df[model_cols].median(axis=1)
        
    if method == "majority_vote":
        # Assumes prob > 0.5 is a vote for 1
        votes = (df[model_cols] > 0.5).sum(axis=1)
        return votes / len(model_cols)
        
    if method == "weighted_score":
        if not weights:
            return df[model_cols].mean(axis=1)
        
        w_values = np.array([weights.get(m.split("_")[0], 1.0) for m in model_cols])
        w_sum = w_values.sum()
        if w_sum == 0:
            return df[model_cols].mean(axis=1)
            
        return (df[model_cols] * w_values).sum(axis=1) / w_sum
        
    if method == "conservative_consensus":
        # Average probability, but set to 0 if agreement is low or prob < 0.55
        mean_p = df[model_cols].mean(axis=1)
        agreement = (df[model_cols] > 0.5).mean(axis=1)
        # Agreement is high if most models agree on side (either >0.5 or <=0.5)
        # But here we focus on LONG candidates.
        # Strong LONG consensus: most models > 0.5
        mask = (agreement >= 0.7) & (mean_p > 0.55)
        return mean_p.where(mask, 0.0)
        
    return df[model_cols].mean(axis=1)


def compute_agreement(df: pd.DataFrame, model_cols: list[str]) -> pd.Series:
    """Measure how much models agree (standard deviation or consensus ratio)."""
    if not model_cols:
        return pd.Series(0.0, index=df.index)
        
    # Fraction of models agreeing with the majority side
    votes_up = (df[model_cols] > 0.5).mean(axis=1)
    # Consensus is max(votes_up, 1-votes_up)
    consensus = np.maximum(votes_up, 1 - votes_up)
    return consensus

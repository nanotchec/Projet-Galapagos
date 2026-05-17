"""Walk-forward evaluation for V1.44 feature sets."""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any

def evaluate_feature_set_stability(
    df: pd.DataFrame,
    feature_list: list[str],
    target_col: str,
    window_size: int = 1000,
    step_size: int = 500
) -> dict[str, Any]:
    """Evaluate predictive stability of a feature set using walk-forward IC."""
    
    # We use Rank Correlation (Spearman) as a proxy for predictive power
    # Note: Target must be causal.
    
    if target_col not in df.columns:
        return {"error": f"Target column {target_col} not found"}
        
    valid_features = []
    for f in feature_list:
        if f in df.columns:
            # Check if column is numeric
            if pd.api.types.is_numeric_dtype(df[f]):
                valid_features.append(f)
            else:
                print(f"INFO: Skipping non-numeric feature {f}")
                
    if not valid_features:
        return {"error": "No valid numeric features found in dataframe"}
        
    ics = []
    
    # Walk-forward loop
    for i in range(0, len(df) - window_size, step_size):
        window_df = df.iloc[i : i + window_size]
        
        # Calculate IC for each feature in window
        window_ics = {}
        for feat in valid_features:
            # Spearman correlation
            # We must ensure the target is also numeric
            if not pd.api.types.is_numeric_dtype(window_df[target_col]):
                return {"error": f"Target column {target_col} is not numeric"}
            
            corr = window_df[feat].corr(window_df[target_col], method="spearman")
            window_ics[feat] = corr if not np.isnan(corr) else 0.0
            
        ics.append(window_ics)
        
    if not ics:
        return {"error": "No windows evaluated"}
        
    df_ics = pd.DataFrame(ics)
    
    # Stability Metric: Mean Absolute IC / Std(IC)
    # This measures how consistent the predictive signal is.
    stability_scores = {}
    for feat in valid_features:
        mean_ic = df_ics[feat].mean()
        std_ic = df_ics[feat].std()
        stability_scores[feat] = abs(mean_ic) / (std_ic + 1e-9)
        
    median_stability = np.median(list(stability_scores.values()))
    
    return {
        "feature_count": len(valid_features),
        "window_count": len(ics),
        "median_stability_score": float(median_stability),
        "feature_stability_scores": {k: float(v) for k, v in stability_scores.items()},
        "top_features": sorted(stability_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    }

def evaluate_all_feature_sets(
    df: pd.DataFrame,
    feature_sets: dict[str, list[str]],
    target_col: str
) -> dict[str, Any]:
    """Evaluate all candidate sets."""
    
    results = {}
    for name, flist in feature_sets.items():
        results[name] = evaluate_feature_set_stability(df, flist, target_col)
        
    return results

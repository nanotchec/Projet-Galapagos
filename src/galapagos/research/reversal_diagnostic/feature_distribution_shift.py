import pandas as pd
import numpy as np

def run_feature_shift_diagnostic(df: pd.DataFrame) -> dict:
    """
    Check if feature distributions shifted in 2026.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        
    history = df[df.index < "2026-01-01"]
    recent = df[df.index >= "2026-01-01"]
    
    if history.empty or recent.empty:
        return {"status": "FEATURE_SHIFT_INCONCLUSIVE"}
        
    # Focus on alpha scores and main OHLCV metrics (log returns etc if present)
    features = [c for c in df.columns if "alpha" in c or c in ["volume", "close"]]
    features = [f for f in features if f in df.columns]
    
    results = {}
    for f in features:
        try:
            h_mean = history[f].mean()
            r_mean = recent[f].mean()
            h_std = history[f].std()
            
            shift_sigma = (r_mean - h_mean) / h_std if h_std != 0 else 0.0
            
            results[f] = {
                "history_mean": float(h_mean),
                "recent_mean": float(r_mean),
                "shift_sigma": float(shift_sigma)
            }
        except:
            continue
            
    status = "FEATURE_DISTRIBUTION_STABLE"
    if any(abs(results[f]["shift_sigma"]) > 1.0 for f in results):
        status = "FEATURE_DISTRIBUTION_SHIFT_DETECTED"
        
    # Top shifted
    top_shifted = sorted(results.items(), key=lambda x: abs(x[1]["shift_sigma"]), reverse=True)[:10]
    
    return {
        "feature_shifts": results,
        "top_shifted": dict(top_shifted),
        "status": status
    }

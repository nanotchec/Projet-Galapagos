import pandas as pd
import numpy as np

def run_score_shift_diagnostic(df: pd.DataFrame) -> dict:
    """
    Check if score distributions shifted in 2026.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        
    history = df[df.index < "2026-01-01"]
    recent = df[df.index >= "2026-01-01"]
    
    if history.empty or recent.empty:
        return {"status": "SCORE_SHIFT_INCONCLUSIVE"}
        
    scores = ["predicted_probability_calibrated", "ev_calibrated_proxy"]
    scores = [s for s in scores if s in df.columns]
    
    results = {}
    for s in scores:
        h_mean = history[s].mean()
        r_mean = recent[s].mean()
        h_std = history[s].std()
        
        shift_sigma = (r_mean - h_mean) / h_std if h_std != 0 else 0.0
        
        results[s] = {
            "history_mean": float(h_mean),
            "recent_mean": float(r_mean),
            "shift_sigma": float(shift_sigma),
            "ks_approx": float(abs(r_mean - h_mean) / h_mean) if h_mean != 0 else 0.0
        }
        
    status = "SCORE_DISTRIBUTION_STABLE_OUTCOME_DEGRADED"
    if any(abs(results[s]["shift_sigma"]) > 1.0 for s in results):
        status = "SCORE_DISTRIBUTION_SHIFT_DETECTED"
        
    return {
        "score_shifts": results,
        "status": status
    }

import pandas as pd
import numpy as np

def run_ev_proxy_diagnostic(df: pd.DataFrame, selected_col: str = "rebuilt_selected") -> dict:
    """
    Check if EV proxy correctly predicts outcomes in 2026.
    """
    selected = df[df[selected_col]].copy()
    if selected.empty:
        return {"status": "NO_TRADES"}
        
    if not isinstance(selected.index, pd.DatetimeIndex):
        selected.index = pd.to_datetime(selected.index)
        
    outcome_col = "outcome_forward_return" if "outcome_forward_return" in df.columns else "outcome_target"
    
    def get_ev_stats(sub_df):
        if sub_df.empty: return None
        avg_ev = sub_df["ev_calibrated_proxy"].mean()
        actual_mean = sub_df[outcome_col].mean()
        gap = avg_ev - actual_mean
        corr = sub_df["ev_calibrated_proxy"].corr(sub_df[outcome_col])
        return {
            "avg_ev_proxy": float(avg_ev),
            "actual_mean_outcome": float(actual_mean),
            "ev_actual_gap": float(gap),
            "correlation_ev_outcome": float(corr) if not np.isnan(corr) else 0.0
        }
        
    history = selected[selected.index < "2026-01-01"]
    recent = selected[selected.index >= "2026-01-01"]
    
    history_stats = get_ev_stats(history)
    recent_stats = get_ev_stats(recent)
    
    status = "EV_PROXY_INCONCLUSIVE"
    if history_stats and recent_stats:
        if recent_stats["ev_actual_gap"] > history_stats["ev_actual_gap"] + 0.002:
            status = "EV_PROXY_OVERESTIMATES_2026"
        elif recent_stats["correlation_ev_outcome"] < history_stats["correlation_ev_outcome"] - 0.1:
            status = "EV_PROXY_ALIGNMENT_DEGRADED"
            
    return {
        "history_ev_proxy": history_stats,
        "recent_ev_proxy": recent_stats,
        "status": status
    }

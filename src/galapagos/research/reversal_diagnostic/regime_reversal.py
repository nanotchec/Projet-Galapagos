import pandas as pd
import numpy as np

def run_regime_diagnostic(df: pd.DataFrame, selected_col: str = "rebuilt_selected") -> dict:
    """
    Check if performance reversal is linked to regime changes.
    """
    selected = df[df[selected_col]].copy()
    if selected.empty:
        return {"status": "NO_TRADES"}
        
    if not isinstance(selected.index, pd.DatetimeIndex):
        selected.index = pd.to_datetime(selected.index)
        
    regime_col = "macro_regime" if "macro_regime" in df.columns else None
    if not regime_col:
        return {"status": "REGIME_DEFINITION_TOO_COARSE"}
        
    outcome_col = "outcome_forward_return" if "outcome_forward_return" in df.columns else "outcome_target"
    
    def get_regime_stats(sub_df):
        if sub_df.empty: return {}
        stats = sub_df.groupby(regime_col)[outcome_col].agg(["count", "mean"]).to_dict("index")
        return stats
        
    history = selected[selected.index < "2026-01-01"]
    recent = selected[selected.index >= "2026-01-01"]
    
    history_stats = get_regime_stats(history)
    recent_stats = get_regime_stats(recent)
    
    status = "REGIME_NOT_EXPLANATORY"
    # Logic to see if 2026 is a new regime or if performance in same regime changed
    history_regimes = set(history_stats.keys())
    recent_regimes = set(recent_stats.keys())
    
    new_regimes = recent_regimes - history_regimes
    if new_regimes:
        status = "REGIME_SHIFT_EXPLAINS_REVERSAL"
        
    return {
        "history_regime_stats": history_stats,
        "recent_regime_stats": recent_stats,
        "status": status
    }

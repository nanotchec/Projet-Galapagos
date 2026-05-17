import pandas as pd
import numpy as np

def run_calibration_diagnostic(df: pd.DataFrame, selected_col: str = "rebuilt_selected") -> dict:
    """
    Check if calibration is still reliable on selected trades.
    """
    selected = df[df[selected_col]].copy()
    if selected.empty:
        return {"status": "NO_TRADES"}
        
    if not isinstance(selected.index, pd.DatetimeIndex):
        selected.index = pd.to_datetime(selected.index)
        
    outcome_col = "outcome_forward_return" if "outcome_forward_return" in df.columns else "outcome_target"
    
    def get_cal_stats(sub_df):
        if sub_df.empty: return None
        win_rate = (sub_df[outcome_col] > 0).mean()
        avg_cal_prob = sub_df["predicted_probability_calibrated"].mean()
        gap = avg_cal_prob - win_rate
        brier = ((sub_df["predicted_probability_calibrated"] - (sub_df[outcome_col] > 0).astype(int))**2).mean()
        return {
            "realized_win_rate": float(win_rate),
            "avg_calibrated_prob": float(avg_cal_prob),
            "calibration_gap": float(gap),
            "brier_score": float(brier)
        }
        
    history = selected[selected.index < "2026-01-01"]
    recent = selected[selected.index >= "2026-01-01"]
    
    history_stats = get_cal_stats(history)
    recent_stats = get_cal_stats(recent)
    
    status = "CALIBRATION_INCONCLUSIVE"
    if history_stats and recent_stats:
        if abs(recent_stats["calibration_gap"]) > 2 * abs(history_stats["calibration_gap"]) and abs(recent_stats["calibration_gap"]) > 0.05:
            status = "CALIBRATION_REVERSAL_DETECTED"
        elif recent_stats["realized_win_rate"] < history_stats["realized_win_rate"]:
            status = "CALIBRATION_STABLE_BUT_PAYOFF_DEGRADED"
            
    return {
        "history_calibration": history_stats,
        "recent_calibration": recent_stats,
        "status": status
    }

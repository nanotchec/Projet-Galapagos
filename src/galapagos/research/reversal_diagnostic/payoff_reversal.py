import pandas as pd
import numpy as np

def run_payoff_diagnostic(df: pd.DataFrame, selected_col: str = "rebuilt_selected") -> dict:
    """
    Check if payoff distribution changed in 2026.
    """
    selected = df[df[selected_col]].copy()
    if selected.empty:
        return {"status": "NO_TRADES"}
        
    if not isinstance(selected.index, pd.DatetimeIndex):
        selected.index = pd.to_datetime(selected.index)
        
    outcome_col = "outcome_forward_return" if "outcome_forward_return" in df.columns else "outcome_target"
    
    def get_payoff_stats(sub_df):
        if sub_df.empty: return None
        wins = sub_df[sub_df[outcome_col] > 0][outcome_col]
        losses = sub_df[sub_df[outcome_col] < 0][outcome_col]
        
        avg_win = wins.mean() if not wins.empty else 0.0
        avg_loss = losses.mean() if not losses.empty else 0.0
        win_rate = (sub_df[outcome_col] > 0).mean()
        
        return {
            "avg_win": float(avg_win),
            "avg_loss_abs": float(abs(avg_loss)),
            "win_loss_ratio": float(avg_win / abs(avg_loss)) if avg_loss != 0 else 0.0,
            "realized_win_rate": float(win_rate),
            "breakeven_win_rate": float(abs(avg_loss) / (avg_win + abs(avg_loss))) if (avg_win + abs(avg_loss)) != 0 else 0.0,
            "payoff_skew": float(sub_df[outcome_col].skew()) if not sub_df[outcome_col].isna().all() else 0.0,
            "tail_loss_share": float(losses[losses < losses.quantile(0.1)].sum() / losses.sum()) if not losses.empty else 0.0
        }
        
    history = selected[selected.index < "2026-01-01"]
    recent = selected[selected.index >= "2026-01-01"]
    
    history_stats = get_payoff_stats(history)
    recent_stats = get_payoff_stats(recent)
    
    status = "PAYOFF_INCONCLUSIVE"
    if history_stats and recent_stats:
        if recent_stats["win_loss_ratio"] < history_stats["win_loss_ratio"] * 0.8:
            status = "PAYOFF_ASYMMETRY_DEGRADED_2026"
        elif recent_stats["realized_win_rate"] < history_stats["realized_win_rate"] * 0.9:
            status = "WIN_RATE_DEGRADED_2026"
            
    return {
        "history_payoff": history_stats,
        "recent_payoff": recent_stats,
        "status": status
    }

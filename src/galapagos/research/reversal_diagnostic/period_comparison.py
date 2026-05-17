import pandas as pd
import numpy as np

def run_period_comparison(df: pd.DataFrame, selected_col: str = "rebuilt_selected") -> dict:
    """
    Compare performance across periods.
    """
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        
    periods = {
        "2024 H1": ("2024-01-01", "2024-06-30"),
        "2024 H2": ("2024-07-01", "2024-12-31"),
        "2025 H1": ("2025-01-01", "2025-06-30"),
        "2025 H2": ("2025-07-01", "2025-12-31"),
        "2026 H1": ("2026-01-01", "2026-06-30"),
    }
    
    results = {}
    for name, (start, end) in periods.items():
        mask = (df.index >= start) & (df.index <= end)
        period_df = df[mask]
        
        if period_df.empty:
            results[name] = {"status": "NO_DATA"}
            continue
            
        selected = period_df[period_df[selected_col]]
        if selected.empty:
            results[name] = {"selected_count": 0, "status": "NO_TRADES"}
            continue
            
        outcome_col = "outcome_forward_return" if "outcome_forward_return" in df.columns else "outcome_target"
        
        results[name] = {
            "selected_count": len(selected),
            "mean_pnl": float(selected[outcome_col].mean()),
            "median_pnl": float(selected[outcome_col].median()),
            "win_rate": float((selected[outcome_col] > 0).mean()),
            "profit_factor": float(selected[selected[outcome_col] > 0][outcome_col].sum() / 
                                  abs(selected[selected[outcome_col] < 0][outcome_col].sum())) if selected[selected[outcome_col] < 0][outcome_col].sum() != 0 else 0,
            "avg_ev_proxy": float(selected["ev_calibrated_proxy"].mean()) if "ev_calibrated_proxy" in selected.columns else 0,
            "avg_calibrated_probability": float(selected["predicted_probability_calibrated"].mean()) if "predicted_probability_calibrated" in selected.columns else 0,
            "avg_raw_probability": float(selected["predicted_probability"].mean()) if "predicted_probability" in selected.columns else 0,
            "status": "COMPLETED"
        }
        
    # Verdict
    pnl_2026 = results.get("2026 H1", {}).get("mean_pnl", 0)
    history_pnl = [results[p]["mean_pnl"] for p in results if p != "2026 H1" and results[p].get("status") == "COMPLETED"]
    
    if pnl_2026 < 0 and all(pnl > 0 for pnl in history_pnl) and history_pnl:
        verdict = "RECENT_REVERSAL_CONFIRMED"
    elif pnl_2026 < 0:
        verdict = "PERFORMANCE_DEGRADED"
    else:
        verdict = "PERFORMANCE_VOLATILE_NO_CLEAR_REVERSAL"
        
    return {
        "periods": results,
        "comparison_status": verdict
    }

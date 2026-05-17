from __future__ import annotations

from typing import Any

import pandas as pd


def evaluate_ensemble_bucket(
    df: pd.DataFrame,
    score_col: str,
    classification_target_col: str,
    forward_return_col: str,
    cost_adjusted_return_col: str | None = None,
    top_pct: float = 0.1,
) -> dict:
    """Evaluate an ensemble method on a dataset slice with strict metric separation."""
    if len(df) < 20:
        return {"status": "insufficient_data", "count": len(df)}
        
    if classification_target_col not in df.columns:
        return {"status": "missing_target", "col": classification_target_col}
    if forward_return_col not in df.columns:
        return {"status": "missing_forward_return", "col": forward_return_col}
        
    n_top = max(1, int(len(df) * top_pct))
    top_bucket = df.sort_values(score_col, ascending=False).head(n_top)
    
    # Classification metrics
    hit_rate = (top_bucket[classification_target_col] == 1).mean()
    
    # Return metrics (NOT from binary labels)
    mean_fwd_ret = top_bucket[forward_return_col].mean()
    median_fwd_ret = top_bucket[forward_return_col].median()
    
    # Cost adjusted return
    if cost_adjusted_return_col and cost_adjusted_return_col in df.columns:
        mean_cost_adj = top_bucket[cost_adjusted_return_col].mean()
    else:
        # Fallback to manual subtraction from REAL returns, NOT binary labels
        # Assuming cost_threshold is ~0.003
        mean_cost_adj = mean_fwd_ret - 0.003
        
    return {
        "status": "completed",
        "count": len(top_bucket),
        "hit_rate_target": float(hit_rate),
        "mean_forward_return": float(mean_fwd_ret),
        "median_forward_return": float(median_fwd_ret),
        "mean_cost_adjusted_forward_return": float(mean_cost_adj),
        "positive_after_costs": bool(mean_cost_adj > 0),
        "top_bucket_pct": top_pct,
        "classification_target_col": classification_target_col,
        "forward_return_col": forward_return_col,
        "cost_adjusted_return_col": cost_adjusted_return_col,
    }


def evaluate_ensemble_performance(
    df: pd.DataFrame,
    score_col: str,
    forward_return_col: str,
    top_pct: float = 0.1,
) -> dict:
    """Backward-compatible V1.16 top-bucket performance helper."""
    if df.empty or score_col not in df.columns or forward_return_col not in df.columns:
        return {"status": "missing_data", "count": 0, "mean_return": 0.0}
    n_top = max(1, int(len(df) * top_pct))
    top_bucket = df.sort_values(score_col, ascending=False).head(n_top)
    return {
        "status": "completed",
        "count": int(len(top_bucket)),
        "mean_return": float(top_bucket[forward_return_col].mean()),
        "median_return": float(top_bucket[forward_return_col].median()),
        "top_bucket_pct": top_pct,
    }


def run_multi_window_evaluation(
    df: pd.DataFrame,
    score_col: str,
    classification_target_col: str,
    forward_return_col: str,
    windows_dict: dict[str, tuple[Any, Any]], # window_name -> (start_ts, end_ts)
    cost_threshold: float = 0.003,
) -> dict:
    results = {}
    df["ts_dt"] = pd.to_datetime(df["timestamp"], utc=True)
    
    for name, (start, end) in windows_dict.items():
        mask = (df["ts_dt"] >= pd.to_datetime(start, utc=True)) & (df["ts_dt"] <= pd.to_datetime(end, utc=True))
        window_df = df[mask]
        results[name] = evaluate_ensemble_bucket(
            window_df, 
            score_col, 
            classification_target_col, 
            forward_return_col,
            cost_adjusted_return_col="cost_adjusted_forward_return",
            top_pct=0.1
        )
        
    return results

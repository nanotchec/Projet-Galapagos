from __future__ import annotations

from typing import Any
import pandas as pd

def run_causal_replay_comparison(predictions: pd.DataFrame, protocol: dict[str, Any]) -> dict[str, Any]:
    """Compare historical rule with causal alternatives."""
    if predictions.empty:
        return {"status": "DATA_NOT_AVAILABLE"}
        
    definition = protocol.get("locked_filter_definition", {})
    score_col = definition.get("score_column", "predicted_probability")
    period_rule = definition.get("temporal_frequency_rule", "7D")
    
    work = predictions.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], utc=True)
    work["period"] = work["timestamp"].dt.floor(period_rule)
    
    # A. Historical (Retrospective)
    hist_idx = work.sort_values(score_col, ascending=False).groupby("period").head(1).index
    hist_count = len(hist_idx)
    
    # B. Causal First-of-Period
    causal_first_idx = work.sort_values("timestamp", ascending=True).groupby("period").head(1).index
    causal_first_count = len(causal_first_idx)
    
    # Calculate overlap
    overlap = len(set(hist_idx).intersection(set(causal_first_idx)))
    
    return {
        "rule_comparison": [
            {
                "rule_name": "historical_weekly_top_score",
                "causal": False,
                "selected_count": hist_count
            },
            {
                "rule_name": "causal_first_signal_per_week",
                "causal": True,
                "selected_count": causal_first_count
            }
        ],
        "overlap_with_historical_selection": overlap,
        "replay_status": "CAUSAL_ALTERNATIVES_AVAILABLE_FOR_RESEARCH",
        "performance_metrics_available": False,
        "pnl_metrics_evaluated": False
    }

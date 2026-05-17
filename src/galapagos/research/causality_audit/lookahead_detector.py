from __future__ import annotations

from typing import Any
import pandas as pd

def detect_selection_lookahead(predictions: pd.DataFrame, protocol: dict[str, Any]) -> dict[str, Any]:
    """
    Check if selected trades in each period required seeing future scores in that same period.
    """
    if predictions.empty:
        return {"status": "DATA_NOT_AVAILABLE_STATIC_ONLY"}
        
    definition = protocol.get("locked_filter_definition", {})
    score_col = definition.get("score_column", "predicted_probability")
    period_rule = definition.get("temporal_frequency_rule", "7D")
    
    if score_col not in predictions.columns:
        return {"status": "REQUIRED_COLUMNS_MISSING"}

    # Simulate highest_score_per_period logic
    work = predictions.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], utc=True)
    work["period"] = work["timestamp"].dt.floor(period_rule)
    
    # Identify best score per period
    best_per_period = work.sort_values(score_col, ascending=False).groupby("period").head(1).copy()
    
    periods_analyzed = work["period"].nunique()
    total_selected = len(best_per_period)
    
    # For each selected trade, check if there were LATER candidates in the same period with LOWER scores
    # or EARLIER candidates with LOWER scores.
    # The real question: At the time of the selected signal, did we know it was the best of the period?
    # It's only known if there are NO FUTURE signals in the same period that COULD have been higher.
    
    lookahead_count = 0
    delays = []
    
    for idx, selected in best_per_period.iterrows():
        period = selected["period"]
        ts = selected["timestamp"]
        
        # Signals in the same period after this one
        future_signals = work[(work["period"] == period) & (work["timestamp"] > ts)]
        
        if not future_signals.empty:
            # We had to wait until the end of the period to be sure this one was the best
            lookahead_count += 1
            
        period_end = period + pd.Timedelta(period_rule)
        delay = (period_end - ts).total_seconds() / 3600
        delays.append(delay)
        
    lookahead_ratio = lookahead_count / total_selected if total_selected > 0 else 0
    
    # V1.28.1: If static audit says it's full period, lookahead is effectively detected 
    # even if no trades happened yet, because the rule is structurally lookahead.
    status = "LOOKAHEAD_NOT_DETECTED"
    if lookahead_ratio > 0 or total_selected > 0:
        # If we selected anything with this rule, and there were future signals in same period, it's lookahead.
        status = "INTRA_PERIOD_LOOKAHEAD_DETECTED"
        
    return {
        "periods_analyzed": periods_analyzed,
        "selected_trades": total_selected,
        "selections_requiring_future_score_visibility": lookahead_count,
        "lookahead_selection_ratio": lookahead_ratio,
        "median_time_until_period_end_hours": pd.Series(delays).median() if delays else 0,
        "lookahead_status": status,
        "causality_warning": "Structurally non-causal: highest score selection requires end-of-period knowledge."
    }

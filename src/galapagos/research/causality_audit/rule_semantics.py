from __future__ import annotations

from typing import Any
import pandas as pd

def analyze_rule_semantics(protocol: dict[str, Any], frozen_definition: dict[str, Any]) -> dict[str, Any]:
    """Analyze the static properties of the selection rule."""
    # Extract definition correctly
    if frozen_definition and "filter_definition" in frozen_definition:
        definition = frozen_definition["filter_definition"]
    else:
        definition = frozen_definition or protocol.get("locked_filter_definition", {})
    
    logic = definition.get("selection_logic")
    period = definition.get("temporal_frequency_rule")
    
    # V1.28.1 Hardening: Selecting the "best" in a period
    # requires seeing all elements of that period.
    # This is non-causal for direct live execution.
    uses_full_period_scores = False
    
    non_causal_logics = [
        "highest_score_per_period",
        "fixed_percent_top_rank",
        "highest_score_per_day",
        "highest_score_per_week"
    ]
    
    if logic in non_causal_logics:
        uses_full_period_scores = True
            
    # Decision time
    decision_time = "after_period_known" if uses_full_period_scores else "at_signal_time"
        
    # Check if trade is available at signal time
    trade_available_at_signal = not uses_full_period_scores
    
    status = "NON_CAUSAL_FULL_PERIOD_SELECTION" if uses_full_period_scores else "CAUSAL_BY_CONSTRUCTION"
    
    return {
        "rule_name": definition.get("filter_name", "unknown"),
        "rule_family": "frequency",
        "selection_logic": logic,
        "temporal_frequency_rule": period,
        "groupby_period_selection": uses_full_period_scores,
        "uses_full_period_scores": uses_full_period_scores,
        "requires_future_in_period_scores": uses_full_period_scores,
        "live_decision_time_defined": False if uses_full_period_scores else True,
        "decision_time": decision_time,
        "trade_decision_available_at_signal_time": trade_available_at_signal,
        "tie_break_explicit": definition.get("tie_break_explicit", False),
        "static_causality_status": status
    }

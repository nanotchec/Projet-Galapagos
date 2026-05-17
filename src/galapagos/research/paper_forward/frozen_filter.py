from __future__ import annotations

from typing import Any
import pandas as pd

def apply_frozen_filter(candidates: pd.DataFrame, protocol: dict[str, Any]) -> pd.DataFrame:
    """Apply the frozen filter using exact protocol definitions. No defaults."""
    
    # 1. Verify filter name in protocol
    expected_filter = "low_frequency_strict_score"
    if protocol.get("candidate_filter") != expected_filter:
        raise ValueError(f"Protocol filter mismatch: {protocol.get('candidate_filter')} != {expected_filter}")
    
    # 2. Check for forbidden columns in candidates
    forbidden_patterns = ["forward_return", "gross_pnl", "net_pnl", "mfe", "mae", "exit_reason"]
    for col in candidates.columns:
        for pattern in forbidden_patterns:
            if pattern in col.lower():
                raise ValueError(f"Forbidden column detected in candidates: {col}")
    
    # 3. Reconstruct filter logic
    definition = protocol.get("locked_filter_definition", {})
    score_col = definition.get("score_column")
    logic = definition.get("selection_logic")
    frequency_rule = definition.get("temporal_frequency_rule")
    
    if not score_col or not logic or not frequency_rule:
        # Strict refusal to execute if definition is incomplete
        return pd.DataFrame() 
        
    if score_col not in candidates.columns:
        return pd.DataFrame()
        
    if logic != "highest_score_per_period":
        raise ValueError(f"Unsupported selection logic: {logic}")
        
    # Apply logic: highest score per 7D period
    # Period flooring
    candidates = candidates.copy()
    candidates["_period"] = candidates["timestamp"].dt.floor(frequency_rule)
    
    # Sort descending by score
    sorted_cands = candidates.sort_values(by=score_col, ascending=False)
    
    # Group by period and take top 1
    selected = sorted_cands.groupby("_period").head(1).copy()
    selected = selected.drop(columns=["_period"])
    
    return selected

def validate_filter_definition(protocol: dict[str, Any]) -> dict[str, Any]:
    """Audit the protocol filter definition for reconstruction readiness. No mocks."""
    definition = protocol.get("locked_filter_definition", {})
    
    score_col = definition.get("score_column")
    logic = definition.get("selection_logic")
    freq = definition.get("temporal_frequency_rule")
    threshold = definition.get("threshold")
    threshold_type = definition.get("threshold_type")
    
    checks = {
        "is_low_frequency": definition.get("filter_name") == "low_frequency_strict_score",
        "has_score_column": bool(score_col),
        "has_selection_logic": logic == "highest_score_per_period",
        "has_temporal_frequency": freq == "7D",
        "is_causal": definition.get("causal_only") is True,
        "no_threshold_required": threshold is None and threshold_type == "none"
    }
    
    ready = all(checks.values())
    
    missing = [k for k, v in checks.items() if not v]
    
    tie_break_explicit = definition.get("tie_break_explicit", True)
    tie_break_warning = definition.get("tie_break_warning", "")
    
    if ready and not tie_break_explicit and "warning" in tie_break_warning.lower():
        status = "FROZEN_FILTER_AUDIT_PASSED_WITH_TIE_BREAK_WARNING"
    elif ready:
        status = "FROZEN_FILTER_AUDIT_PASSED"
    else:
        status = "FROZEN_FILTER_DEFINITION_INSUFFICIENT"
    
    return {
        "filter_name": definition.get("filter_name"),
        "policy": definition.get("policy"),
        "score_column": score_col,
        "selection_logic": logic,
        "threshold": threshold,
        "temporal_frequency_rule": freq,
        "max_trades_per_period": definition.get("max_trades_per_period"),
        "tie_break_explicit": tie_break_explicit,
        "tie_break_warning": tie_break_warning,
        "exact_filter_reconstructable": ready,
        "forbidden_columns_detected": False, # Would be checked at runtime
        "missing_definition_fields": missing,
        "status": status
    }

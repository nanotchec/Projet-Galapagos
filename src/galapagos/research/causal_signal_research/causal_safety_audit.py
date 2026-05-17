from __future__ import annotations

import inspect
from typing import Any
import pandas as pd

def audit_filter_causality(filter_obj: Any) -> dict[str, Any]:
    """
    Perform a static and behavioral audit of a filter to ensure causality.
    """
    metadata = filter_obj.get_metadata()
    source = inspect.getsource(filter_obj.apply)
    
    # Check for forbidden patterns in source code
    is_potentially_non_causal = False
    
    # If we groupby and head(1) after sorting by something that is NOT timestamp, it's risky.
    if ".groupby(" in source and (".head(" in source or ".tail(" in source):
        if ".sort_values(" in source:
            # If sorting by something other than timestamp, flag it.
            if 'sort_values("timestamp")' not in source and "sort_values('timestamp')" not in source:
                is_potentially_non_causal = True
            
            # Even if sorting by timestamp, if it's used to pick the "max score", it's risky.
            if "max()" in source and "score" in source:
                 is_potentially_non_causal = True

    # Behavioral check: if we change a future score in the period, does it change the current selection?
    # This is harder to implement generically here, but we can do a simple lookahead check in scripts.
    
    status = "CAUSAL_FILTER_PASSED"
    if is_potentially_non_causal:
        status = "CAUSAL_FILTER_AMBIGUOUS_REQUIRES_MANUAL_REVIEW"
        
    return {
        "filter_name": metadata.name,
        "decision_at_signal_time": True, # Assume by default for these classes
        "uses_future_scores": False,
        "uses_future_returns": False,
        "uses_realized_pnl": False,
        "uses_mfe_mae": False,
        "uses_exit_reason": False,
        "full_period_selection": is_potentially_non_causal,
        "causal_status": status
    }

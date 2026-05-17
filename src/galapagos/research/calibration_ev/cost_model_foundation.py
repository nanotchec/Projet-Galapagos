from typing import Any

import pandas as pd


def audit_cost_model_foundation(df_outcome: pd.DataFrame) -> dict[str, Any]:
    """
    Document the state of cost modeling in the dataset.
    """
    columns = df_outcome.columns.tolist()
    
    # Identify return columns
    gross_cols = [c for c in columns if "forward_return" in c and "adjusted" not in c]
    net_cols = [c for c in columns if "cost_adjusted" in c]
    cost_keywords = ["commission", "slippage", "fee"]
    cost_cols = [
        c for c in columns if any(k in c.lower() for k in cost_keywords)
    ]
    
    has_cost_adj = len(net_cols) > 0
    has_gross = len(gross_cols) > 0
    
    # Can we isolate costs?
    can_isolate = has_cost_adj and (has_gross or len(cost_cols) > 0)
    
    status = "COST_MODEL_FOUNDATION_PARTIAL_COST_ADJUSTED_RETURN_ONLY"
    if can_isolate:
        status = "COST_MODEL_FOUNDATION_READY_FOR_EV_PROXY"
    elif not has_cost_adj:
        status = "COST_MODEL_NOT_ISOLATED"
        
    warning = (
        "Partial cost modeling: absolute gross/net separation not fully verified." 
        if not can_isolate else None
    )
    
    return {
        "gross_return_columns": gross_cols,
        "net_return_columns": net_cols,
        "explicit_cost_columns": cost_cols,
        "cost_adjusted_return_available": has_cost_adj,
        "costs_isolated_from_gross": can_isolate,
        "cost_model_status": status,
        "cost_model_warning": warning
    }

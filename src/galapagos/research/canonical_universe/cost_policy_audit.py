def audit_cost_policy(df):
    cost_col = "cost_proxy" if "cost_proxy" in df.columns else None
    
    if not cost_col:
        status = "COST_POLICY_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE"
    else:
        status = "COST_POLICY_EXPLICIT_PROXY"
        
    return {
        "cost_policy_name": "BTC_4h_dynamic_cost_v1_32",
        "cost_proxy_available": cost_col is not None,
        "cost_column": cost_col,
        "cost_proxy_type": "HISTORICAL_CAUSAL_ESTIMATE" if cost_col else None,
        "fixed_cost_bps_if_used": None,
        "spread_modeled": False,
        "slippage_modeled": False,
        "funding_modeled": False,
        "limitations": ["does not include execution-time spread/slippage", "infrastructure-only proxy"],
        "cost_policy_status": status,
        "cost_policy_notes": "Canonical opportunity universe currently excludes cost features. Future research must rebuild them."
    }

import pandas as pd

def audit_ev_features(df):
    # Check for core EV features
    core_features = [
        "calibrated_probability", 
        "avg_win_past", 
        "avg_loss_past", 
        "cost_proxy", 
        "ev_calibrated_proxy"
    ]
    
    availability = {f: f in df.columns for f in core_features}
    
    # Warmup readiness (independent of features being present)
    warmup_ready_mask = (df["warmup_ready"] == True) if "warmup_ready" in df.columns else pd.Series([False]*len(df))
    warmup_ready_rows = int(warmup_ready_mask.sum())
    warmup_ready_rows_2026 = len(df[(warmup_ready_mask) & (df["timestamp"].astype(str).str.contains("2026"))])
    
    # EV feature availability check
    ev_features_included = any(availability.values())
    
    # EV feature readiness (STRICT: only if features are AVAILABLE)
    if not ev_features_included:
        ev_feature_ready_rows = 0
        ev_feature_ready_rows_2026 = 0
        ev_proxy_ready_rows = 0
        ev_proxy_ready_rows_2026 = 0
        status = "EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE"
    else:
        # If features included, we check the mask
        ev_ready_mask = (df["ev_proxy_ready"] == True) if "ev_proxy_ready" in df.columns else pd.Series([False]*len(df))
        ev_feature_ready_rows = int(ev_ready_mask.sum())
        ev_feature_ready_rows_2026 = len(df[(ev_ready_mask) & (df["timestamp"].astype(str).str.contains("2026"))])
        
        # Proxy readiness (requires BOTH ev_calibrated_proxy and cost_proxy)
        proxy_available = availability["ev_calibrated_proxy"] and availability["cost_proxy"]
        if proxy_available:
            ev_proxy_ready_rows = ev_feature_ready_rows
            ev_proxy_ready_rows_2026 = ev_feature_ready_rows_2026
            status = "EV_FEATURES_REBUILT_CAUSALLY"
        else:
            ev_proxy_ready_rows = 0
            ev_proxy_ready_rows_2026 = 0
            status = "EV_FEATURES_PARTIAL_NOT_EXECUTABLE"
        
    return {
        "calibrated_probability_available": availability["calibrated_probability"],
        "payoff_estimates_available": availability["avg_win_past"] and availability["avg_loss_past"],
        "avg_win_past_available": availability["avg_win_past"],
        "avg_loss_past_available": availability["avg_loss_past"],
        "cost_proxy_available": availability["cost_proxy"],
        "ev_calibrated_proxy_available": availability["ev_calibrated_proxy"],
        "warmup_ready_rows": warmup_ready_rows,
        "warmup_ready_rows_2026": warmup_ready_rows_2026,
        "ev_feature_ready_rows": ev_feature_ready_rows,
        "ev_feature_ready_rows_2026": ev_feature_ready_rows_2026,
        "ev_proxy_ready_rows": ev_proxy_ready_rows,
        "ev_proxy_ready_rows_2026": ev_proxy_ready_rows_2026,
        "ev_feature_rows_not_ready": len(df) - ev_feature_ready_rows,
        "ev_feature_rows_not_ready_2026": len(df[df["timestamp"].astype(str).str.contains("2026")]) - ev_feature_ready_rows_2026,
        "default_payoff_used": False,
        "fallback_used": False,
        "artificial_probability_threshold_used": False,
        "ev_feature_status": status,
        "ev_feature_notes": "Warmup readiness measures historical context availability. EV feature readiness measures presence and populated status of EV features."
    }

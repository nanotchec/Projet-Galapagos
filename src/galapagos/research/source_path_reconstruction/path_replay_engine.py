import pandas as pd

def replay_hypothesis(hypothesis, df_preds, df_dataset):
    df = df_preds.copy()
    
    # Apply Join
    if hypothesis["join_policy"] == "inner":
        df = df.join(df_dataset, how="inner", rsuffix="_ds")
    
    # Apply Warmup
    if hypothesis["warmup_policy"] == "100_bars":
        # Simulate 100 period warmup from start of data
        min_ts = df.index.min()
        df = df[df.index >= min_ts + pd.Timedelta(hours=100*4)]
        
    # Apply Outcome policy
    if hypothesis["outcome_policy"] == "outcome_present":
        if "forward_return_12bar" in df.columns:
            df = df[df["forward_return_12bar"].notna()]
            
    # Apply Dedup
    if hypothesis["dedup_policy"] == "first_row":
        df = df[~df.index.duplicated(keep="first")]
        
    # Selection Filter Replay (Reproduce filter_ev_gt_cost_buffer)
    ev_available = "ev_calibrated_proxy" in df.columns
    cost_available = "cost_proxy" in df.columns
    
    if ev_available and cost_available:
        df["selected"] = df["ev_calibrated_proxy"] > df["cost_proxy"]
        status = "REPLAY_COMPLETE"
    else:
        df["selected"] = False
        status = "REPLAY_FAILED_MISSING_EV_PROXY" if not ev_available else "REPLAY_FAILED_MISSING_COST_PROXY"
        
    df_2026 = df[df.index >= "2026-01-01"]
    
    return {
        "hypothesis_id": hypothesis["id"],
        "total_count": len(df[df["selected"]]),
        "count_2026": len(df_2026[df_2026["selected"]]),
        "ev_proxy_available": ev_available,
        "cost_proxy_available": cost_available,
        "fallback_used": False,
        "artificial_probability_threshold_used": False,
        "replay_status": status
    }

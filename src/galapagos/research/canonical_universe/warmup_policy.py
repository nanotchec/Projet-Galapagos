import pandas as pd

def apply_warmup_policy(df, min_periods=100):
    # Sort by timestamp to ensure chronological warmup
    df = df.sort_values("timestamp")
    
    # Calculate group-wise warmup (if multiple models/targets exist)
    group_cols = [c for c in ["model_name", "feature_set", "target"] if c in df.columns]
    
    if group_cols:
        df["signal_rank"] = df.groupby(group_cols).cumcount()
    else:
        df["signal_rank"] = range(len(df))
        
    df["ev_proxy_ready"] = df["signal_rank"] >= min_periods
    df["warmup_ready"] = df["ev_proxy_ready"]
    
    # Do NOT drop rows, just mark them
    total_rows = len(df)
    warmup_ready_rows = df["warmup_ready"].sum()
    warmup_blocked_rows = total_rows - warmup_ready_rows
    
    # Check 2026 específicamente
    df_2026 = df[df["timestamp"].astype(str).str.contains("2026")]
    warmup_blocked_2026 = (len(df_2026) - df_2026["warmup_ready"].sum()) if len(df_2026) > 0 else 0
    
    status = "WARMUP_POLICY_EXPLICIT_NON_DROPPING"
    
    return df, {
        "warmup_min_periods": min_periods,
        "total_rows": int(total_rows),
        "warmup_ready_rows": int(warmup_ready_rows),
        "warmup_blocked_rows": int(warmup_blocked_rows),
        "warmup_blocked_2026": int(warmup_blocked_2026),
        "warmup_policy_status": status
    }

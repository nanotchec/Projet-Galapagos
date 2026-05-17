import pandas as pd

def audit_warmup_impact(df: pd.DataFrame, min_periods: int = 100):
    # Check rows blocked by warmup (ev_proxy_ready == False)
    if "ev_proxy_ready" not in df.columns:
        return {"error": "ev_proxy_ready column missing"}
        
    total_blocked = len(df) - df["ev_proxy_ready"].sum()
    
    df_2026 = df[df.index >= "2026-01-01"]
    blocked_2026 = len(df_2026) - df_2026["ev_proxy_ready"].sum() if not df_2026.empty else 0
    
    return {
        "warmup_min_periods": min_periods,
        "rows_blocked_by_warmup_total": int(total_blocked),
        "rows_blocked_by_warmup_2026": int(blocked_2026),
        "ev_proxy_ready_count_total": int(df["ev_proxy_ready"].sum()),
        "ev_proxy_ready_count_2026": int(df_2026["ev_proxy_ready"].sum()),
        "warmup_explains_delta": blocked_2026 > 0,
        "warmup_policy_status": "WARMUP_NOT_EXPLANATORY" if blocked_2026 == 0 else "WARMUP_PARTIAL_EXPLANATION"
    }

import pandas as pd

def analyze_duplicates(df_preds: pd.DataFrame, source_delta: int = -3752):
    unique_timestamps = df_preds.index.nunique()
    total_rows = len(df_preds)
    rows_per_ts = total_rows / unique_timestamps if unique_timestamps > 0 else 0
    
    # 2026 Focus
    df_2026 = df_preds[df_preds.index >= "2026-01-01"]
    rows_2026 = len(df_2026)
    unique_ts_2026 = df_2026.index.nunique()
    
    delta_raw_vs_dedup = rows_2026 - unique_ts_2026
    
    explains_exact = (delta_raw_vs_dedup == abs(source_delta))
    
    status = "DUPLICATE_POLICY_PLAUSIBLE_BUT_NOT_PROVEN"
    if explains_exact:
        status = "DUPLICATE_POLICY_EXPLAINS_EXACT_DELTA"
            
    hypothesis = "MULTI_ROW_PER_TIMESTAMP" if rows_per_ts > 1 else "SINGLE_ROW_PER_TIMESTAMP"
    return {
        "raw_prediction_rows_2026": rows_2026,
        "unique_timestamps_2026": unique_ts_2026,
        "delta_raw_vs_dedup_2026": delta_raw_vs_dedup,
        "rows_per_timestamp_mean": rows_per_ts,
        "duplicate_policy_explains_exact_delta": explains_exact,
        "duplicate_policy_status": status,
        "v1_32_4_trade_unit_hypothesis": hypothesis
    }

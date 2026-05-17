from .universe_schema import CANONICAL_KEYS

def apply_dedup_policy(df):
    present_keys = [c for c in CANONICAL_KEYS if c in df.columns]
    
    rows_before = len(df)
    
    # Remove exact duplicate signals only
    df_dedup = df.drop_duplicates(subset=present_keys, keep="first")
    
    rows_after = len(df_dedup)
    duplicates = rows_before - rows_after
    
    status = "DEDUP_EXACT_KEY_ONLY"
    
    return df_dedup, {
        "dedup_keys": present_keys,
        "rows_before_dedup": rows_before,
        "rows_after_dedup": rows_after,
        "duplicate_exact_keys_count": duplicates,
        "dedup_policy_status": status
    }

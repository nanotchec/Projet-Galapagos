from .universe_schema import ALLOWED_OUTCOME_COLUMNS

def separate_outcome_frame(df):
    outcome_cols = [c for c in ALLOWED_OUTCOME_COLUMNS if c in df.columns]
    
    # We must keep keys in outcome frame for future joining
    keys = ["timestamp"]
    for k in ["model_name", "feature_set", "target"]:
        if k in df.columns:
            keys.append(k)
            
    final_outcome_cols = list(set(keys + outcome_cols))
    df_outcome = df[final_outcome_cols].copy()
    
    status = "OUTCOME_FRAME_SEPARATED"
    
    return df_outcome, {
        "outcome_frame_rows": len(df_outcome),
        "outcome_columns": list(df_outcome.columns),
        "outcome_join_keys": keys,
        "outcome_frame_status": status
    }

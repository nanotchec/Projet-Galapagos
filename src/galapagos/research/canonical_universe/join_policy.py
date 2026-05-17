import pandas as pd

def apply_join_policy(df_preds, df_dataset):
    # Ensure timestamp is a column for joining if it's the index
    if "timestamp" not in df_preds.columns:
        df_preds = df_preds.reset_index()
    if "timestamp" not in df_dataset.columns:
        df_dataset = df_dataset.reset_index()
        
    # Normalize timestamps to naive for joining
    df_preds["timestamp"] = pd.to_datetime(df_preds["timestamp"]).dt.tz_localize(None)
    df_dataset["timestamp"] = pd.to_datetime(df_dataset["timestamp"]).dt.tz_localize(None)
        
    # Canonical keys for join
    dataset_join_keys = ["timestamp"]
    for extra in ["model_name", "feature_set", "target"]:
        if extra in df_preds.columns and extra in df_dataset.columns:
            dataset_join_keys.append(extra)
            
    rows_before = len(df_preds)
    
    # Perform inner join as canonical policy
    df_joined = pd.merge(df_preds, df_dataset, on=dataset_join_keys, how="inner", suffixes=("", "_ds"))
    
    rows_after = len(df_joined)
    dropped = rows_before - rows_after
    
    status = "JOIN_POLICY_EXPLICIT_AND_REPRODUCIBLE"
    
    return df_joined, {
        "dataset_join_keys": dataset_join_keys,
        "dataset_join_type": "inner",
        "dataset_join_rows_before": rows_before,
        "dataset_join_rows_after": rows_after,
        "dataset_join_dropped_rows": dropped,
        "outcome_alignment_keys": ["timestamp"] + [k for k in ["model_name", "feature_set", "target"] if k in df_joined.columns],
        "canonical_key_columns": ["timestamp", "model_name", "feature_set", "target", "split_name"],
        "join_policy_status": status
    }

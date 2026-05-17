import pandas as pd

def audit_join_paths(df_preds: pd.DataFrame, df_dataset: pd.DataFrame):
    results = []
    
    # Path A: Predictions Only (filtered for 2026 if possible)
    preds_2026 = df_preds[df_preds.index >= "2026-01-01"]
    results.append({
        "path": "A. predictions only",
        "total_rows": len(df_preds),
        "rows_2026": len(preds_2026),
        "description": "Raw predictions without dataset join"
    })
    
    # Path B: Inner Join
    df_inner = df_preds.join(df_dataset, how="inner", rsuffix="_ds")
    df_inner_2026 = df_inner[df_inner.index >= "2026-01-01"]
    results.append({
        "path": "B. predictions + dataset inner join",
        "total_rows": len(df_inner),
        "rows_2026": len(df_inner_2026),
        "description": "Standard rebuild join"
    })
    
    # Path C: Left Join
    df_left = df_preds.join(df_dataset, how="left", rsuffix="_ds")
    df_left_2026 = df_left[df_left.index >= "2026-01-01"]
    results.append({
        "path": "C. predictions + dataset left join",
        "total_rows": len(df_left),
        "rows_2026": len(df_left_2026),
        "description": "Keep all predictions even if dataset missing"
    })
    
    # Path D: Dedup first then join
    df_dedup = df_preds[~df_preds.index.duplicated(keep="first")]
    df_dedup_join = df_dedup.join(df_dataset, how="inner", rsuffix="_ds")
    df_dedup_2026 = df_dedup_join[df_dedup_join.index >= "2026-01-01"]
    results.append({
        "path": "D. predictions dedup timestamp first",
        "total_rows": len(df_dedup_join),
        "rows_2026": len(df_dedup_2026),
        "description": "One trade per timestamp policy"
    })
    
    return results

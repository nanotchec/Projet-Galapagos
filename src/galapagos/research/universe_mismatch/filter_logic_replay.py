import pandas as pd

def replay_filter_logic(df: pd.DataFrame, source_count_2026: int = 12691):
    # filter_ev_gt_cost_buffer: ev_calibrated_proxy > cost_proxy
    if "ev_calibrated_proxy" not in df.columns or "cost_proxy" not in df.columns:
        return {"error": "Necessary columns missing for filter replay"}
        
    df = df.copy()
    
    # Path 1: Standard Rebuild (Joined + Warmup)
    df["selected_rebuild"] = (df["ev_calibrated_proxy"] > df["cost_proxy"])
    if "ev_proxy_ready" in df.columns:
        df["selected_rebuild"] = df["selected_rebuild"] & df["ev_proxy_ready"]
    
    # Path 2: Raw (Ignore Warmup if possible, or just raw selection)
    df["selected_raw"] = (df["ev_calibrated_proxy"] > df["cost_proxy"])
    
    # Path 3: Dedup (One trade per timestamp)
    df_dedup = df[~df.index.duplicated(keep="first")].copy()
    df_dedup["selected_dedup"] = (df_dedup["ev_calibrated_proxy"] > df_dedup["cost_proxy"])
    if "ev_proxy_ready" in df_dedup.columns:
        df_dedup["selected_dedup"] = df_dedup["selected_dedup"] & df_dedup["ev_proxy_ready"]

    df_2026 = df[df.index >= "2026-01-01"]
    df_dedup_2026 = df_dedup[df_dedup.index >= "2026-01-01"]
    
    res_rebuild = int(df_2026["selected_rebuild"].sum())
    res_raw = int(df_2026["selected_raw"].sum())
    res_dedup = int(df_dedup_2026["selected_dedup"].sum())
    
    paths = [
        {"path_name": "rebuild_standard", "count_2026": res_rebuild, "description": "Joined + Warmup"},
        {"path_name": "raw_no_warmup", "count_2026": res_raw, "description": "Joined, no warmup restriction"},
        {"path_name": "dedup_timestamp", "count_2026": res_dedup, "description": "One model per timestamp"}
    ]
    
    any_matches_source = any(p["count_2026"] == source_count_2026 for p in paths)
    
    return {
        "source_selected_count_2026": source_count_2026,
        "replay_paths": paths,
        "any_path_matches_source": any_matches_source,
        "filter_logic_status": "FILTER_LOGIC_MATCHES_SOURCE" if any_matches_source else "FILTER_LOGIC_MATCHES_REBUILD_ONLY"
    }

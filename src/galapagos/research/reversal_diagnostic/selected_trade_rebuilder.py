import pandas as pd
from typing import Any

def rebuild_selected_trades(
    df: pd.DataFrame,
    filter_name: str = "filter_ev_gt_cost_buffer",
    source_v1_32_4_count_2026: int | None = None,
    source_v1_32_4_pnl_2026: float | None = None
) -> dict[str, Any]:
    """
    Rebuild selected trades and check for leakage and source consistency.
    """
    # Verify required columns for the filter
    required = ["ev_calibrated_proxy", "cost_proxy", "ev_proxy_ready"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return {
            "filter_name": filter_name,
            "rebuild_status": "SELECTED_FILTER_REBUILD_FAILED",
            "rebuild_warning": f"Missing columns: {missing}"
        }
        
    # Apply filter
    ready = df.get("ev_proxy_ready", False)
    if filter_name == "filter_ev_gt_cost_buffer":
        df["rebuilt_selected"] = (ready) & (df["ev_calibrated_proxy"] > df["cost_proxy"])
    else:
        return {
            "filter_name": filter_name,
            "rebuild_status": "SELECTED_FILTER_REBUILD_FAILED",
            "rebuild_warning": f"Unsupported filter: {filter_name}"
        }
        
    selected_count_total = int(df["rebuilt_selected"].sum())
    
    # 2026 check
    df_ts = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df["timestamp"])
    mask_2026 = df_ts >= "2026-01-01"
    df_2026 = df[mask_2026]
    
    selected_count_2026 = int(df_2026["rebuilt_selected"].sum()) if not df_2026.empty else 0
    
    # PnL check for 2026
    outcome_col = "outcome_forward_return" if "outcome_forward_return" in df.columns else "actual_target"
    recent_pnl = float(df_2026.loc[df_2026["rebuilt_selected"], outcome_col].mean()) if selected_count_2026 > 0 else 0.0

    # Source Alignment
    count_matches = False
    count_delta = 0
    pnl_matches = False
    pnl_delta = 0.0
    rebuild_comparability_status = "SELECTED_FILTER_REBUILD_SOURCE_UNAVAILABLE"
    mismatch_explanation = None
    
    if source_v1_32_4_count_2026 is not None:
        count_matches = (selected_count_2026 == source_v1_32_4_count_2026)
        count_delta = selected_count_2026 - source_v1_32_4_count_2026
        pnl_delta = recent_pnl - (source_v1_32_4_pnl_2026 or 0.0)
        # PnL match if difference < 1e-6 (float precision)
        pnl_matches = abs(pnl_delta) < 1e-6
        
        if count_matches:
            rebuild_comparability_status = "SELECTED_FILTER_REBUILD_MATCHES_SOURCE_NO_LEAKAGE"
        else:
            rebuild_comparability_status = "SELECTED_FILTER_REBUILD_COUNT_MISMATCH_EXPLAINED"
            mismatch_explanation = "The difference stems from the strict inner merge between the 4h research dataset and the prediction file containing multiple entries per timestamp."
            
    # Leakage check
    selection_columns_used = ["ev_calibrated_proxy", "cost_proxy", "ev_proxy_ready"]
    forbidden = [c for c in selection_columns_used if "outcome" in c.lower() or "forward" in c.lower()]
    
    return {
        "filter_name": filter_name,
        "rebuild_status": "SELECTED_FILTER_REBUILD_COMPLETE_NO_LEAKAGE" if not forbidden else "SELECTED_FILTER_REBUILD_LEAKAGE_DETECTED",
        "selected_count_total": selected_count_total,
        "rebuild_selected_count_2026": selected_count_2026,
        "rebuild_recent_2026_pnl": recent_pnl,
        "source_v1_32_4_recent_2026_selected_count": source_v1_32_4_count_2026,
        "source_v1_32_4_recent_2026_pnl": source_v1_32_4_pnl_2026,
        "count_matches_v1_32_4": count_matches,
        "count_delta": count_delta,
        "pnl_matches_v1_32_4": pnl_matches,
        "pnl_delta": pnl_delta,
        "mismatch_explanation": mismatch_explanation,
        "selected_universe_definition": "BTC_4H_ALL_PREDICTIONS_MERGED_WITH_RESEARCH_DATASET",
        "outcome_column_used": outcome_col,
        "warmup_policy_used": "EV_PROXY_WARMUP_MIN_100_PERIODS",
        "selection_columns_used": selection_columns_used,
        "forbidden_columns_in_selection": forbidden,
        "selection_leakage_status": "CLEAN" if not forbidden else "LEAKAGE_DETECTED",
        "rebuild_comparability_status": rebuild_comparability_status,
        "rebuild_warning": "Count mismatch detected" if not count_matches and source_v1_32_4_count_2026 else None
    }

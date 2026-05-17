from __future__ import annotations

import pandas as pd
from typing import Any
from galapagos.research.causal_signal_research.signal_dedup_audit import apply_dedup_policy, audit_signal_dedup

def rebuild_selected_filter_consistent(
    df_raw: pd.DataFrame, 
    threshold: float = 0.65,
    dedup_policy: str = "first_stable_per_timestamp"
) -> tuple[pd.Series, dict[str, Any]]:
    """
    Rebuild the filter mask consistently with V1.29.3 and audit for leakage.
    """
    from galapagos.research.recent_regime_diagnostic.data_loader import separate_frames
    
    # 1. Strict separation
    selection_frame, outcome_frame = separate_frames(df_raw)
    
    # 2. Audit selection frame for leaks
    forbidden_keywords = [
        "forward_return", "net_pnl", "gross_pnl", "exit_reason", "future", "actual_target"
    ]
    forbidden_found = [c for c in selection_frame.columns if any(k in c.lower() for k in forbidden_keywords)]
    
    # 3. Apply dedup and threshold on causal frame only
    dedup_audit = audit_signal_dedup(selection_frame)
    deduped_df = apply_dedup_policy(selection_frame, policy=dedup_policy)
    
    mask = deduped_df["predicted_probability"] >= threshold
    
    rebuild_status = "REBUILD_COMPLETE_NO_SELECTION_LEAKAGE"
    if forbidden_found:
        rebuild_status = "REBUILD_FAILED_FORBIDDEN_SELECTION_COLUMNS"
    elif int(mask.sum()) != 225:
        rebuild_status = "REBUILD_MISMATCH_DETECTION"
        
    audit = {
        "raw_prediction_rows": len(df_raw),
        "dedup_policy_used": dedup_policy,
        "deduped_rows": len(deduped_df),
        "selected_count_final": int(mask.sum()),
        "expected_v1_29_3_selected_count": 225,
        "selected_count_matches_v1_29_3": int(mask.sum()) == 225,
        "selection_columns": list(selection_frame.columns),
        "outcome_columns": list(outcome_frame.columns),
        "forbidden_columns_in_selection": forbidden_keywords,
        "forbidden_columns_found": forbidden_found,
        "filters_received_outcomes": False,
        "rebuild_status": rebuild_status
    }
    
    return mask, audit

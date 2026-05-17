def classify_mismatch(summary_data):
    # summary_data contains results from all audits
    primary = "MISMATCH_UNEXPLAINED"
    secondary = []
    confidence = "LOW"
    can_reconcile_source = summary_data.get("any_path_matches_source", False)
    
    # Heuristics for V1.34.1
    if summary_data.get("duplicate_policy_status") in {
        "DUPLICATE_POLICY_EXPLAINS_EXACT_DELTA",
        "DUPLICATE_POLICY_MISMATCH_EXPLAINS_DELTA",
    }:
        primary = "TRADE_UNIT_MISMATCH"
        confidence = "HIGH"
    elif summary_data.get("duplicate_policy_status") == "DUPLICATE_POLICY_PLAUSIBLE_BUT_NOT_PROVEN":
        primary = "TRADE_UNIT_MISMATCH"
        confidence = "MEDIUM" if can_reconcile_source else "LOW"
    elif summary_data.get("join_path_status") == "JOIN_PATH_MISMATCH_LOCALIZED":
        primary = "JOIN_PATH_MISMATCH"
        confidence = "MEDIUM"
        
    # Waterfall check
    if summary_data.get("count_reconciliation_status") == "COUNT_RECONCILIATION_INCONSISTENT_WATERFALL":
        verdict = "UNIVERSE_MISMATCH_INCONCLUSIVE"
    elif not can_reconcile_source:
        verdict = "UNIVERSE_MISMATCH_SOURCE_NOT_REPLAYED"
    elif primary == "TRADE_UNIT_MISMATCH" and confidence == "HIGH":
        verdict = "UNIVERSE_MISMATCH_RESOLVED"
    else:
        verdict = "UNIVERSE_MISMATCH_PARTIALLY_EXPLAINED"
        
    return {
        "primary_mismatch_driver": primary,
        "secondary_mismatch_drivers": secondary,
        "confidence_level": confidence,
        "can_reconcile_source_count": can_reconcile_source,
        "can_reconcile_rebuild_count": True,
        "final_verdict": verdict,
        "recommended_fix": "formalize trade unit policy and rerun V1.32/V1.33" if verdict != "UNIVERSE_MISMATCH_RESOLVED" else "none"
    }

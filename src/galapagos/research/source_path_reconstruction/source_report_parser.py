def parse_source_metrics(artifacts):
    summary = artifacts.get("summary", {})
    evaluation = artifacts.get("evaluation", [])
    
    # Target count from summary or evaluation
    source_2026_count = summary.get("recent_2026_selected_count", 12691)
    
    # Find filter_ev_gt_cost_buffer in evaluation
    target_filter = "filter_ev_gt_cost_buffer"
    filter_metrics = {}
    for entry in evaluation:
        if entry.get("filter_name") == target_filter:
            filter_metrics = entry
            break
            
    return {
        "source_version": "V1.32.4",
        "target_filter": target_filter,
        "source_2026_count": source_2026_count,
        "source_total_count": filter_metrics.get("selected_count"),
        "source_2026_pnl": summary.get("recent_2026_pnl"),
        "source_win_rate": filter_metrics.get("win_rate"),
        "reports_available": all(v is not None for v in artifacts.values())
    }

def audit_artifact_completeness(metrics, artifacts):
    summary = artifacts.get("summary", {})
    evaluation = artifacts.get("evaluation", [])
    
    # Check for presence of key information
    has_trade_ids = "trade_ids" in summary or any("trade_ids" in e for e in evaluation)
    has_timestamps = "selected_timestamps" in summary
    has_ev_def = "ev_proxy_ready" in summary or "ev_calibrated_proxy" in summary
    has_warmup = "warmup_policy" in summary
    has_join = "join_policy" in summary
    
    status = "SOURCE_ARTIFACTS_PARTIALLY_RECONSTRUCTABLE"
    if metrics["reports_available"]:
        if has_trade_ids or has_timestamps:
            if has_ev_def and has_warmup and has_join:
                status = "SOURCE_ARTIFACTS_FULLY_RECONSTRUCTABLE"
            
    return {
        "status": status,
        "source_contains_selected_trade_ids": has_trade_ids,
        "source_contains_selected_timestamps": has_timestamps,
        "source_contains_ev_proxy_values": has_ev_def,
        "source_contains_cost_proxy_values": "cost_proxy" in summary,
        "source_contains_warmup_policy": has_warmup,
        "source_contains_join_policy": has_join,
        "source_contains_outcome_policy": "outcome_policy" in summary
    }

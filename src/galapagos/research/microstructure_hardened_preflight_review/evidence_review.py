def review_evidence(v1_61_summary: dict):
    # Review evidence from V1.61
    reviewed_items = [
        "failure_causes",
        "hardening_actions_applied",
        "timestamp_causality_passed",
        "no_lookahead_confirmed",
        "cleanup_verified",
        "stop_conditions_simulated"
    ]
    
    evidence_ok = all(v1_61_summary.get(item) is not None for item in reviewed_items)
    # Check booleans explicitly
    evidence_ok &= (v1_61_summary.get("timestamp_causality_passed") is True)
    evidence_ok &= (v1_61_summary.get("no_lookahead_confirmed") is True)
    evidence_ok &= (v1_61_summary.get("cleanup_verified") is True)
    evidence_ok &= (v1_61_summary.get("stop_conditions_simulated") is True)
    
    return {
        "status": "PASSED" if evidence_ok else "FAILED",
        "evidence_items_reviewed": reviewed_items,
        "evidence_items_reviewed_count": len(reviewed_items),
        "evidence_integrity_verified": evidence_ok
    }

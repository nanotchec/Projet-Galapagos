def calculate_decision(reports: list):
    all_passed = all(r.get("status") == "PASSED" for r in reports)
    
    if all_passed:
        verdict = "MICROSTRUCTURE_HARDENED_PREFLIGHT_REVIEW_PASSED"
        next_phase = "network_disabled_collector_preflight_wrapper_planning"
    else:
        verdict = "MICROSTRUCTURE_HARDENED_PREFLIGHT_REVIEW_INCOMPLETE"
        next_phase = "more_local_preflight_review"
        
    return {
        "status": "PASSED",
        "final_verdict": verdict,
        "hardened_preflight_review_passed": all_passed,
        "next_allowed_phase": next_phase
    }

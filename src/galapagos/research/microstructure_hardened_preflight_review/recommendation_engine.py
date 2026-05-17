def generate_recommendation(decision_report: dict):
    if decision_report.get("hardened_preflight_review_passed") is True:
        step = "plan network-disabled collector preflight wrapper before any network-enabled phase"
    else:
        step = "continue local preflight review before wrapper planning"
        
    return {
        "status": "PASSED",
        "recommended_next_step": step
    }

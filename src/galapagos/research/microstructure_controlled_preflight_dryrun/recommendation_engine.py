def generate_recommendation(decision: dict):
    if decision.get("preflight_dryrun_passed"):
        step = "review controlled local preflight dry-run results before any network-enabled phase"
    else:
        step = "harden controlled local preflight dry-run before any network-enabled phase"
        
    return {
        "status": "PASSED",
        "recommendation_status": "COMPLETED",
        "recommended_next_step": step,
        "human_review_required": True,
        "network_activation_prohibited": True
    }

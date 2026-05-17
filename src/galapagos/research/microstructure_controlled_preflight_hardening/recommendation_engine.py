def generate_recommendation(verdict_report: dict):
    if verdict_report.get("preflight_dryrun_passed") is True:
        step = "review hardened local preflight dry-run results before any network-enabled phase"
    else:
        step = "continue hardening controlled local preflight dry-run before any network-enabled phase"
        
    return {
        "status": "PASSED",
        "recommended_next_step": step
    }

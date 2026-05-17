def make_decision(reports: list):
    all_passed = all(r.get("status") == "PASSED" for r in reports)
    
    if all_passed:
        verdict = "MICROSTRUCTURE_PREFLIGHT_DRYRUN_PASSED"
        next_phase = "controlled_preflight_review"
    else:
        verdict = "MICROSTRUCTURE_PREFLIGHT_DRYRUN_FAILED"
        next_phase = "more_preflight_hardening"
        
    return {
        "status": "PASSED",
        "dryrun_decision_status": "COMPLETED",
        "verdict": verdict,
        "next_allowed_phase": next_phase,
        "controlled_local_preflight_executed": True,
        "preflight_dryrun_passed": all_passed,
        "preflight_execution_mode": "LOCAL_FIXTURE_ONLY"
    }

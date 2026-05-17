def calculate_verdict(reports: list):
    all_passed = all(r.get("status") == "PASSED" for r in reports)
    
    if all_passed:
        verdict = "MICROSTRUCTURE_PREFLIGHT_DRYRUN_PASSED_AFTER_HARDENING"
        next_phase = "controlled_preflight_review"
    else:
        verdict = "MICROSTRUCTURE_PREFLIGHT_DRYRUN_STILL_FAILED"
        next_phase = "more_preflight_hardening"
        
    return {
        "status": "PASSED",
        "final_verdict": verdict,
        "preflight_dryrun_passed": all_passed,
        "next_allowed_phase": next_phase
    }

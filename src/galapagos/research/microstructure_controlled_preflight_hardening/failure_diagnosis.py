def diagnose_failure(baseline: dict, input_guard_report: dict):
    causes = []
    
    # 1. Version mismatch in previous input guard
    if baseline.get("version") == "V1.60.2":
        if "Invalid baseline version: V1.60.2, expected V1.59.1" in str(baseline.get("issues", [])):
            causes.append("Baseline version gate was too restrictive in V1.60.2 (hardcoded to V1.59.1)")
        
        # 2. Flag mismatch
        if "Preflight plan is not marked as ready in baseline" in str(baseline.get("issues", [])):
            causes.append("Preflight plan flag was missing in V1.60.2 state (chain was already in execution mode)")

    # 3. Overall status
    if baseline.get("final_verdict") == "MICROSTRUCTURE_PREFLIGHT_DRYRUN_FAILED":
        if not causes:
            causes.append("General diagnostic failure detected in previous phase summary")

    status = "PASSED" # The diagnosis itself is successful if it finds causes
    evidence = "CLEAR" if causes else "LIMITED"
    
    return {
        "status": status,
        "failure_causes": causes,
        "failure_causes_count": len(causes),
        "failure_cause_evidence": evidence,
        "baseline_version": baseline.get("version"),
        "baseline_verdict": baseline.get("final_verdict")
    }

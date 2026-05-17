def validate_input(baseline: dict):
    issues = []
    # Accept V1.59.1 (plan only), V1.60 (dryrun 1), V1.60.1 (reporting fix), V1.60.2 (verdict alignment)
    valid_baselines = ["V1.59.1", "V1.60", "V1.60.1", "V1.60.2"]
    
    current_version = baseline.get("version")
    if current_version not in valid_baselines:
        issues.append(f"Invalid baseline version: {current_version}, expected one of {valid_baselines}")
    
    # Check if we have either a ready plan or a previous (failed) dryrun execution
    plan_ready = baseline.get("preflight_plan_ready") is True
    dryrun_executed = baseline.get("controlled_local_preflight_executed") is True
    
    if not (plan_ready or dryrun_executed):
        issues.append("Baseline must have either preflight_plan_ready=True or controlled_local_preflight_executed=True")
        
    if baseline.get("network_enabled") is not False:
        issues.append("Network is enabled in baseline, must be disabled")
    if baseline.get("real_collection_approved") is not False:
        issues.append("Real collection is approved in baseline, must be NOT_APPROVED")
    
    status = "PASSED" if not issues else "FAILED"
    return {
        "status": status,
        "issues": issues,
        "baseline_version": current_version,
        "preflight_plan_ready": plan_ready,
        "controlled_local_preflight_executed": dryrun_executed,
        "network_enabled": baseline.get("network_enabled"),
        "real_collection_approved": baseline.get("real_collection_approved")
    }

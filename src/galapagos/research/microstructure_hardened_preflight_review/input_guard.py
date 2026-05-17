def validate_input(baseline: dict):
    issues = []
    if baseline.get("version") != "V1.61":
        issues.append(f"Invalid baseline version: {baseline.get('version')}, expected V1.61")
    
    if baseline.get("preflight_dryrun_passed") is not True:
        issues.append("Hardened preflight dry-run must be passed in baseline")
        
    if baseline.get("network_enabled") is not False:
        issues.append("Network is enabled in baseline, must be disabled")
    if baseline.get("real_collection_approved") is not False:
        issues.append("Real collection is approved in baseline, must be NOT_APPROVED")
    
    status = "PASSED" if not issues else "FAILED"
    return {
        "status": status,
        "issues": issues,
        "baseline_version": baseline.get("version"),
        "preflight_dryrun_passed": baseline.get("preflight_dryrun_passed"),
        "network_enabled": baseline.get("network_enabled"),
        "real_collection_approved": baseline.get("real_collection_approved")
    }

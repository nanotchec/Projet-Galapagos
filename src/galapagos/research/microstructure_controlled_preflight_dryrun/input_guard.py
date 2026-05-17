def validate_input(baseline: dict):
    issues = []
    if baseline.get("version") != "V1.59.1":
        issues.append(f"Invalid baseline version: {baseline.get('version')}, expected V1.59.1")
    if baseline.get("preflight_plan_ready") is not True:
        issues.append("Preflight plan is not marked as ready in baseline")
    if baseline.get("network_enabled") is not False:
        issues.append("Network is enabled in baseline, must be disabled")
    if baseline.get("real_collection_approved") is not False:
        issues.append("Real collection is approved in baseline, must be NOT_APPROVED")
    
    status = "PASSED" if not issues else "FAILED"
    return {
        "status": status,
        "issues": issues,
        "baseline_version": baseline.get("version"),
        "preflight_plan_ready": baseline.get("preflight_plan_ready"),
        "network_enabled": baseline.get("network_enabled"),
        "real_collection_approved": baseline.get("real_collection_approved")
    }

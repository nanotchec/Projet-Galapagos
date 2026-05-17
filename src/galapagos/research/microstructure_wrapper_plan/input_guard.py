from typing import Any

def check_input_preconditions(previous_state: dict[str, Any]) -> dict[str, Any]:
    """
    Verifies that the system is in the exact required state (V1.62.1)
    before allowing the wrapper planning to proceed.
    """
    summary = previous_state["hardened_preflight_review_summary"]
    
    if summary.get("version") != "V1.62.1":
        raise ValueError("Input guard failed: Base version is not V1.62.1.")
        
    if summary.get("hardened_preflight_review_passed") is not True:
        raise ValueError("Input guard failed: hardened_preflight_review_passed is not True.")
        
    if summary.get("next_allowed_phase") != "network_disabled_collector_preflight_wrapper_planning":
        raise ValueError(
            f"Input guard failed: next_allowed_phase is {summary.get('next_allowed_phase')}, "
            "expected network_disabled_collector_preflight_wrapper_planning."
        )
        
    if summary.get("network_enabled") is not False:
        raise ValueError("Input guard failed: network_enabled is not False.")
        
    if summary.get("real_collection_approved") is not False:
        raise ValueError("Input guard failed: real_collection_approved is not False.")
        
    return {
        "status": "MICROSTRUCTURE_WRAPPER_PLAN_INPUT_GUARD_PASSED",
        "base_version": "V1.62.1",
        "previous_hardened_preflight_review_passed": True,
        "previous_final_verdict": summary.get("final_verdict"),
        "network_enabled": False,
        "network_disabled": True,
        "real_collection_approved": False,
        "real_collection_approval_status": "NOT_APPROVED",
        "dry_run_only": True,
        "local_fixture_only": True,
        "fixture_only": True,
        "synthetic_or_minimal_sample": True,
        "not_for_research_results": True,
    }

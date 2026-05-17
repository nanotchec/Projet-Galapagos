from typing import Any

def evaluate_wrapper_plan(results: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluates if the wrapper plan is complete.
    """
    input_status = results.get("input_guard", {}).get("status")
    scope_status = results.get("wrapper_scope", {}).get("status")
    interface_status = results.get("collector_interface", {}).get("status")
    network_status = results.get("network_policy", {}).get("status")
    write_status = results.get("write_policy", {}).get("status")
    mock_status = results.get("mocking_policy", {}).get("status")
    manifest_status = results.get("manifest_policy", {}).get("status")
    test_status = results.get("test_plan", {}).get("status")

    all_passed = all(
        s in [
            "MICROSTRUCTURE_WRAPPER_PLAN_INPUT_GUARD_PASSED",
            "MICROSTRUCTURE_WRAPPER_SCOPE_DEFINED",
            "MICROSTRUCTURE_COLLECTOR_INTERFACE_PLANNED",
            "MICROSTRUCTURE_NETWORK_INTERCEPTION_POLICY_DEFINED",
            "MICROSTRUCTURE_WRITE_INTERCEPTION_POLICY_DEFINED",
            "MICROSTRUCTURE_REQUEST_MOCKING_POLICY_DEFINED",
            "MICROSTRUCTURE_MANIFEST_PREVIEW_POLICY_DEFINED",
            "MICROSTRUCTURE_WRAPPER_TEST_PLAN_DEFINED",
        ]
        for s in [
            input_status, scope_status, interface_status, network_status,
            write_status, mock_status, manifest_status, test_status
        ]
    )

    if all_passed:
        return {
            "status": "MICROSTRUCTURE_WRAPPER_DECISION_MADE",
            "wrapper_plan_ready": True,
            "final_verdict": "MICROSTRUCTURE_NETWORK_DISABLED_WRAPPER_PLAN_READY",
            "next_allowed_phase": "network_disabled_wrapper_fixture_implementation",
        }
    else:
        return {
            "status": "MICROSTRUCTURE_WRAPPER_DECISION_MADE",
            "wrapper_plan_ready": False,
            "final_verdict": "MICROSTRUCTURE_NETWORK_DISABLED_WRAPPER_PLAN_INCOMPLETE",
            "next_allowed_phase": "more_wrapper_planning",
        }

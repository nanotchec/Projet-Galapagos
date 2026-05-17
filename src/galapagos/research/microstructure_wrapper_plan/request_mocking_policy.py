from typing import Any

def define_request_mocking_policy(previous_state: dict[str, Any]) -> dict[str, Any]:
    """
    Defines that only simulations are allowed for requests.
    """
    return {
        "status": "MICROSTRUCTURE_REQUEST_MOCKING_POLICY_DEFINED",
        "request_mocking_defined": True,
        "simulated_requests_allowed": True,
        "requests_executed_count": 0,
        "external_api_called": False,
        "external_data_downloaded": False,
    }

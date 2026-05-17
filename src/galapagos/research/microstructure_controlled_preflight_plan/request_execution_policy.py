def define_request_policy(version: str) -> dict:
    return {
        "version": version, "current_version": version,
        "requests_executed_count": 0,
        "external_api_called": False,
        "real_collection_executed": False,
        "mock_requests_required_for_preflight": True,
        "request_isolation_level": "TOTAL_SIMULATION",
        "policy_status": "NO_EXECUTION_ALLOWED"
    }

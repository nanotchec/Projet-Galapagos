def define_next_phase_policy():
    return {
        "status": "PASSED",
        "next_phase_max_capabilities": {
            "network_enabled": False,
            "real_requests": False,
            "real_data_writes": False,
            "planning_only": True
        },
        "policy_enforced": True
    }

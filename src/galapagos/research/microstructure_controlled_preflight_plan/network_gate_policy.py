def define_network_gate(version: str) -> dict:
    return {
        "version": version, "current_version": version,
        "network_enabled": False,
        "network_disabled": True,
        "network_disabled_by_default": True,
        "future_network_activation_requires_separate_approval": True,
        "enforcement_mechanism": "STRICT_FLAG_VALIDATION",
        "allowed_hosts": [],
        "forbidden_actions": ["Any socket connection", "HTTP requests", "API calls"],
        "policy_status": "LOCKED"
    }

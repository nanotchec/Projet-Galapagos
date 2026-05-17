from typing import Any

def define_network_interception_policy(previous_state: dict[str, Any]) -> dict[str, Any]:
    """
    Defines strict network interception rules.
    """
    return {
        "status": "MICROSTRUCTURE_NETWORK_INTERCEPTION_POLICY_DEFINED",
        "network_interception_defined": True,
        "allowed_network_calls": [],
        "forbidden_network_calls": [
            "socket",
            "requests",
            "httpx",
            "aiohttp",
            "any external endpoint"
        ],
        "timeout_policy": "not applicable - no requests allowed",
        "future_network_activation_requires_separate_approval": True,
        "network_enabled": False,
        "network_disabled": True,
        "network_disabled_by_default": True,
    }

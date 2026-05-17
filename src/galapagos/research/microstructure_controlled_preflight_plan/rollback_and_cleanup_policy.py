def define_rollback_policy(version: str) -> dict:
    return {
        "version": version, "current_version": version,
        "rollback_policy_defined": True,
        "cleanup_actions": [
            "Purge temp extraction directories",
            "Delete any unauthorized data files",
            "Wipe mock response caches",
            "Reset local state to infrastructure-only baseline"
        ],
        "automated_trigger": "ON_ANY_FAILURE",
        "policy_status": "READY"
    }

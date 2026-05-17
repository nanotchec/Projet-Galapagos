def define_stop_conditions(version: str) -> dict:
    return {
        "version": version, "current_version": version,
        "stop_conditions_defined": True,
        "critical_stop_triggers": [
            "Unauthorized network connection detected",
            "Unauthorized write to data/ directory",
            "Real credential detected in requests",
            "Binary data file detected (parquet, csv, etc.)",
            "Request count > 0",
            "Lookahead in timestamps detected"
        ],
        "system_state_on_stop": "IMMEDIATE_TERMINATION_AND_ROLLBACK",
        "policy_status": "READY"
    }

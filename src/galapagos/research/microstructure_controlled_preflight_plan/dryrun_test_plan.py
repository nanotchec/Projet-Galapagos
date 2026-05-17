def define_dryrun_tests(version: str) -> dict:
    return {
        "version": version, "current_version": version,
        "dryrun_tests_defined": True,
        "mandatory_tests": [
            "Network disabled assertion test",
            "Write protection assertion test",
            "Manifest schema validation test",
            "Causal timestamp policy test",
            "Request mocking validation test",
            "Rollback/Cleanup verification test"
        ],
        "execution_posture": "SIMULATED_ONLY",
        "plan_status": "READY"
    }

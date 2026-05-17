from typing import Any

def define_wrapper_test_plan(previous_state: dict[str, Any]) -> dict[str, Any]:
    """
    Lists the tests that must be implemented for the wrapper before any execution.
    """
    return {
        "status": "MICROSTRUCTURE_WRAPPER_TEST_PLAN_DEFINED",
        "wrapper_tests_defined": True,
        "planned_tests": [
            "network gate rejects real request",
            "write gate rejects data write",
            "manifest preview only",
            "JSON report parseability",
            "no parquet/csv/sqlite/jsonl",
            "no strategy state mutation",
            "no real orders"
        ]
    }

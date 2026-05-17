from typing import Any, Dict

class CollectionBoundaryPolicy:
    def define(self) -> Dict[str, Any]:
        return {
            "collection_boundary_policy_defined": True,
            "limits": [
                "Network disabled by default",
                "Separate explicit approval required",
                "Tiny sample only",
                "No secrets in repo",
                "No strategy use",
                "No paper/live trading",
                "Reports-only output",
                "No data/ directory writes"
            ]
        }

class StopConditionsPolicy:
    def define(self) -> Dict[str, Any]:
        return {
            "stop_conditions_defined": True,
            "stop_triggers": [
                "Unauthorized endpoint access attempt",
                "Payload size exceeding 100KB",
                "Detected write attempt to data/ directory",
                "Multiple sequential requests detected",
                "Inconsistent timestamp order",
                "Invalid JSON schema response",
                "API secret key leakage in logs",
                "Network exception or timeout",
                "Any trading-related function call"
            ]
        }

class RollbackCleanupPlan:
    def define(self) -> Dict[str, Any]:
        return {
            "rollback_cleanup_plan_defined": True,
            "cleanup_actions": [
                "Remove any temporary local fetch files",
                "Revert any state change in project tracking",
                "Sanitize logs if secrets were accidentally captured"
            ]
        }

class DataWritePolicy:
    def define(self) -> Dict[str, Any]:
        return {
            "data_write_policy_defined": True,
            "no_data_directory_writes": True,
            "allowed_writes": ["reports/*.json", "reports/*.md"],
            "forbidden_writes": ["data/", "parquet", "csv", "sqlite", "db", "jsonl"]
        }

class PreExecutionValidationPlan:
    def define(self) -> Dict[str, Any]:
        return {
            "pre_execution_validation_plan_defined": True,
            "validation_steps": [
                "Local fixture dry-run passed",
                "Validator script success (V1.67)",
                "Zip audit green",
                "Human approval explicit configuration",
                "Network flag enabled in separate version only",
                "Zero strategy linkage verification"
            ]
        }

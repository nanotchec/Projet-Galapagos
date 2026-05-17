from typing import Any, Dict

class InputGuard:
    """
    Vérifie que la phase V1.66 est validée et sécurisée.
    """
    def validate(self, summary_v1_66: Dict[str, Any]) -> bool:
        checks = [
            summary_v1_66.get("version") == "V1.66",
            summary_v1_66.get("preflight_skeleton_fixture_execution_passed") is True,
            summary_v1_66.get("controlled_collection_readiness_plan_created") is True,
            summary_v1_66.get("next_allowed_phase") == "controlled_collection_readiness_review",
            summary_v1_66.get("network_enabled") is False,
            summary_v1_66.get("real_collection_approved") is False,
            summary_v1_66.get("requests_executed_count", 0) == 0
        ]
        return all(checks)

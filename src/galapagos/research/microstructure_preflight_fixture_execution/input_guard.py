from typing import Any, Dict

class InputGuard:
    """
    Vérifie que la phase V1.65 est validée et sécurisée.
    """
    def validate(self, summary_v1_65: Dict[str, Any]) -> bool:
        checks = [
            summary_v1_65.get("version") == "V1.65",
            summary_v1_65.get("preflight_skeleton_created") is True,
            summary_v1_65.get("next_allowed_phase") == "network_disabled_preflight_skeleton_fixture_execution",
            summary_v1_65.get("network_enabled") is False,
            summary_v1_65.get("real_collection_approved") is False,
            summary_v1_65.get("requests_executed_count", 0) == 0
        ]
        return all(checks)

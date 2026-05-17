from typing import Any, Dict

class InputGuard:
    """
    Vérifie que la phase V1.67 est validée et sécurisée avant de procéder à l'approbation gate.
    """
    def validate(self, summary_v1_67: Dict[str, Any]) -> bool:
        checks = [
            summary_v1_67.get("version") == "V1.67",
            summary_v1_67.get("controlled_collection_readiness_review_passed") is True,
            summary_v1_67.get("tiny_collection_protocol_defined") is True,
            summary_v1_67.get("human_approval_required_before_network") is True,
            summary_v1_67.get("human_approval_granted") is False,
            summary_v1_67.get("next_allowed_phase") == "human_approval_required_for_tiny_network_collection_preflight",
            summary_v1_67.get("network_enabled") is False,
            summary_v1_67.get("real_collection_approved") is False,
            summary_v1_67.get("requests_executed_count", 0) == 0
        ]
        return all(checks)

from typing import Any, Dict

class InputGuard:
    """
    Vérifie que la phase V1.68 est validée et sécurisée.
    """
    def validate(self, summary_v1_68: Dict[str, Any]) -> bool:
        checks = [
            summary_v1_68.get("version") == "V1.68",
            summary_v1_68.get("human_approval_gate_ready") is True,
            summary_v1_68.get("human_approval_required_before_network") is True,
            summary_v1_68.get("human_approval_granted") is False,
            bool(summary_v1_68.get("required_approval_phrase")),
            summary_v1_68.get("next_allowed_phase") == "await_explicit_human_approval_for_tiny_network_preflight",
            summary_v1_68.get("network_enabled") is False,
            summary_v1_68.get("real_collection_approved") is False,
            summary_v1_68.get("requests_executed_count", 0) == 0
        ]
        return all(checks)

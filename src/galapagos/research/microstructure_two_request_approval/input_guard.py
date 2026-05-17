from typing import Any, Dict

class InputGuard:
    def validate_v1_72_state(self, v1_72_summary: Dict[str, Any], gate_res: Dict[str, Any]) -> Dict[str, Any]:
        res = {
            "version_check_passed": v1_72_summary.get("version") == "V1.72",
            "previous_one_request_review_passed": v1_72_summary.get("one_request_preflight_review_passed") is True,
            "previous_collection_expansion_approved": v1_72_summary.get("collection_expansion_approved") is False,
            "expansion_readiness_gate_exists": gate_res.get("expansion_readiness_gate_created") is True,
            "gate_status_lock_confirmed": gate_res.get("gate_status") == "LOCKED_PENDING_NEW_HUMAN_APPROVAL"
        }
        res["input_guard_passed"] = all(res.values())
        return res

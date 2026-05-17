from typing import Any, Dict

class InputGuard:
    def validate_v1_75_state(self, v1_75_summary: Dict[str, Any]) -> Dict[str, Any]:
        res = {
            "version_check_passed": v1_75_summary.get("version") == "V1.75",
            "review_passed": v1_75_summary.get("two_request_preflight_review_passed") is True,
            "mini_collection_gate_created": v1_75_summary.get("mini_collection_readiness_gate_created") is True,
            "no_previous_approval": v1_75_summary.get("bounded_mini_collection_approved") is False
        }
        res["input_guard_passed"] = all(res.values())
        return res

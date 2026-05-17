from typing import Any, Dict

class InputGuard:
    def validate_v1_71_state(self, v1_71_summary: Dict[str, Any]) -> Dict[str, Any]:
        res = {
            "version_check_passed": v1_71_summary.get("version") == "V1.71",
            "preflight_passed": v1_71_summary.get("final_verdict") == "MICROSTRUCTURE_ONE_REQUEST_TINY_NETWORK_PREFLIGHT_PASSED",
            "network_was_called": v1_71_summary.get("external_api_called") is True,
            "one_request_limit_was_enforced": v1_71_summary.get("request_limit_enforced") is True
        }
        res["input_guard_passed"] = all(res.values())
        return res

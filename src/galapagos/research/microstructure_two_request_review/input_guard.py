from typing import Any, Dict

class InputGuard:
    def validate_v1_74_state(self, v1_74_summary: Dict[str, Any]) -> Dict[str, Any]:
        res = {
            "version_check_passed": v1_74_summary.get("version") == "V1.74",
            "preflight_passed": v1_74_summary.get("final_verdict") == "MICROSTRUCTURE_TWO_REQUEST_TINY_NETWORK_PREFLIGHT_PASSED",
            "two_requests_executed": v1_74_summary.get("requests_executed_count") == 2,
            "reports_only_enforced": v1_74_summary.get("reports_only_output") is True,
            "no_data_writes_certified": v1_74_summary.get("no_data_directory_writes") is True
        }
        res["input_guard_passed"] = all(res.values())
        return res

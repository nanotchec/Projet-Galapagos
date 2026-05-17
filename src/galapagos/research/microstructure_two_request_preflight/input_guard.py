from typing import Any, Dict

class InputGuard:
    def validate_v1_73_1_state(self, v1_73_1_summary: Dict[str, Any]) -> Dict[str, Any]:
        res = {
            "version_check_passed": v1_73_1_summary.get("version") == "V1.73.1",
            "approval_phrase_validated": v1_73_1_summary.get("approval_phrase_validated") is True,
            "human_approval_granted": v1_73_1_summary.get("human_approval_granted") is True,
            "v1_74_authorized": v1_73_1_summary.get("v1_74_two_request_preflight_authorized") is True,
            "max_request_count_is_2": v1_73_1_summary.get("max_request_count") == 2,
            "no_data_writes_mandate": v1_73_1_summary.get("v1_74_no_data_directory_writes") is True,
            "no_trading_mandate": v1_73_1_summary.get("v1_74_no_trading") is True
        }
        res["input_guard_passed"] = all(res.values())
        return res

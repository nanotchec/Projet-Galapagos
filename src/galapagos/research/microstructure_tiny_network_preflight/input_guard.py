from typing import Any, Dict

class InputGuard:
    def validate_approval(self, previous_summary: Dict[str, Any]) -> Dict[str, Any]:
        res = {
            "version_check_passed": previous_summary.get("version") == "V1.70.2",
            "human_approval_granted": previous_summary.get("human_approval_granted") is True,
            "approval_phrase_validated": previous_summary.get("approval_phrase_validated") is True,
            "v1_71_network_preflight_authorized": previous_summary.get("v1_71_network_preflight_authorized") is True,
            "max_request_count_limit": previous_summary.get("max_request_count", 0) == 1,
            "no_data_directory_writes_limit": previous_summary.get("no_data_directory_writes") is True,
            "no_real_trading_limit": previous_summary.get("no_real_trading") is True
        }
        res["input_guard_passed"] = all(res.values())
        return res

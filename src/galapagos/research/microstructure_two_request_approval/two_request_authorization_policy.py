from typing import Any, Dict

class TwoRequestAuthorizationPolicy:
    def get_policy(self, approved: bool) -> Dict[str, Any]:
        return {
            "v1_74_two_request_preflight_authorized": approved,
            "v1_74_must_remain_two_requests_max": True,
            "v1_74_reports_only": True,
            "v1_74_no_data_directory_writes": True,
            "v1_74_no_trading": True,
            "max_request_count": 2 if approved else 0,
            "max_records_preview": 20 if approved else 0
        }

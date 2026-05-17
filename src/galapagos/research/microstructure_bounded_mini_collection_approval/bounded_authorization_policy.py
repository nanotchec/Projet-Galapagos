from typing import Any, Dict

class BoundedAuthorizationPolicy:
    def __init__(self):
        self.max_request_count = 10
        self.max_records_preview_total = 100

    def get_policy(self) -> Dict[str, Any]:
        return {
            "v1_77_must_remain_bounded": True,
            "v1_77_max_request_count": self.max_request_count,
            "v1_77_max_records_preview_total": self.max_records_preview_total,
            "v1_77_reports_only": True,
            "v1_77_no_data_directory_writes": True,
            "v1_77_no_dataset_creation": True,
            "v1_77_no_trading": True
        }

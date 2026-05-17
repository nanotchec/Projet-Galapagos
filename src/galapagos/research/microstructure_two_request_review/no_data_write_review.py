from typing import Any, Dict

class NoDataWriteReview:
    def review_no_data_writes(self, v1_74_summary: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "no_data_directory_writes": v1_74_summary.get("no_data_directory_writes"),
            "dataset_created": v1_74_summary.get("dataset_created"),
            "new_data_files_created": v1_74_summary.get("new_data_files_created"),
            "no_data_write_review_passed": (
                v1_74_summary.get("no_data_directory_writes") is True and
                v1_74_summary.get("dataset_created") is False and
                v1_74_summary.get("new_data_files_created") is False
            )
        }

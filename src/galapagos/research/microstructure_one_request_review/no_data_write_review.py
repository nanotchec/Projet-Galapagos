from typing import Any, Dict

class NoDataWriteReview:
    def review_writes(self, v1_71_summary: Dict[str, Any]) -> Dict[str, Any]:
        res = {
            "previous_no_data_directory_writes": v1_71_summary.get("no_data_directory_writes") is True,
            "previous_dataset_created": v1_71_summary.get("dataset_created") is False,
            "previous_parquet_created": v1_71_summary.get("parquet_created") is False,
            "previous_csv_created": v1_71_summary.get("csv_created") is False,
            "previous_sqlite_created": v1_71_summary.get("sqlite_created") is False,
            "previous_jsonl_created": v1_71_summary.get("jsonl_created") is False,
            "previous_db_created": v1_71_summary.get("db_created") is False
        }
        res["no_data_write_review_passed"] = all(res.values())
        return res

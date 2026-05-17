from typing import Any, Dict

class ResponsePreviewReview:
    def review_preview(self, v1_74_summary: Dict[str, Any]) -> Dict[str, Any]:
        total_records = v1_74_summary.get("records_preview_count_total", 0)
        per_request_ok = v1_74_summary.get("records_preview_count_per_request_lte_10", False)
        
        return {
            "records_preview_count_total": total_records,
            "records_preview_count_total_lte_20": v1_74_summary.get("records_preview_count_total_lte_20"),
            "records_preview_count_per_request_lte_10": per_request_ok,
            "response_preview_review_passed": (
                total_records <= 20 and
                per_request_ok is True
            )
        }

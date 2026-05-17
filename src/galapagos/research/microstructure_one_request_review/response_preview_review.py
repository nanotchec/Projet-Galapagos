from typing import Any, Dict

class ResponsePreviewReview:
    def review_preview(self, v1_71_summary: Dict[str, Any]) -> Dict[str, Any]:
        count = v1_71_summary.get("records_preview_count", 0)
        res = {
            "previous_records_preview_count": count,
            "previous_records_preview_count_lte_10": count <= 10,
            "reports_only_output_check": v1_71_summary.get("reports_only_output") is True
        }
        res["response_preview_review_passed"] = all(res.values())
        return res

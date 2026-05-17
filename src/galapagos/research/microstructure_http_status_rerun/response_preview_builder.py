from typing import Any, Dict, List

class ResponsePreviewBuilder:
    def __init__(self, max_total_records: int = 100, max_per_request: int = 10):
        self.max_total_records = max_total_records
        self.max_per_request = max_per_request

    def build_preview(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        previews = []
        total_records = 0
        
        for r in responses:
            if not r.get("success_flag") or not r.get("content"):
                continue
                
            data = r["content"]
            if not isinstance(data, list):
                continue
                
            count = len(data)
            preview_count = min(count, self.max_per_request)
            
            # Don't exceed global limit
            if total_records + preview_count > self.max_total_records:
                preview_count = self.max_total_records - total_records
                
            if preview_count <= 0:
                break
                
            previews.append({
                "request_index": r["request_index"],
                "record_count": preview_count,
                "data_preview": data[:preview_count],
                "status_code": r["status_code"]
            })
            total_records += preview_count
            
        return {
            "records_preview_count_total": total_records,
            "max_records_preview_total": self.max_total_records,
            "previews": previews,
            "records_preview_count_total_lte_100": total_records <= 100
        }

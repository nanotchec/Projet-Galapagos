from typing import Any, Dict, List

class ResponsePreviewBuilder:
    def __init__(self, max_total_records: int = 100, max_per_request: int = 10):
        self.max_total_records = max_total_records
        self.max_per_request = max_per_request
        self.total_records_count = 0

    def build_preview(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        previews = []
        for i, res in enumerate(responses):
            if not res.get("success") or "json_body" not in res:
                continue
                
            body = res["json_body"]
            if not isinstance(body, list):
                continue
                
            # Limit records per request
            subset = body[:self.max_per_request]
            
            # Global limit
            remaining = self.max_total_records - self.total_records_count
            if remaining <= 0:
                break
                
            subset = subset[:remaining]
            self.total_records_count += len(subset)
            
            previews.append({
                "request_index": i,
                "record_count": len(subset),
                "data_preview": subset
            })
            
        return {
            "records_preview_count_total": self.total_records_count,
            "max_records_preview_total": self.max_total_records,
            "previews": previews,
            "records_preview_count_total_lte_100": self.total_records_count <= 100
        }

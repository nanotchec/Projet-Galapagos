from typing import Any, Dict, List

class ResponsePreviewBuilder:
    def build_preview(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        previews = []
        total_records = 0
        status_codes = []
        total_bytes = 0

        for idx, resp in enumerate(responses):
            if resp["success"]:
                data = resp["data"]
                status_codes.append(resp["status_code"])
                total_bytes += resp["size_bytes"]
                
                preview_data = data[:10]
                total_records += len(preview_data)
                
                previews.append({
                    "request_index": idx,
                    "record_count": len(preview_data),
                    "preview": preview_data,
                    "fields_preview": ["open_time", "open", "high", "low", "close", "volume"] # Binance OHLCV
                })
            else:
                status_codes.append(resp["status_code"])

        return {
            "response_received": len(responses) > 0,
            "response_status_codes": status_codes,
            "response_size_bytes_total": total_bytes,
            "records_preview_count_total": total_records,
            "records_preview_count_total_lte_20": total_records <= 20,
            "records_preview_count_per_request_lte_10": all(p["record_count"] <= 10 for p in previews),
            "previews": previews
        }

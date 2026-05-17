from typing import Any, Dict, List

class ResponsePreviewBuilder:
    def build_preview(self, client_res: Dict[str, Any], max_records: int = 10) -> Dict[str, Any]:
        raw = client_res.get("raw_response")
        if not raw or not isinstance(raw, list):
            return {
                "records_preview_count": 0,
                "preview_data": [],
                "fields_found": []
            }

        preview_data = raw[:max_records]
        
        # Binance klines format: [ [open_time, open, high, low, close, vol, close_time, ...], ... ]
        # We'll just take a few fields if possible or the whole small records
        return {
            "records_preview_count": len(preview_data),
            "preview_data": preview_data,
            "fields_summary": "Binance Klines (OHLCV)",
            "records_preview_count_lte_10": len(preview_data) <= 10
        }
